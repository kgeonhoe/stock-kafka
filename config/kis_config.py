"""
Korean Investment Securities API Configuration
"""
import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KISConfig:
    # API Credentials (환경변수에서 읽기)
    APP_KEY = os.getenv('KIS_APP_KEY', '')
    APP_SECRET = os.getenv('KIS_APP_SECRET', '')
    ACCESS_TOKEN = os.getenv('KIS_ACCESS_TOKEN', '')  # 빈 값이어도 됨, 자동 발급
    
    # API URLs
    BASE_URL = os.getenv('KIS_BASE_URL', 'https://openapi.koreainvestment.com:9443')
    PAPER_TRADING = os.getenv('KIS_PAPER_TRADING', 'true').lower() == 'true'
    
    # API Endpoints
    ENDPOINTS = {
        'oauth': '/oauth2/tokenP',
        'nasdaq_price': '/uapi/overseas-price/v1/quotations/price',
        'nasdaq_daily': '/uapi/overseas-price/v1/quotations/dailyprice', 
        'nasdaq_search': '/uapi/overseas-price/v1/quotations/search',
        'nasdaq_realtime': '/uapi/overseas-price/v1/quotations/realtime',
    }
    
    # Request Headers
    HEADERS = {
        'Content-Type': 'application/json',
        'authorization': f'Bearer {ACCESS_TOKEN}',
        'appkey': APP_KEY,
        'appsecret': APP_SECRET,
        'tr_id': '',  # Will be set dynamically
    }
    
    # NASDAQ Market Codes
    MARKET_CODES = {
        'NASDAQ': 'NAS',
        'NYSE': 'NYS',
        'AMEX': 'AMS',
    }
    
    # Trading Session Times (EST)
    TRADING_SESSIONS = {
        'pre_market': {
            'start': '04:00',
            'end': '09:30'
        },
        'regular': {
            'start': '09:30',
            'end': '16:00'
        },
        'after_hours': {
            'start': '16:00',
            'end': '20:00'
        }
    }
    
    # API Rate Limits
    RATE_LIMITS = {
        'per_second': 20,
        'per_minute': 1000,
        'per_hour': 10000,
    }
    
    # Watchlist Tiers
    WATCHLIST_TIERS = {
        'tier1': {
            'name': 'High Priority',
            'symbols': [],  # Will be populated from database
            'update_interval': 1,
            'max_symbols': 15
        },
        'tier2': {
            'name': 'Medium Priority', 
            'symbols': [],
            'update_interval': 5,
            'max_symbols': 30
        },
        'tier3': {
            'name': 'Low Priority',
            'symbols': [],
            'update_interval': 30,
            'max_symbols': 100
        }
    }
    
    # Popular NASDAQ Symbols for initial setup
    POPULAR_NASDAQ_SYMBOLS = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
        'META', 'NVDA', 'NFLX', 'PYPL', 'ADBE',
        'INTC', 'CMCSA', 'AVGO', 'TXN', 'QCOM',
        'COST', 'TMUS', 'SBUX', 'INTU', 'BKNG'
    ]

    @classmethod
    def validate_credentials(cls) -> bool:
        """Validate if required credentials are present"""
        return all([
            cls.APP_KEY,
            cls.APP_SECRET
            # ACCESS_TOKEN은 자동으로 발급받으므로 검증하지 않음
        ])
    
    @classmethod
    def get_market_code(cls, market: str) -> str:
        """Get market code for API requests"""
        return cls.MARKET_CODES.get(market.upper(), 'NAS')
    
    @classmethod
    def get_endpoint_url(cls, endpoint: str) -> str:
        """Get full URL for an endpoint"""
        path = cls.ENDPOINTS.get(endpoint, '')
        return f"{cls.BASE_URL}{path}"
