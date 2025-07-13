"""
Korean Investment Securities API Client
"""
import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import hmac
import base64
from dataclasses import dataclass
from enum import Enum

from config.kis_config import KISConfig
from logger_config import logger
import redis
import os

class MarketType(Enum):
    NASDAQ = "NAS"
    NYSE = "NYS"
    AMEX = "AMS"

@dataclass
class StockQuote:
    symbol: str
    price: float
    volume: int
    high: float
    low: float
    open: float
    close: float
    change_percent: float
    market: str
    timestamp: datetime

class KISAPIClient:
    def __init__(self):
        self.config = KISConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token = ""  # 빈 값으로 시작, 자동 발급
        
        # Redis 연결 시도
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 연결 테스트
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Continuing without cache.")
            self.redis_client = None
        
        # Rate limiting
        self.rate_limits = {
            'per_second': 20,
            'per_minute': 1000,
            'per_hour': 10000
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def initialize(self):
        """Initialize HTTP session and authenticate"""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Stock-Kafka-Pipeline/1.0'
                }
            )
            
        # Validate credentials
        if not self.config.validate_credentials():
            raise ValueError("KIS API credentials are not properly configured. Please check your .env file.")
            
        # Get initial access token
        await self._get_new_access_token()
        logger.info("KIS API client initialized successfully")
        
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def _refresh_token_if_needed(self):
        """Refresh access token if needed"""
        try:
            if not self.redis_client:
                # Redis 없이 토큰 새로 발급
                await self._get_new_access_token()
                return
                
            # Check if token is cached and still valid
            cached_token = self.redis_client.get("kis_access_token")
            token_expiry = self.redis_client.get("kis_token_expiry")
            
            if cached_token and token_expiry:
                expiry_time = datetime.fromisoformat(token_expiry)
                if datetime.now() < expiry_time - timedelta(minutes=10):  # 10분 여유
                    self.access_token = cached_token
                    return
                    
            # Refresh token
            await self._get_new_access_token()
            
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise
            
    async def _get_new_access_token(self, retry_count: int = 0, max_retries: int = 2):
        """Get new access token from KIS API with auto-retry"""
        url = f"{self.config.BASE_URL}/oauth2/tokenP"
        
        payload = {
            'grant_type': 'client_credentials',
            'appkey': self.config.APP_KEY,
            'appsecret': self.config.APP_SECRET
        }
        
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        try:
            if retry_count == 0:
                logger.info("🔑 Requesting new access token...")
            else:
                logger.info(f"🔄 Retrying token request... ({retry_count + 1}/{max_retries + 1})")
                
            async with self.session.post(url, json=payload, headers=headers) as response:
                response_text = await response.text()
                logger.debug(f"Token response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    if 'access_token' in data:
                        self.access_token = data['access_token']
                        expires_in = data.get('expires_in', 3600)  # Default 1 hour
                        
                        # Cache token
                        if self.redis_client:
                            try:
                                expiry_time = datetime.now() + timedelta(seconds=expires_in)
                                self.redis_client.setex("kis_access_token", expires_in, self.access_token)
                                self.redis_client.setex("kis_token_expiry", expires_in, expiry_time.isoformat())
                            except Exception as redis_error:
                                logger.warning(f"Redis cache failed: {redis_error}")
                        
                        logger.info("✅ Access token obtained successfully")
                        return
                    else:
                        logger.error(f"No access_token in response: {data}")
                        raise Exception("No access_token in response")
                else:
                    # 토큰 발급 제한 체크
                    if "1분당 1회" in response_text or "EGW00133" in response_text:
                        if retry_count < max_retries:
                            wait_time = 65  # 65초 대기
                            logger.warning(f"⏰ 토큰 발급 제한 - {wait_time}초 후 재시도... ({retry_count + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            return await self._get_new_access_token(retry_count + 1, max_retries)
                        else:
                            logger.error("❌ 토큰 발급 최대 재시도 횟수 초과")
                            raise Exception("Token generation rate limit exceeded. Maximum retries reached.")
                    else:
                        logger.error(f"Failed to get access token: {response.status} - {response_text}")
                        raise Exception(f"Failed to get access token: {response.status} - {response_text}")
                    
        except Exception as e:
            if "rate limit" in str(e) and retry_count < max_retries:
                # 재시도 가능한 경우
                return await self._get_new_access_token(retry_count + 1, max_retries)
            else:
                logger.error(f"Error getting new access token: {e}")
                raise
            raise
            
    async def _check_rate_limit(self, endpoint: str) -> bool:
        """Check if API rate limit allows the request"""
        current_time = int(time.time())
        
        # 더 엄격한 초당 제한 (15회로 감소)
        second_key = f"rate_limit:second:{current_time}"
        second_count = self.redis_client.incr(second_key)
        self.redis_client.expire(second_key, 1)
        
        if second_count > 15:  # 20 -> 15로 감소
            logger.warning("Per-second rate limit exceeded")
            await asyncio.sleep(1)  # 1초 대기
            return False
            
        # Check per-minute limit
        minute_key = f"rate_limit:minute:{current_time // 60}"
        minute_count = self.redis_client.incr(minute_key)
        self.redis_client.expire(minute_key, 60)
        
        if minute_count > self.rate_limits['per_minute']:
            logger.warning("Per-minute rate limit exceeded")
            return False
            
        # 요청 간 최소 대기 시간 추가 (100ms)
        await asyncio.sleep(0.1)
        
        return True
        
    async def _make_request(self, endpoint: str, tr_id: str, params: Dict = None, retry_count: int = 0) -> Dict:
        """Make authenticated API request with enhanced error handling"""
        if not await self._check_rate_limit(endpoint):
            raise Exception("Rate limit exceeded")
            
        await self._refresh_token_if_needed()
        
        url = self.config.get_endpoint_url(endpoint)
        headers = {
            'Content-Type': 'application/json',
            'authorization': f'Bearer {self.access_token}',
            'appkey': self.config.APP_KEY,
            'appsecret': self.config.APP_SECRET,
            'tr_id': tr_id,
        }
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    return await response.json()
                    
                elif response.status == 401:
                    # Token expired, refresh and retry once
                    if retry_count == 0:
                        logger.warning("Token expired, refreshing...")
                        await self._get_new_access_token()
                        return await self._make_request(endpoint, tr_id, params, retry_count + 1)
                    else:
                        raise Exception("Authentication failed after token refresh")
                        
                elif response.status == 500:
                    # 초당 거래건수 초과 처리
                    if "초당 거래건수" in response_text:
                        if retry_count < 2:
                            wait_time = (retry_count + 1) * 2  # 2초, 4초 점진적 대기
                            logger.warning(f"⏰ 초당 거래건수 초과 - {wait_time}초 후 재시도...")
                            await asyncio.sleep(wait_time)
                            return await self._make_request(endpoint, tr_id, params, retry_count + 1)
                        else:
                            raise Exception("초당 거래건수 초과 - 최대 재시도 횟수 도달")
                    else:
                        raise Exception(f"Server error: {response.status} - {response_text}")
                        
                else:
                    error_text = response_text
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            raise
            
    async def get_nasdaq_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get current quote for NASDAQ symbol"""
        cache_key = f"quote:{symbol}"
        
        # Check cache first
        cached_quote = self.redis_client.get(cache_key)
        if cached_quote:
            try:
                data = json.loads(cached_quote)
                return StockQuote(**data)
            except:
                pass  # Cache miss or invalid data
                
        try:
            params = {
                'SYMB': symbol,
                'EXCD': 'NAS'
            }
            
            response = await self._make_request('nasdaq_price', 'HHDFS00000300', params)
            
            if response and 'output' in response:
                data = response['output']
                
                quote = StockQuote(
                    symbol=symbol,
                    price=float(data.get('last', 0)),
                    volume=int(data.get('tvol', 0)),
                    high=float(data.get('high', 0)),
                    low=float(data.get('low', 0)),
                    open=float(data.get('open', 0)),
                    close=float(data.get('base', 0)),
                    change_percent=float(data.get('rate', 0)),
                    market='NASDAQ',
                    timestamp=datetime.now()
                )
                
                # Cache for 5 seconds
                self.redis_client.setex(cache_key, 5, json.dumps(quote.__dict__, default=str))
                
                return quote
                
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None
            
    async def get_nasdaq_daily_data(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get daily historical data for NASDAQ symbol"""
        cache_key = f"daily:{symbol}:{days}"
        
        # Check cache first (cache for 1 hour)
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            try:
                return json.loads(cached_data)
            except:
                pass
                
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            params = {
                'SYMB': symbol,
                'EXCD': 'NAS',
                'GUBN': '0',  # Daily
                'BYMD': end_date,
                'MODP': '1'
            }
            
            response = await self._make_request('nasdaq_daily', 'HHDFS76240000', params)
            
            if response and 'output2' in response:
                daily_data = []
                for item in response['output2']:
                    daily_data.append({
                        'symbol': symbol,
                        'date': item.get('xymd', ''),
                        'open': float(item.get('open', 0)),
                        'high': float(item.get('high', 0)),
                        'low': float(item.get('low', 0)),
                        'close': float(item.get('clos', 0)),
                        'volume': int(item.get('tvol', 0)),
                        'change_percent': float(item.get('rate', 0))
                    })
                
                # Cache for 1 hour
                self.redis_client.setex(cache_key, 3600, json.dumps(daily_data))
                
                return daily_data
                
        except Exception as e:
            logger.error(f"Failed to get daily data for {symbol}: {e}")
            return []
            
    async def search_nasdaq_symbols(self, query: str) -> List[Dict]:
        """Search for NASDAQ symbols"""
        try:
            params = {
                'PRDT_TYPE_CD': '512',  # US stocks
                'PDNO': query,
                'PRDT_NAME': query
            }
            
            response = await self._make_request('nasdaq_search', 'CTPF1604R', params)
            
            if response and 'output' in response:
                symbols = []
                for item in response['output']:
                    symbols.append({
                        'symbol': item.get('pdno', ''),
                        'name': item.get('prdt_name', ''),
                        'market': item.get('excd_name', ''),
                        'currency': item.get('tr_crcy_cd', 'USD')
                    })
                return symbols
                
        except Exception as e:
            logger.error(f"Failed to search symbols for {query}: {e}")
            return []
            
    async def get_multiple_quotes(self, symbols: List[str]) -> List[StockQuote]:
        """Get quotes for multiple symbols with proper rate limiting"""
        quotes = []
        
        logger.info(f"📊 Getting quotes for {len(symbols)} symbols with rate limiting...")
        
        for i, symbol in enumerate(symbols):
            try:
                # 각 요청 사이에 0.5초 대기
                if i > 0:
                    await asyncio.sleep(0.5)
                    
                quote = await self.get_nasdaq_quote(symbol)
                if quote:
                    quotes.append(quote)
                    logger.info(f"✅ {symbol}: ${quote.price:.2f}")
                else:
                    logger.warning(f"⚠️ {symbol}: 데이터 없음")
                    
            except Exception as e:
                logger.error(f"❌ {symbol} 조회 실패: {e}")
                continue
                
        return quotes
        
    async def get_account_balance(self) -> Dict:
        """Get account balance (for future portfolio management)"""
        # Placeholder for account balance API
        # This would require different endpoint and authentication
        return {
            'cash': 0.0,
            'total_value': 0.0,
            'positions': []
        }
        
    def get_trading_session(self) -> str:
        """Get current trading session"""
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        if '04:00' <= current_time < '09:30':
            return 'pre_market'
        elif '09:30' <= current_time < '16:00':
            return 'regular'
        elif '16:00' <= current_time < '20:00':
            return 'after_hours'
        else:
            return 'closed'
            
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        session = self.get_trading_session()
        return session in ['pre_market', 'regular', 'after_hours']

# Global API client instance
api_client = KISAPIClient()
