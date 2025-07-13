"""
Technical Analysis Indicators for Stock Analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TechnicalIndicators:
    """기술적 지표 데이터 클래스"""
    symbol: str
    timestamp: datetime
    rsi_14: float
    macd: float
    macd_signal: float
    macd_histogram: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_width: float
    sma_5: float
    sma_20: float
    sma_60: float
    ema_12: float
    ema_26: float
    stoch_k: float
    stoch_d: float
    williams_r: float
    momentum: float
    roc: float  # Rate of Change
    
class TechnicalAnalyzer:
    """기술적 분석 계산기"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI (Relative Strength Index) 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence) 계산"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """볼린저 밴드 계산"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        width = (upper - lower) / sma * 100
        
        return {
            'upper': upper,
            'middle': sma,
            'lower': lower,
            'width': width
        }
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """스토캐스틱 오실레이터 계산"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    @staticmethod
    def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Williams %R 계산"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return williams_r
    
    @staticmethod
    def calculate_momentum(prices: pd.Series, period: int = 10) -> pd.Series:
        """모멘텀 계산"""
        return prices / prices.shift(period) * 100
    
    @staticmethod
    def calculate_roc(prices: pd.Series, period: int = 10) -> pd.Series:
        """Rate of Change 계산"""
        return ((prices - prices.shift(period)) / prices.shift(period)) * 100
    
    @classmethod
    def calculate_all_indicators(cls, df: pd.DataFrame) -> TechnicalIndicators:
        """모든 기술적 지표 계산"""
        if len(df) < 60:  # 최소 60일 데이터 필요
            raise ValueError("Insufficient data for technical analysis (need at least 60 days)")
        
        # 데이터 정렬 (날짜 오름차순)
        df = df.sort_values('date')
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # RSI 계산
        rsi_14 = cls.calculate_rsi(close, 14)
        
        # MACD 계산
        macd_data = cls.calculate_macd(close)
        
        # 볼린저 밴드 계산
        bb_data = cls.calculate_bollinger_bands(close)
        
        # 이동평균 계산
        sma_5 = close.rolling(window=5).mean()
        sma_20 = close.rolling(window=20).mean()
        sma_60 = close.rolling(window=60).mean()
        
        # 지수이동평균 계산
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        
        # 스토캐스틱 계산
        stoch_data = cls.calculate_stochastic(high, low, close)
        
        # Williams %R 계산
        williams_r = cls.calculate_williams_r(high, low, close)
        
        # 모멘텀 및 ROC 계산
        momentum = cls.calculate_momentum(close)
        roc = cls.calculate_roc(close)
        
        # 최신 값 반환 (마지막 인덱스)
        latest_idx = -1
        
        return TechnicalIndicators(
            symbol=df['symbol'].iloc[latest_idx],
            timestamp=datetime.now(),
            rsi_14=float(rsi_14.iloc[latest_idx]) if not pd.isna(rsi_14.iloc[latest_idx]) else 50.0,
            macd=float(macd_data['macd'].iloc[latest_idx]) if not pd.isna(macd_data['macd'].iloc[latest_idx]) else 0.0,
            macd_signal=float(macd_data['signal'].iloc[latest_idx]) if not pd.isna(macd_data['signal'].iloc[latest_idx]) else 0.0,
            macd_histogram=float(macd_data['histogram'].iloc[latest_idx]) if not pd.isna(macd_data['histogram'].iloc[latest_idx]) else 0.0,
            bb_upper=float(bb_data['upper'].iloc[latest_idx]) if not pd.isna(bb_data['upper'].iloc[latest_idx]) else 0.0,
            bb_middle=float(bb_data['middle'].iloc[latest_idx]) if not pd.isna(bb_data['middle'].iloc[latest_idx]) else 0.0,
            bb_lower=float(bb_data['lower'].iloc[latest_idx]) if not pd.isna(bb_data['lower'].iloc[latest_idx]) else 0.0,
            bb_width=float(bb_data['width'].iloc[latest_idx]) if not pd.isna(bb_data['width'].iloc[latest_idx]) else 0.0,
            sma_5=float(sma_5.iloc[latest_idx]) if not pd.isna(sma_5.iloc[latest_idx]) else 0.0,
            sma_20=float(sma_20.iloc[latest_idx]) if not pd.isna(sma_20.iloc[latest_idx]) else 0.0,
            sma_60=float(sma_60.iloc[latest_idx]) if not pd.isna(sma_60.iloc[latest_idx]) else 0.0,
            ema_12=float(ema_12.iloc[latest_idx]) if not pd.isna(ema_12.iloc[latest_idx]) else 0.0,
            ema_26=float(ema_26.iloc[latest_idx]) if not pd.isna(ema_26.iloc[latest_idx]) else 0.0,
            stoch_k=float(stoch_data['k'].iloc[latest_idx]) if not pd.isna(stoch_data['k'].iloc[latest_idx]) else 50.0,
            stoch_d=float(stoch_data['d'].iloc[latest_idx]) if not pd.isna(stoch_data['d'].iloc[latest_idx]) else 50.0,
            williams_r=float(williams_r.iloc[latest_idx]) if not pd.isna(williams_r.iloc[latest_idx]) else -50.0,
            momentum=float(momentum.iloc[latest_idx]) if not pd.isna(momentum.iloc[latest_idx]) else 100.0,
            roc=float(roc.iloc[latest_idx]) if not pd.isna(roc.iloc[latest_idx]) else 0.0
        )
    
    @staticmethod
    def detect_signals(indicators: TechnicalIndicators, current_price: float) -> Dict[str, any]:
        """매수/매도 신호 탐지"""
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'neutral_signals': [],
            'total_score': 0,
            'signal_strength': 'NEUTRAL'
        }
        
        score = 0
        
        # RSI 신호
        if indicators.rsi_14 < 30:
            signals['buy_signals'].append('RSI_OVERSOLD')
            score += 2
        elif indicators.rsi_14 > 70:
            signals['sell_signals'].append('RSI_OVERBOUGHT')
            score -= 2
        elif 30 <= indicators.rsi_14 <= 50:
            signals['buy_signals'].append('RSI_FAVORABLE')
            score += 1
        
        # MACD 신호
        if indicators.macd > indicators.macd_signal and indicators.macd_histogram > 0:
            signals['buy_signals'].append('MACD_GOLDEN_CROSS')
            score += 2
        elif indicators.macd < indicators.macd_signal and indicators.macd_histogram < 0:
            signals['sell_signals'].append('MACD_DEATH_CROSS')
            score -= 2
        
        # 볼린저 밴드 신호
        if current_price <= indicators.bb_lower:
            signals['buy_signals'].append('BB_LOWER_TOUCH')
            score += 2
        elif current_price >= indicators.bb_upper:
            signals['sell_signals'].append('BB_UPPER_TOUCH')
            score -= 1
        elif indicators.bb_lower < current_price < indicators.bb_middle:
            signals['buy_signals'].append('BB_LOWER_HALF')
            score += 1
        
        # 이동평균 신호 (정배열)
        if indicators.sma_5 > indicators.sma_20 > indicators.sma_60:
            signals['buy_signals'].append('MA_GOLDEN_ALIGNMENT')
            score += 2
        elif indicators.sma_5 < indicators.sma_20 < indicators.sma_60:
            signals['sell_signals'].append('MA_DEATH_ALIGNMENT')
            score -= 2
        
        # 스토캐스틱 신호
        if indicators.stoch_k < 20 and indicators.stoch_d < 20:
            signals['buy_signals'].append('STOCH_OVERSOLD')
            score += 1
        elif indicators.stoch_k > 80 and indicators.stoch_d > 80:
            signals['sell_signals'].append('STOCH_OVERBOUGHT')
            score -= 1
        
        # Williams %R 신호
        if indicators.williams_r < -80:
            signals['buy_signals'].append('WILLIAMS_R_OVERSOLD')
            score += 1
        elif indicators.williams_r > -20:
            signals['sell_signals'].append('WILLIAMS_R_OVERBOUGHT')
            score -= 1
        
        # 모멘텀 신호
        if indicators.momentum > 105:
            signals['buy_signals'].append('POSITIVE_MOMENTUM')
            score += 1
        elif indicators.momentum < 95:
            signals['sell_signals'].append('NEGATIVE_MOMENTUM')
            score -= 1
        
        # 총 점수 및 신호 강도 결정
        signals['total_score'] = score
        
        if score >= 5:
            signals['signal_strength'] = 'STRONG_BUY'
        elif score >= 3:
            signals['signal_strength'] = 'BUY'
        elif score >= 1:
            signals['signal_strength'] = 'WEAK_BUY'
        elif score <= -5:
            signals['signal_strength'] = 'STRONG_SELL'
        elif score <= -3:
            signals['signal_strength'] = 'SELL'
        elif score <= -1:
            signals['signal_strength'] = 'WEAK_SELL'
        else:
            signals['signal_strength'] = 'NEUTRAL'
        
        return signals
