"""
Batch Processor for Daily Stock Data Collection and Analysis
"""
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.logger_config import logger
from src.kis_api_client import KISAPIClient
from src.database import DuckDBManager
from src.technical_analysis import TechnicalAnalyzer
from src.cache_manager import CacheManager
from config.kis_config import KISConfig

class BatchProcessor:
    def __init__(self):
        self.db_manager = DuckDBManager()
        self.cache_manager = CacheManager()
        self.config = KISConfig()
        self.running = False
        
        # 실시간 모니터링 우선 종목 (응답성 최적화)
        self.base_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
            'META', 'NVDA', 'NFLX', 'ADBE', 'CRM',
            'INTC', 'AMD', 'QCOM', 'AVGO', 'TXN',
            'COST', 'SBUX', 'PYPL', 'ZOOM', 'UBER'
        ]
        
        # 실시간 처리 최적화 설정
        self.is_realtime_mode = True
        self.quick_scan_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']  # 빠른 스캔용
        
    async def start(self):
        """배치 프로세서 시작"""
        logger.info("📅 Starting Batch Processor...")
        self.running = True
        
        # 초기 실행
        await self.run_daily_batch()
        
        # 일일 스케줄링 (실제 운영 시에는 cron job이나 스케줄러 사용)
        while self.running:
            await asyncio.sleep(3600)  # 1시간마다 확인
            
            # 매일 오전 8시에 실행 (시장 개장 전)
            now = datetime.now()
            if now.hour == 8 and now.minute == 0:
                await self.run_daily_batch()
    
    async def stop(self):
        """배치 프로세서 중지"""
        logger.info("🛑 Stopping Batch Processor...")
        self.running = False
    
    async def run_daily_batch(self):
        """일일 배치 처리 실행"""
        logger.info("🚀 Running daily batch processing...")
        
        try:
            # 1. 기본 종목 데이터 수집
            logger.info("📊 Step 1: Collecting stock data...")
            stock_data = await self.collect_stock_data(self.base_symbols)
            
            # 2. 기술적 지표 계산
            logger.info("📈 Step 2: Calculating technical indicators...")
            analyzed_stocks = await self.analyze_stocks(stock_data)
            
            # 3. 관심종목 선별
            logger.info("🎯 Step 3: Selecting watchlist...")
            watchlist = await self.select_watchlist(analyzed_stocks)
            
            # 4. 데이터베이스 저장
            logger.info("💾 Step 4: Saving to database...")
            await self.save_to_database(analyzed_stocks, watchlist)
            
            # 5. 캐시 업데이트
            logger.info("🔄 Step 5: Updating cache...")
            await self.update_cache(watchlist)
            
            logger.info("✅ Daily batch processing completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Daily batch processing failed: {e}")
    
    async def collect_stock_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """주식 데이터 수집"""
        logger.info(f"📈 Collecting data for {len(symbols)} symbols...")
        
        stock_data = {}
        
        async with KISAPIClient() as client:
            for i, symbol in enumerate(symbols):
                try:
                    # Rate limiting을 위한 대기
                    if i > 0:
                        await asyncio.sleep(1)  # 1초 대기
                    
                    logger.info(f"📊 Processing {symbol} ({i+1}/{len(symbols)})")
                    
                    # 현재가 정보
                    current_quote = await client.get_nasdaq_quote(symbol)
                    if not current_quote:
                        logger.warning(f"⚠️ No current data for {symbol}")
                        continue
                    
                    # 60일 일일 데이터 (기술적 분석용)
                    daily_data = await client.get_nasdaq_daily_data(symbol, 60)
                    if not daily_data or len(daily_data) < 30:
                        logger.warning(f"⚠️ Insufficient historical data for {symbol}")
                        continue
                    
                    stock_data[symbol] = {
                        'current_quote': current_quote,
                        'daily_data': daily_data,
                        'collected_at': datetime.now()
                    }
                    
                    logger.info(f"✅ {symbol}: Current ${current_quote.price:.2f}, {len(daily_data)} days history")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to collect data for {symbol}: {e}")
                    continue
        
        logger.info(f"📈 Collected data for {len(stock_data)} symbols")
        return stock_data
    
    async def analyze_stocks(self, stock_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """주식 데이터 기술적 분석"""
        logger.info(f"🧮 Analyzing {len(stock_data)} stocks...")
        
        analyzed_stocks = {}
        
        for symbol, data in stock_data.items():
            try:
                # DataFrame 생성
                df = pd.DataFrame(data['daily_data'])
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                df = df.sort_values('date')
                
                # 기술적 지표 계산
                indicators = TechnicalAnalyzer.calculate_all_indicators(df)
                
                # 신호 탐지
                current_price = data['current_quote'].price
                signals = TechnicalAnalyzer.detect_signals(indicators, current_price)
                
                # 거래량 분석
                volume_analysis = self.analyze_volume(df, data['current_quote'].volume)
                
                analyzed_stocks[symbol] = {
                    'current_quote': data['current_quote'],
                    'indicators': indicators,
                    'signals': signals,
                    'volume_analysis': volume_analysis,
                    'daily_data': data['daily_data'],
                    'analyzed_at': datetime.now()
                }
                
                logger.info(f"✅ {symbol}: {signals['signal_strength']} (Score: {signals['total_score']})")
                
            except Exception as e:
                logger.error(f"❌ Failed to analyze {symbol}: {e}")
                continue
        
        logger.info(f"🧮 Analyzed {len(analyzed_stocks)} stocks")
        return analyzed_stocks
    
    def analyze_volume(self, df: pd.DataFrame, current_volume: int) -> Dict[str, Any]:
        """거래량 분석"""
        if len(df) < 20:
            return {'avg_volume_20d': 0, 'volume_ratio': 1.0, 'volume_trend': 'NORMAL'}
        
        # 최근 20일 평균 거래량
        avg_volume_20d = df['volume'].tail(20).mean()
        
        # 현재 거래량 비율
        volume_ratio = current_volume / avg_volume_20d if avg_volume_20d > 0 else 1.0
        
        # 거래량 트렌드 판단
        if volume_ratio >= 2.0:
            volume_trend = 'SURGE'  # 급증
        elif volume_ratio >= 1.5:
            volume_trend = 'HIGH'   # 높음
        elif volume_ratio <= 0.5:
            volume_trend = 'LOW'    # 낮음
        else:
            volume_trend = 'NORMAL' # 보통
        
        return {
            'avg_volume_20d': int(avg_volume_20d),
            'volume_ratio': round(volume_ratio, 2),
            'volume_trend': volume_trend
        }
    
    async def select_watchlist(self, analyzed_stocks: Dict[str, Dict]) -> Dict[str, List[str]]:
        """관심종목 선별"""
        logger.info("🎯 Selecting watchlist by tiers...")
        
        # 종목별 점수 계산
        scored_stocks = []
        
        for symbol, data in analyzed_stocks.items():
            signals = data['signals']
            volume_analysis = data['volume_analysis']
            indicators = data['indicators']
            
            # 기본 신호 점수
            base_score = signals['total_score']
            
            # 거래량 보너스
            volume_bonus = 0
            if volume_analysis['volume_trend'] == 'SURGE':
                volume_bonus = 3
            elif volume_analysis['volume_trend'] == 'HIGH':
                volume_bonus = 2
            elif volume_analysis['volume_trend'] == 'LOW':
                volume_bonus = -1
            
            # RSI 보너스 (과매도 구간 선호)
            rsi_bonus = 0
            if indicators.rsi_14 < 30:
                rsi_bonus = 2
            elif indicators.rsi_14 < 50:
                rsi_bonus = 1
            
            # 변동성 보너스 (볼린저 밴드 폭)
            volatility_bonus = 0
            if indicators.bb_width > 10:  # 높은 변동성
                volatility_bonus = 1
            
            total_score = base_score + volume_bonus + rsi_bonus + volatility_bonus
            
            scored_stocks.append({
                'symbol': symbol,
                'score': total_score,
                'signal_strength': signals['signal_strength'],
                'volume_trend': volume_analysis['volume_trend'],
                'rsi': indicators.rsi_14
            })
        
        # 점수 순으로 정렬
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        # 티어별 분류
        watchlist = {
            'tier1': [],  # 고우선순위 (상위 15개)
            'tier2': [],  # 중간우선순위 (상위 16-30개)  
            'tier3': []   # 저우선순위 (상위 31-50개)
        }
        
        # Tier 1: 상위 15개 (강한 매수 신호)
        tier1_candidates = [s for s in scored_stocks if s['score'] >= 3][:15]
        watchlist['tier1'] = [s['symbol'] for s in tier1_candidates]
        
        # Tier 2: 중간 15개
        tier2_candidates = [s for s in scored_stocks if s['score'] >= 0 and s['symbol'] not in watchlist['tier1']][:15]
        watchlist['tier2'] = [s['symbol'] for s in tier2_candidates]
        
        # Tier 3: 나머지 20개
        tier3_candidates = [s for s in scored_stocks if s['symbol'] not in watchlist['tier1'] and s['symbol'] not in watchlist['tier2']][:20]
        watchlist['tier3'] = [s['symbol'] for s in tier3_candidates]
        
        logger.info(f"🎯 Watchlist created:")
        logger.info(f"   - Tier 1 (High): {len(watchlist['tier1'])} symbols")
        logger.info(f"   - Tier 2 (Medium): {len(watchlist['tier2'])} symbols")
        logger.info(f"   - Tier 3 (Low): {len(watchlist['tier3'])} symbols")
        
        # 상위 5개 종목 로깅
        for i, stock in enumerate(scored_stocks[:5]):
            logger.info(f"   {i+1}. {stock['symbol']}: {stock['signal_strength']} (Score: {stock['score']})")
        
        return watchlist
    
    async def save_to_database(self, analyzed_stocks: Dict[str, Dict], watchlist: Dict[str, List[str]]):
        """분석 결과를 데이터베이스에 저장"""
        logger.info("💾 Saving analysis results to database...")
        
        try:
            # 일일 요약 데이터 준비
            daily_summaries = []
            trading_signals = []
            
            current_date = datetime.now().date()
            
            for symbol, data in analyzed_stocks.items():
                indicators = data['indicators']
                signals = data['signals']
                current_quote = data['current_quote']
                volume_analysis = data['volume_analysis']
                
                # 일일 요약 데이터
                daily_summary = {
                    'date': current_date,
                    'symbol': symbol,
                    'open': current_quote.open,
                    'high': current_quote.high,
                    'low': current_quote.low,
                    'close': current_quote.price,
                    'volume': current_quote.volume,
                    'change_percent': current_quote.change_percent,
                    'volatility': indicators.bb_width,
                    'avg_volume_20d': volume_analysis['avg_volume_20d'],
                    'rsi_14': indicators.rsi_14,
                    'macd': indicators.macd,
                    'macd_signal': indicators.macd_signal,
                    'bollinger_upper': indicators.bb_upper,
                    'bollinger_lower': indicators.bb_lower
                }
                daily_summaries.append(daily_summary)
                
                # 거래 신호 데이터 (강한 신호만)
                if signals['signal_strength'] in ['STRONG_BUY', 'BUY', 'STRONG_SELL', 'SELL']:
                    trading_signal = {
                        'timestamp': datetime.now(),
                        'symbol': symbol,
                        'signal_type': signals['signal_strength'],
                        'signal_strength': abs(signals['total_score']) / 10.0,  # 0-1 정규화
                        'price': current_quote.price,
                        'volume': current_quote.volume,
                        'indicators': json.dumps({
                            'rsi_14': indicators.rsi_14,
                            'macd': indicators.macd,
                            'bb_position': 'lower' if current_quote.price < indicators.bb_lower else 'upper' if current_quote.price > indicators.bb_upper else 'middle',
                            'volume_trend': volume_analysis['volume_trend']
                        }),
                        'tier': 'tier1' if symbol in watchlist['tier1'] else 'tier2' if symbol in watchlist['tier2'] else 'tier3'
                    }
                    trading_signals.append(trading_signal)
            
            # 데이터베이스에 저장
            if daily_summaries:
                self.db_manager.insert_daily_summary(daily_summaries)
                logger.info(f"💾 Saved {len(daily_summaries)} daily summaries")
            
            if trading_signals:
                for signal in trading_signals:
                    self.db_manager.insert_trading_signal(signal)
                logger.info(f"💾 Saved {len(trading_signals)} trading signals")
            
            # 관심종목 업데이트
            for tier, symbols in watchlist.items():
                if symbols:
                    scores = [analyzed_stocks[symbol]['signals']['total_score'] for symbol in symbols]
                    self.db_manager.update_watchlist(symbols, tier, scores)
            
            logger.info("✅ Database save completed")
            
        except Exception as e:
            logger.error(f"❌ Failed to save to database: {e}")
            raise
    
    async def update_cache(self, watchlist: Dict[str, List[str]]):
        """캐시 업데이트"""
        logger.info("🔄 Updating cache...")
        
        try:
            # 관심종목 캐시 업데이트
            for tier, symbols in watchlist.items():
                self.cache_manager.cache_watchlist(tier, symbols, ttl=86400)  # 24시간
            
            # 배치 실행 시간 캐시
            self.cache_manager.set("last_batch_run", datetime.now().isoformat(), ttl=86400)
            
            logger.info("✅ Cache update completed")
            
        except Exception as e:
            logger.error(f"❌ Failed to update cache: {e}")
    
    async def run_manual_batch(self, symbols: List[str] = None):
        """수동 배치 실행 (테스트용)"""
        logger.info("🧪 Running manual batch for testing...")
        
        test_symbols = symbols or ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        try:
            # 소규모 테스트
            stock_data = await self.collect_stock_data(test_symbols)
            analyzed_stocks = await self.analyze_stocks(stock_data)
            watchlist = await self.select_watchlist(analyzed_stocks)
            
            logger.info("🧪 Manual batch test completed:")
            for tier, symbols in watchlist.items():
                logger.info(f"   - {tier}: {symbols}")
            
            return {
                'analyzed_stocks': analyzed_stocks,
                'watchlist': watchlist
            }
            
        except Exception as e:
            logger.error(f"❌ Manual batch test failed: {e}")
            raise
    
    async def run_quick_scan(self):
        """빠른 스캔 (장중 실시간 모니터링용)"""
        logger.info("⚡ Running quick scan for realtime monitoring...")
        
        try:
            # 주요 5개 종목만 빠르게 스캔
            stock_data = await self.collect_stock_data(self.quick_scan_symbols)
            analyzed_stocks = await self.analyze_stocks(stock_data)
            
            # 간단한 신호 체크만
            alerts = []
            for symbol, data in analyzed_stocks.items():
                signals = data['signals']
                if signals['signal_strength'] in ['STRONG_BUY', 'STRONG_SELL']:
                    alerts.append({
                        'symbol': symbol,
                        'signal': signals['signal_strength'],
                        'price': data['current_quote'].price,
                        'score': signals['total_score']
                    })
            
            if alerts:
                logger.info(f"🚨 Quick scan alerts: {alerts}")
                # 중요 신호만 캐시에 저장
                await self.cache_manager.set("quick_alerts", alerts, ttl=300)  # 5분
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Quick scan failed: {e}")
            return []
    
    async def run_lightweight_batch(self):
        """경량 배치 처리 (실시간 모드용)"""
        logger.info("🪶 Running lightweight batch processing...")
        
        try:
            # 1. 현재가 데이터만 수집 (과거 데이터 스킵)
            logger.info("📊 Step 1: Collecting current quotes only...")
            current_quotes = await self.collect_current_quotes_only(self.base_symbols)
            
            # 2. 기본 기술적 지표만 계산 (RSI, MACD만)
            logger.info("📈 Step 2: Calculating basic indicators...")
            basic_analysis = await self.basic_technical_analysis(current_quotes)
            
            # 3. 간단한 신호 탐지
            logger.info("🎯 Step 3: Basic signal detection...")
            simple_signals = await self.detect_simple_signals(basic_analysis)
            
            # 4. 캐시에만 저장 (DB 저장 스킵)
            logger.info("🔄 Step 4: Caching results...")
            await self.cache_results_only(simple_signals)
            
            logger.info("✅ Lightweight batch processing completed!")
            
        except Exception as e:
            logger.error(f"❌ Lightweight batch processing failed: {e}")
    
    async def collect_current_quotes_only(self, symbols: List[str]) -> Dict[str, Dict]:
        """현재가만 수집 (과거 데이터 스킵으로 속도 향상)"""
        logger.info(f"⚡ Collecting current quotes for {len(symbols)} symbols...")
        
        current_quotes = {}
        
        async with KISAPIClient() as client:
            for i, symbol in enumerate(symbols):
                try:
                    # Rate limiting을 더 짧게 (0.5초)
                    if i > 0:
                        await asyncio.sleep(0.5)
                    
                    # 현재가만 조회 (과거 데이터 스킵)
                    current_quote = await client.get_nasdaq_quote(symbol)
                    if current_quote:
                        current_quotes[symbol] = {
                            'current_quote': current_quote,
                            'collected_at': datetime.now()
                        }
                        logger.debug(f"✅ {symbol}: ${current_quote.price:.2f}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get quote for {symbol}: {e}")
                    continue
        
        logger.info(f"⚡ Collected {len(current_quotes)} current quotes")
        return current_quotes
    
    async def basic_technical_analysis(self, current_quotes: Dict[str, Dict]) -> Dict[str, Dict]:
        """기본 기술적 분석 (캐시된 과거 데이터 활용)"""
        logger.info(f"📊 Basic analysis for {len(current_quotes)} symbols...")
        
        analyzed_data = {}
        
        for symbol, data in current_quotes.items():
            try:
                # 캐시에서 과거 데이터 조회
                cached_history = await self.cache_manager.get(f"history_{symbol}")
                
                if cached_history and len(cached_history) >= 14:
                    # 기본 지표만 계산 (RSI, 단순 이동평균)
                    prices = [float(d['close']) for d in cached_history[-14:]]
                    current_price = data['current_quote'].price
                    
                    # 간단한 RSI 계산
                    rsi = self.calculate_simple_rsi(prices + [current_price])
                    
                    # 단순 이동평균
                    sma_5 = sum(prices[-5:]) / 5 if len(prices) >= 5 else current_price
                    sma_14 = sum(prices) / len(prices)
                    
                    analyzed_data[symbol] = {
                        'current_quote': data['current_quote'],
                        'rsi': rsi,
                        'sma_5': sma_5,
                        'sma_14': sma_14,
                        'trend': 'UP' if current_price > sma_5 > sma_14 else 'DOWN' if current_price < sma_5 < sma_14 else 'SIDEWAYS'
                    }
                else:
                    # 과거 데이터 없으면 현재가만 저장
                    analyzed_data[symbol] = {
                        'current_quote': data['current_quote'],
                        'rsi': 50.0,  # 중성값
                        'sma_5': data['current_quote'].price,
                        'sma_14': data['current_quote'].price,
                        'trend': 'UNKNOWN'
                    }
                    
            except Exception as e:
                logger.warning(f"⚠️ Basic analysis failed for {symbol}: {e}")
                continue
        
        return analyzed_data
    
    def calculate_simple_rsi(self, prices: List[float], period: int = 14) -> float:
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
    
    async def detect_simple_signals(self, analyzed_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """간단한 신호 탐지"""
        signals = {}
        
        for symbol, data in analyzed_data.items():
            try:
                current_price = data['current_quote'].price
                rsi = data['rsi']
                trend = data['trend']
                
                # 간단한 신호 로직
                signal_strength = 'HOLD'
                score = 0
                
                # RSI 기반 신호
                if rsi < 30 and trend != 'DOWN':
                    signal_strength = 'BUY'
                    score = 2
                elif rsi > 70 and trend != 'UP':
                    signal_strength = 'SELL'
                    score = -2
                elif rsi < 40 and trend == 'UP':
                    signal_strength = 'WEAK_BUY'
                    score = 1
                elif rsi > 60 and trend == 'DOWN':
                    signal_strength = 'WEAK_SELL'
                    score = -1
                
                signals[symbol] = {
                    'signal_strength': signal_strength,
                    'score': score,
                    'rsi': rsi,
                    'trend': trend,
                    'price': current_price
                }
                
            except Exception as e:
                logger.warning(f"⚠️ Signal detection failed for {symbol}: {e}")
                continue
        
        return signals
    
    async def cache_results_only(self, signals: Dict[str, Dict]):
        """결과를 캐시에만 저장 (DB 스킵)"""
        try:
            # 신호 캐시 (5분)
            await self.cache_manager.set("realtime_signals", signals, ttl=300)
            
            # 강한 신호만 별도 캐시 (10분)
            strong_signals = {
                symbol: data for symbol, data in signals.items()
                if data['signal_strength'] in ['BUY', 'SELL', 'STRONG_BUY', 'STRONG_SELL']
            }
            
            if strong_signals:
                await self.cache_manager.set("strong_signals", strong_signals, ttl=600)
                logger.info(f"🚨 Cached {len(strong_signals)} strong signals")
            
            # 마지막 실행 시간
            await self.cache_manager.set("last_realtime_scan", datetime.now().isoformat(), ttl=3600)
            
        except Exception as e:
            logger.error(f"❌ Failed to cache results: {e}")
