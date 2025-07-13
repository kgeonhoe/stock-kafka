"""
Stock Data Processing Manager
모든 데이터 처리 로직을 통합 관리하는 메인 프로세서
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from enum import Enum
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kis_api_client import KISAPIClient
from src.api.bulk_data_client import BulkDataClient
from src.cache_manager import CacheManager
from src.database import DuckDBManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcessingMode(Enum):
    """처리 모드"""
    HISTORICAL = "historical"   # 과거 데이터 대량 적재
    REALTIME = "realtime"      # 실시간 모니터링
    DAILY = "daily"            # 일일 배치 처리
    SIGNALS = "signals"        # 신호 탐지
    MAINTENANCE = "maintenance" # 시스템 유지보수

class StockDataProcessor:
    """통합 주식 데이터 처리 관리자"""
    
    def __init__(self):
        self.kis_client = KISAPIClient()
        self.cache_manager = CacheManager()
        self.db_manager = DuckDBManager()
        self.is_running = False
        
        # 처리 대상 종목들
        self.symbols = {
            'tier1': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],  # 최우선
            'tier2': ['META', 'NVDA', 'NFLX', 'ADBE', 'CRM'],     # 우선
            'tier3': ['INTC', 'AMD', 'QCOM', 'AVGO', 'CSCO']      # 일반
        }
    
    async def start(self, mode: ProcessingMode, **kwargs):
        """처리 시작"""
        logger.info(f"🚀 Starting Stock Data Processor in {mode.value} mode...")
        self.is_running = True
        
        try:
            if mode == ProcessingMode.HISTORICAL:
                await self._process_historical_data(**kwargs)
            elif mode == ProcessingMode.REALTIME:
                await self._process_realtime_data(**kwargs)
            elif mode == ProcessingMode.DAILY:
                await self._process_daily_batch(**kwargs)
            elif mode == ProcessingMode.SIGNALS:
                await self._process_signals(**kwargs)
            elif mode == ProcessingMode.MAINTENANCE:
                await self._process_maintenance(**kwargs)
            else:
                raise ValueError(f"Unknown processing mode: {mode}")
                
        except KeyboardInterrupt:
            logger.info("⏹️ Processing interrupted by user")
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            raise
        finally:
            self.is_running = False
            logger.info("🛑 Stock Data Processor stopped")
    
    async def _process_historical_data(self, days_back: int = 30, **kwargs):
        """과거 데이터 대량 처리"""
        logger.info(f"📚 Processing historical data for {days_back} days...")
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        async with BulkDataClient(self.kis_client, self.cache_manager) as bulk_client:
            # Tier 1 종목 우선 처리
            for tier, symbols in self.symbols.items():
                logger.info(f"📊 Processing {tier} symbols: {symbols}")
                
                try:
                    results = await bulk_client.fetch_multiple_symbols_bulk(
                        symbols=symbols,
                        start_date=start_date,
                        end_date=end_date,
                        market="NASDAQ",
                        concurrent_limit=2 if tier == 'tier1' else 1
                    )
                    
                    # DuckDB에 저장
                    await self._save_historical_to_db(results)
                    
                    # Tier 간 휴식
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to process {tier}: {e}")
                    continue
    
    async def _process_realtime_data(self, **kwargs):
        """실시간 데이터 처리"""
        logger.info("⚡ Starting realtime data processing...")
        
        while self.is_running:
            try:
                # Tier 1 종목만 실시간 모니터링
                for symbol in self.symbols['tier1']:
                    await self._process_realtime_symbol(symbol)
                    await asyncio.sleep(0.5)  # API 부하 방지
                
                # 5분 간격으로 반복
                logger.info("💤 Realtime cycle completed, waiting 5 minutes...")
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Realtime processing error: {e}")
                await asyncio.sleep(60)  # 에러 시 1분 대기
    
    async def _process_daily_batch(self, **kwargs):
        """일일 배치 처리"""
        logger.info("🗓️ Starting daily batch processing...")
        
        try:
            # 1. 모든 종목 현재가 수집
            all_symbols = []
            for symbols in self.symbols.values():
                all_symbols.extend(symbols)
            
            current_data = await self._collect_current_quotes(all_symbols)
            
            # 2. 기술적 분석
            analyzed_data = await self._analyze_technical_indicators(current_data)
            
            # 3. 신호 탐지
            signals = await self._detect_trading_signals(analyzed_data)
            
            # 4. 결과 저장
            await self._save_daily_results(analyzed_data, signals)
            
            logger.info("✅ Daily batch processing completed")
            
        except Exception as e:
            logger.error(f"❌ Daily batch processing failed: {e}")
            raise
    
    async def _process_signals(self, **kwargs):
        """신호 탐지 처리"""
        logger.info("🎯 Starting signal detection processing...")
        
        # 캐시된 데이터로 빠른 신호 탐지
        try:
            for tier, symbols in self.symbols.items():
                tier_signals = []
                
                for symbol in symbols:
                    signal = await self._quick_signal_check(symbol)
                    if signal:
                        tier_signals.append(signal)
                
                if tier_signals:
                    logger.info(f"🚨 {tier} signals: {tier_signals}")
                    await self._cache_signals(tier, tier_signals)
            
        except Exception as e:
            logger.error(f"❌ Signal detection failed: {e}")
            raise
    
    async def _process_maintenance(self, **kwargs):
        """시스템 유지보수"""
        logger.info("🔧 Starting maintenance processing...")
        
        try:
            # 1. 오래된 데이터 정리
            cutoff_date = date.today() - timedelta(days=180)
            await self.db_manager.cleanup_old_data(cutoff_date)
            
            # 2. 캐시 정리
            await self.cache_manager.cleanup_expired()
            
            # 3. 데이터베이스 최적화
            await self.db_manager.optimize_tables()
            
            logger.info("✅ Maintenance completed")
            
        except Exception as e:
            logger.error(f"❌ Maintenance failed: {e}")
            raise
    
    async def _process_realtime_symbol(self, symbol: str):
        """실시간 단일 종목 처리"""
        try:
            # 현재가 조회
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
                current_price = float(output.get("last", "0"))
                
                # 간단한 신호 체크
                signal = await self._quick_signal_check(symbol, current_price)
                
                if signal:
                    logger.info(f"🚨 {symbol}: {signal}")
                    
                    # 실시간 알림 캐시
                    await self.cache_manager.set_stock_data(
                        f"realtime_alert:{symbol}",
                        signal,
                        expire_seconds=300
                    )
            
        except Exception as e:
            logger.error(f"❌ Realtime processing failed for {symbol}: {e}")
    
    async def _collect_current_quotes(self, symbols: List[str]) -> Dict:
        """현재가 데이터 수집"""
        current_data = {}
        
        for symbol in symbols:
            try:
                # 현재가 조회 로직
                quote = await self.kis_client.get_nasdaq_quote(symbol)
                if quote:
                    current_data[symbol] = quote
                    
                await asyncio.sleep(0.5)  # API 부하 방지
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to get quote for {symbol}: {e}")
                continue
        
        return current_data
    
    async def _analyze_technical_indicators(self, current_data: Dict) -> Dict:
        """기술적 지표 분석"""
        # 여기에 기술적 분석 로직 구현
        # 기존 batch_runner.py의 로직을 참고
        return current_data
    
    async def _detect_trading_signals(self, analyzed_data: Dict) -> Dict:
        """거래 신호 탐지"""
        # 여기에 신호 탐지 로직 구현
        signals = {}
        return signals
    
    async def _quick_signal_check(self, symbol: str, current_price: float = None) -> Optional[Dict]:
        """빠른 신호 체크"""
        try:
            # 캐시에서 과거 데이터 조회
            cached_prices = await self.cache_manager.get_stock_data(f"prices:{symbol}") or []
            
            if len(cached_prices) >= 14 and current_price:
                # 간단한 RSI 계산
                prices = cached_prices[-14:] + [current_price]
                rsi = self._calculate_rsi(prices)
                
                if rsi < 30:
                    return {"symbol": symbol, "signal": "BUY", "rsi": rsi, "price": current_price}
                elif rsi > 70:
                    return {"symbol": symbol, "signal": "SELL", "rsi": rsi, "price": current_price}
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Quick signal check failed for {symbol}: {e}")
            return None
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """RSI 계산"""
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
    
    async def _save_historical_to_db(self, results: Dict):
        """과거 데이터 DB 저장"""
        # DuckDB 저장 로직 구현
        pass
    
    async def _save_daily_results(self, analyzed_data: Dict, signals: Dict):
        """일일 결과 저장"""
        # 일일 분석 결과 저장 로직 구현
        pass
    
    async def _cache_signals(self, tier: str, signals: List[Dict]):
        """신호 캐시 저장"""
        await self.cache_manager.set_stock_data(
            f"signals:{tier}",
            signals,
            expire_seconds=600  # 10분
        )

# CLI 인터페이스
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Stock Data Processor')
    parser.add_argument(
        '--mode',
        type=str,
        choices=['historical', 'realtime', 'daily', 'signals', 'maintenance'],
        default='daily',
        help='Processing mode'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Days back for historical processing'
    )
    
    args = parser.parse_args()
    
    processor = StockDataProcessor()
    mode = ProcessingMode(args.mode)
    
    await processor.start(mode, days_back=args.days)

if __name__ == "__main__":
    asyncio.run(main())
