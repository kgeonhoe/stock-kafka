"""
한국투자증권 API 대량 데이터 조회 클라이언트
python-kis 라이브러리의 배치 처리 방식을 참고하여 구현
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from decimal import Decimal
import aiohttp
from dataclasses import dataclass

from ..kis_api_client import KISAPIClient
from ..cache_manager import CacheManager

logger = logging.getLogger(__name__)

@dataclass
class ChartData:
    """차트 데이터 구조"""
    symbol: str
    date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    market: str = "NASDAQ"

class BulkDataClient:
    """대량 데이터 조회를 위한 클라이언트"""
    
    def __init__(self, kis_client: KISAPIClient, cache_manager: CacheManager):
        self.kis_client = kis_client
        self.cache_manager = cache_manager
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting 설정 (python-kis 방식 적용)
        self.max_requests_per_second = 15
        self.request_interval = 1.0 / self.max_requests_per_second
        self.last_request_time = 0.0
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def _smart_rate_limit(self):
        """스마트 레이트 리미팅 (python-kis RateLimiter 방식)"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            wait_time = self.request_interval - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.3f} seconds")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    async def get_daily_chart_bulk(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date,
        market: str = "NASDAQ"
    ) -> List[ChartData]:
        """
        기간별 일봉 차트 데이터 대량 조회
        python-kis의 daily_chart 로직을 참고하여 구현
        """
        logger.info(f"Fetching daily chart for {symbol} from {start_date} to {end_date}")
        
        all_chart_data = []
        current_date = end_date  # 최신 날짜부터 역순으로 조회
        
        # 캐시 확인
        cache_key = f"daily_chart:{symbol}:{start_date}:{end_date}"
        cached_data = await self.cache_manager.get_stock_data(cache_key)
        if cached_data:
            logger.info(f"Found cached daily chart data for {symbol}")
            return self._parse_cached_chart_data(cached_data)
        
        while current_date >= start_date:
            await self._smart_rate_limit()
            
            try:
                # 일봉 조회 API 호출 (KIS 해외주식 기간별시세 API 사용)
                chart_data = await self._fetch_daily_chart_page(
                    symbol, current_date, market
                )
                
                if not chart_data:
                    logger.warning(f"No chart data received for {symbol} on {current_date}")
                    break
                
                # 데이터 필터링 (start_date 이후만)
                filtered_data = [
                    data for data in chart_data 
                    if data.date >= start_date
                ]
                
                all_chart_data.extend(filtered_data)
                
                # 가장 오래된 데이터의 날짜 확인
                if chart_data:
                    oldest_date = min(data.date for data in chart_data)
                    if oldest_date <= start_date:
                        break
                    current_date = oldest_date - timedelta(days=1)
                else:
                    break
                    
                logger.debug(f"Fetched {len(chart_data)} records for {symbol}, continuing from {current_date}")
                
            except Exception as e:
                logger.error(f"Error fetching chart data for {symbol}: {e}")
                # 에러 발생 시 기존 데이터라도 반환
                break
        
        # 날짜순으로 정렬
        all_chart_data.sort(key=lambda x: x.date)
        
        # 캐시 저장 (1시간 유지)
        if all_chart_data:
            await self.cache_manager.set_stock_data(
                cache_key, 
                self._serialize_chart_data(all_chart_data),
                expire_seconds=3600
            )
        
        logger.info(f"Successfully fetched {len(all_chart_data)} daily chart records for {symbol}")
        return all_chart_data
    
    async def _fetch_daily_chart_page(
        self, 
        symbol: str, 
        end_date: date, 
        market: str
    ) -> List[ChartData]:
        """단일 페이지 일봉 데이터 조회"""
        
        # KIS API 파라미터 준비
        params = {
            "AUTH": "",
            "EXCD": "NAS" if market == "NASDAQ" else "NYS",  # 거래소 코드
            "SYMB": symbol,
            "GUBN": "0",  # 일봉(0), 주봉(1), 월봉(2)
            "BYMD": end_date.strftime("%Y%m%d"),  # 조회 기준일
            "MODP": "0"   # 수정주가 미적용
        }
        
        try:
            # KIS API 호출
            response = await self.kis_client._make_request(
                "GET",
                "/uapi/overseas-price/v1/quotations/dailyprice",
                params=params,
                tr_id="HHDFS76240000"
            )
            
            if response and response.get("rt_cd") == "0":
                output2 = response.get("output2", [])
                return self._parse_daily_chart_response(output2, symbol, market)
            else:
                logger.warning(f"API returned error for {symbol}: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Error in daily chart API call for {symbol}: {e}")
            return []
    
    def _parse_daily_chart_response(
        self, 
        output2: List[Dict], 
        symbol: str, 
        market: str
    ) -> List[ChartData]:
        """일봉 API 응답 데이터 파싱"""
        chart_data = []
        
        for item in output2:
            try:
                chart_data.append(ChartData(
                    symbol=symbol,
                    date=datetime.strptime(item.get("xymd", ""), "%Y%m%d").date(),
                    open_price=Decimal(item.get("open", "0")),
                    high_price=Decimal(item.get("high", "0")),
                    low_price=Decimal(item.get("low", "0")),
                    close_price=Decimal(item.get("clos", "0")),
                    volume=int(item.get("tvol", "0")),
                    market=market
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing chart data item: {item}, error: {e}")
                continue
        
        return chart_data
    
    async def fetch_multiple_symbols_bulk(
        self, 
        symbols: List[str], 
        start_date: date, 
        end_date: date,
        market: str = "NASDAQ",
        concurrent_limit: int = 3
    ) -> Dict[str, List[ChartData]]:
        """
        여러 종목의 일봉 데이터를 동시에 조회
        동시 요청 수를 제한하여 API 부하 관리
        """
        logger.info(f"Fetching bulk data for {len(symbols)} symbols")
        
        semaphore = asyncio.Semaphore(concurrent_limit)
        results = {}
        
        async def fetch_symbol(symbol: str):
            async with semaphore:
                try:
                    data = await self.get_daily_chart_bulk(symbol, start_date, end_date, market)
                    return symbol, data
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {e}")
                    return symbol, []
        
        # 모든 종목 동시 처리
        tasks = [fetch_symbol(symbol) for symbol in symbols]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_tasks:
            if isinstance(result, tuple):
                symbol, data = result
                results[symbol] = data
            else:
                logger.error(f"Task failed with exception: {result}")
        
        successful_symbols = [s for s, data in results.items() if data]
        logger.info(f"Successfully fetched data for {len(successful_symbols)}/{len(symbols)} symbols")
        
        return results
    
    def _serialize_chart_data(self, chart_data: List[ChartData]) -> List[Dict]:
        """차트 데이터를 캐시용 딕셔너리로 직렬화"""
        return [
            {
                "symbol": data.symbol,
                "date": data.date.isoformat(),
                "open_price": str(data.open_price),
                "high_price": str(data.high_price),
                "low_price": str(data.low_price),
                "close_price": str(data.close_price),
                "volume": data.volume,
                "market": data.market
            }
            for data in chart_data
        ]
    
    async def run_realtime_monitoring_batch(self):
        """실시간 모니터링 배치 (현재가 기반)"""
        logger.info("Starting realtime monitoring batch...")
        
        try:
            # 주요 종목들만 실시간 모니터링
            priority_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            
            for symbol in priority_symbols:
                try:
                    await self._process_realtime_symbol(symbol)
                    # 실시간 처리는 빠른 간격
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error processing realtime {symbol}: {e}")
                    continue
            
            logger.info("Realtime monitoring batch completed successfully")
            
        except Exception as e:
            logger.error(f"Realtime monitoring batch failed: {e}")
            raise
    
    async def _process_realtime_symbol(self, symbol: str):
        """실시간 단일 종목 처리 (기존 batch_runner 로직 참고)"""
        try:
            # 현재가 정보 조회 (KIS API)
            params = {
                "AUTH": "",
                "EXCD": "NAS",
                "SYMB": symbol,
            }
            
            response = await self.kis_client._make_request(
                "GET",
                "/uapi/overseas-price/v1/quotations/price",
                params=params,
                tr_id="HHDFS00000300"
            )
            
            if response and response.get("rt_cd") == "0":
                output = response.get("output", {})
                
                # 간단한 신호 체크 (RSI 기반)
                current_price = float(output.get("last", "0"))
                
                # 캐시에서 과거 데이터 조회
                cache_key = f"realtime_history:{symbol}"
                cached_prices = await self.cache_manager.get_stock_data(cache_key) or []
                
                # 간단한 RSI 계산
                if len(cached_prices) >= 14:
                    prices = [float(p) for p in cached_prices[-14:]] + [current_price]
                    rsi = self._calculate_simple_rsi(prices)
                    
                    # 신호 탐지
                    signal = "HOLD"
                    if rsi < 30:
                        signal = "BUY"
                    elif rsi > 70:
                        signal = "SELL"
                    
                    if signal != "HOLD":
                        logger.info(f"🚨 {symbol}: {signal} signal (RSI: {rsi:.1f}, Price: ${current_price})")
                        
                        # 캐시에만 저장 (DB 부하 방지)
                        alert_key = f"realtime_alert:{symbol}"
                        await self.cache_manager.set_stock_data(
                            alert_key, 
                            {"signal": signal, "price": current_price, "rsi": rsi},
                            expire_seconds=300  # 5분
                        )
                
                # 가격 히스토리 업데이트 (최근 20개만 유지)
                cached_prices.append(current_price)
                if len(cached_prices) > 20:
                    cached_prices = cached_prices[-20:]
                
                await self.cache_manager.set_stock_data(
                    cache_key, cached_prices, expire_seconds=3600
                )
                
                logger.debug(f"Realtime update {symbol}: ${current_price}")
            else:
                logger.warning(f"No realtime data received for {symbol}")
                
        except Exception as e:
            logger.error(f"Error processing realtime {symbol}: {e}")
            raise
    
    def _calculate_simple_rsi(self, prices: List[float], period: int = 14) -> float:
        """간단한 RSI 계산"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    # ...existing code...
