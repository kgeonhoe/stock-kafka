"""
Database Configuration for Stock Kafka Pipeline
DuckDB 데이터베이스 경로 및 설정 관리
"""

import os
from pathlib import Path

class DatabaseConfig:
    """데이터베이스 설정 관리"""
    
    # 1TB HDD 디스크 경로
    HDD_PATH = "/dev/hdd"
    
    # DuckDB 설정
    DUCKDB_BASE_DIR = f"{HDD_PATH}/stock-kafka/duckdb"
    DUCKDB_MAIN_DB = f"{DUCKDB_BASE_DIR}/stock_data.db"
    DUCKDB_CACHE_DB = f"{DUCKDB_BASE_DIR}/cache_data.db"
    DUCKDB_ANALYTICS_DB = f"{DUCKDB_BASE_DIR}/analytics_data.db"
    
    # 백업 및 아카이브 설정
    BACKUP_DIR = f"{HDD_PATH}/stock-kafka/backups"
    ARCHIVE_DIR = f"{HDD_PATH}/stock-kafka/archives"
    
    # DuckDB 성능 설정
    DUCKDB_MEMORY_LIMIT = "8GB"  # 메모리 제한
    DUCKDB_THREADS = 4           # 스레드 수
    DUCKDB_TEMP_DIR = f"{HDD_PATH}/stock-kafka/temp"
    
    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리들 생성"""
        directories = [
            cls.DUCKDB_BASE_DIR,
            cls.BACKUP_DIR,
            cls.ARCHIVE_DIR,
            cls.DUCKDB_TEMP_DIR
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✅ Directory ensured: {directory}")
    
    @classmethod
    def get_connection_config(cls):
        """DuckDB 연결 설정 반환"""
        return {
            'database': cls.DUCKDB_MAIN_DB,
            'config': {
                'memory_limit': cls.DUCKDB_MEMORY_LIMIT,
                'threads': cls.DUCKDB_THREADS,
                'temp_directory': cls.DUCKDB_TEMP_DIR,
                'max_memory': '8GB',
                'enable_progress_bar': True,
                'enable_progress_bar_print': False
            }
        }
    
    @classmethod
    def get_disk_usage(cls):
        """디스크 사용량 확인"""
        import shutil
        
        try:
            total, used, free = shutil.disk_usage(cls.HDD_PATH)
            return {
                'total_gb': round(total / (1024**3), 2),
                'used_gb': round(used / (1024**3), 2),
                'free_gb': round(free / (1024**3), 2),
                'usage_percent': round((used / total) * 100, 1)
            }
        except Exception as e:
            return {'error': str(e)}
    
    @classmethod
    def print_config_info(cls):
        """설정 정보 출력"""
        print("🗄️  DuckDB Configuration")
        print("=" * 50)
        print(f"📍 HDD Path: {cls.HDD_PATH}")
        print(f"🗄️  Main DB: {cls.DUCKDB_MAIN_DB}")
        print(f"⚡ Cache DB: {cls.DUCKDB_CACHE_DB}")
        print(f"📊 Analytics DB: {cls.DUCKDB_ANALYTICS_DB}")
        print(f"💾 Memory Limit: {cls.DUCKDB_MEMORY_LIMIT}")
        print(f"🔧 Threads: {cls.DUCKDB_THREADS}")
        print("")
        
        # 디스크 사용량
        usage = cls.get_disk_usage()
        if 'error' not in usage:
            print(f"💽 Disk Usage:")
            print(f"   Total: {usage['total_gb']} GB")
            print(f"   Used:  {usage['used_gb']} GB ({usage['usage_percent']}%)")
            print(f"   Free:  {usage['free_gb']} GB")
        else:
            print(f"❌ Disk usage error: {usage['error']}")

# 환경변수로도 설정 가능
def get_db_path():
    """환경변수 또는 기본값으로 DB 경로 반환"""
    return os.getenv('DUCKDB_PATH', DatabaseConfig.DUCKDB_MAIN_DB)

def get_cache_db_path():
    """캐시 DB 경로 반환"""
    return os.getenv('DUCKDB_CACHE_PATH', DatabaseConfig.DUCKDB_CACHE_DB)

def get_analytics_db_path():
    """분석 DB 경로 반환"""
    return os.getenv('DUCKDB_ANALYTICS_PATH', DatabaseConfig.DUCKDB_ANALYTICS_DB)

if __name__ == "__main__":
    # 설정 테스트
    DatabaseConfig.ensure_directories()
    DatabaseConfig.print_config_info()
