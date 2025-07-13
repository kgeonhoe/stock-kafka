"""
Database utilities for DuckDB operations
"""
import duckdb
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys
from loguru import logger

# Add config path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database_config import DatabaseConfig, get_db_path

class DuckDBManager:
    def __init__(self, db_path: str = None):
        # Use 1TB HDD path from config
        if db_path is None:
            db_path = DatabaseConfig.DUCKDB_MAIN_DB  # 직접 설정 사용
        
        self.db_path = Path(db_path)
        self.config = DatabaseConfig()
        
        # Ensure all directories exist
        DatabaseConfig.ensure_directories()
        
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            # Get optimized connection config
            conn_config = DatabaseConfig.get_connection_config()
            
            self.conn = duckdb.connect(str(self.db_path))
            
            # Apply performance settings
            for key, value in conn_config['config'].items():
                try:
                    if key == 'memory_limit':
                        self.conn.execute(f"SET memory_limit='{value}';")
                    elif key == 'threads':
                        self.conn.execute(f"SET threads={value};")
                    elif key == 'temp_directory':
                        self.conn.execute(f"SET temp_directory='{value}';")
                    elif key == 'max_memory':
                        self.conn.execute(f"SET max_memory='{value}';")
                except Exception as e:
                    logger.warning(f"Could not set {key}: {e}")
            
            self._create_tables()
            logger.info(f"🗄️  Database initialized at {self.db_path}")
            logger.info(f"💾 Using 1TB HDD: {DatabaseConfig.HDD_PATH}")
            
            # Log disk usage
            usage = DatabaseConfig.get_disk_usage()
            if 'error' not in usage:
                logger.info(f"💽 Available space: {usage['free_gb']} GB")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_tables(self):
        """Create all required tables"""
        
        # Raw realtime data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_realtime (
                id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP,
                symbol VARCHAR,
                price DECIMAL(10,4),
                volume BIGINT,
                high DECIMAL(10,4),
                low DECIMAL(10,4),
                open DECIMAL(10,4),
                close DECIMAL(10,4),
                change_percent DECIMAL(6,4),
                market VARCHAR,
                tier VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Daily summary table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY,
                date DATE,
                symbol VARCHAR,
                open DECIMAL(10,4),
                high DECIMAL(10,4),
                low DECIMAL(10,4),
                close DECIMAL(10,4),
                volume BIGINT,
                change_percent DECIMAL(6,4),
                volatility DECIMAL(6,4),
                avg_volume_20d BIGINT,
                rsi_14 DECIMAL(6,4),
                macd DECIMAL(6,4),
                macd_signal DECIMAL(6,4),
                bollinger_upper DECIMAL(10,4),
                bollinger_lower DECIMAL(10,4),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, symbol)
            )
        """)
        
        # Trading signals table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP,
                symbol VARCHAR,
                signal_type VARCHAR,
                signal_strength DECIMAL(3,2),
                price DECIMAL(10,4),
                volume BIGINT,
                indicators JSON,
                tier VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Watchlist table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY,
                symbol VARCHAR,
                tier VARCHAR,
                score DECIMAL(5,2),
                reasons TEXT,
                added_date DATE,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(symbol, tier)
            )
        """)
        
        # Portfolio table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY,
                symbol VARCHAR,
                action VARCHAR,
                quantity INTEGER,
                price DECIMAL(10,4),
                timestamp TIMESTAMP,
                signal_id INTEGER,
                profit_loss DECIMAL(10,4),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_realtime_symbol_timestamp ON raw_realtime(symbol, timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_summary_symbol_date ON daily_summary(symbol, date)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol_timestamp ON trading_signals(symbol, timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_tier_active ON watchlist(tier, is_active)")
        
        logger.info("Database tables created successfully")
    
    def insert_realtime_data(self, data: List[Dict[str, Any]]) -> bool:
        """Insert realtime data"""
        try:
            df = pd.DataFrame(data)
            self.conn.execute("INSERT INTO raw_realtime SELECT * FROM df")
            logger.debug(f"Inserted {len(data)} realtime records")
            return True
        except Exception as e:
            logger.error(f"Failed to insert realtime data: {e}")
            return False
    
    def insert_daily_summary(self, data: List[Dict[str, Any]]) -> bool:
        """Insert daily summary data"""
        try:
            df = pd.DataFrame(data)
            self.conn.execute("""
                INSERT INTO daily_summary 
                SELECT * FROM df 
                ON CONFLICT (date, symbol) 
                DO UPDATE SET 
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    change_percent = EXCLUDED.change_percent,
                    volatility = EXCLUDED.volatility,
                    avg_volume_20d = EXCLUDED.avg_volume_20d,
                    rsi_14 = EXCLUDED.rsi_14,
                    macd = EXCLUDED.macd,
                    macd_signal = EXCLUDED.macd_signal,
                    bollinger_upper = EXCLUDED.bollinger_upper,
                    bollinger_lower = EXCLUDED.bollinger_lower
            """)
            logger.debug(f"Inserted {len(data)} daily summary records")
            return True
        except Exception as e:
            logger.error(f"Failed to insert daily summary: {e}")
            return False
    
    def insert_trading_signal(self, signal: Dict[str, Any]) -> bool:
        """Insert trading signal"""
        try:
            df = pd.DataFrame([signal])
            self.conn.execute("INSERT INTO trading_signals SELECT * FROM df")
            logger.info(f"Inserted trading signal for {signal.get('symbol')}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert trading signal: {e}")
            return False
    
    def get_watchlist_by_tier(self, tier: str) -> List[str]:
        """Get watchlist symbols by tier"""
        try:
            result = self.conn.execute("""
                SELECT symbol FROM watchlist 
                WHERE tier = ? AND is_active = TRUE 
                ORDER BY score DESC
            """, [tier]).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to get watchlist for tier {tier}: {e}")
            return []
    
    def update_watchlist(self, symbols: List[str], tier: str, scores: List[float] = None) -> bool:
        """Update watchlist for a specific tier"""
        try:
            # Deactivate existing entries for this tier
            self.conn.execute("UPDATE watchlist SET is_active = FALSE WHERE tier = ?", [tier])
            
            # Insert new entries
            for i, symbol in enumerate(symbols):
                score = scores[i] if scores and i < len(scores) else 50.0
                self.conn.execute("""
                    INSERT INTO watchlist (symbol, tier, score, added_date, is_active)
                    VALUES (?, ?, ?, ?, TRUE)
                    ON CONFLICT (symbol, tier) 
                    DO UPDATE SET 
                        score = EXCLUDED.score,
                        last_updated = CURRENT_TIMESTAMP,
                        is_active = TRUE
                """, [symbol, tier, score, datetime.now().date()])
            
            logger.info(f"Updated {len(symbols)} symbols in {tier} watchlist")
            return True
        except Exception as e:
            logger.error(f"Failed to update watchlist: {e}")
            return False
    
    def get_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical data for a symbol"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
                SELECT * FROM daily_summary 
                WHERE symbol = ? AND date >= ? AND date <= ?
                ORDER BY date ASC
            """
            
            df = self.conn.execute(query, [symbol, start_date.date(), end_date.date()]).df()
            return df
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def cleanup_old_data(self, days_to_keep: int = 7) -> bool:
        """Clean up old realtime data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            result = self.conn.execute("""
                DELETE FROM raw_realtime 
                WHERE timestamp < ?
            """, [cutoff_date])
            
            deleted_count = result.rowcount if hasattr(result, 'rowcount') else 0
            logger.info(f"Cleaned up {deleted_count} old realtime records")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False
    
    def optimize_tables(self):
        """Optimize database tables for better performance"""
        try:
            logger.info("🔧 Starting database optimization...")
            
            # Analyze tables for better query planning
            tables = ['raw_realtime', 'daily_summary', 'trading_signals', 'watchlist']
            for table in tables:
                try:
                    self.conn.execute(f"ANALYZE {table};")
                    logger.info(f"✅ Analyzed table: {table}")
                except Exception as e:
                    logger.warning(f"Could not analyze {table}: {e}")
            
            # Vacuum to reclaim space
            self.conn.execute("VACUUM;")
            logger.info("✅ Database vacuum completed")
            
            # Update table statistics
            self.conn.execute("PRAGMA optimize;")
            logger.info("✅ Database optimization completed")
            
            return True
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            return False
    
    def get_database_stats(self):
        """Get database statistics and disk usage"""
        try:
            stats = {}
            
            # Table sizes
            tables = ['raw_realtime', 'daily_summary', 'trading_signals', 'watchlist']
            for table in tables:
                try:
                    result = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                    stats[f"{table}_count"] = result[0] if result else 0
                except:
                    stats[f"{table}_count"] = 0
            
            # Database file size
            if self.db_path.exists():
                stats['db_size_mb'] = round(self.db_path.stat().st_size / (1024*1024), 2)
            else:
                stats['db_size_mb'] = 0
            
            # Disk usage
            disk_usage = DatabaseConfig.get_disk_usage()
            stats['disk_usage'] = disk_usage
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def backup_database(self, backup_name: str = None):
        """Create database backup on 1TB disk"""
        try:
            if backup_name is None:
                backup_name = f"stock_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            backup_path = Path(DatabaseConfig.BACKUP_DIR) / backup_name
            
            # Use DuckDB's COPY command for efficient backup
            self.conn.execute(f"COPY DATABASE TO '{backup_path}';")
            
            logger.info(f"✅ Database backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return None
    
    def archive_old_data(self, cutoff_date: datetime, archive_name: str = None):
        """Archive old data to separate file"""
        try:
            if archive_name is None:
                archive_name = f"archived_data_{cutoff_date.strftime('%Y%m%d')}.db"
            
            archive_path = Path(DatabaseConfig.ARCHIVE_DIR) / archive_name
            
            # Create archive database
            archive_conn = duckdb.connect(str(archive_path))
            
            # Copy old data to archive
            old_data = self.conn.execute("""
                SELECT * FROM raw_realtime 
                WHERE timestamp < ?
            """, [cutoff_date]).fetchdf()
            
            if not old_data.empty:
                archive_conn.execute("CREATE TABLE raw_realtime AS SELECT * FROM old_data")
                logger.info(f"✅ Archived {len(old_data)} records to {archive_path}")
                
                # Remove old data from main database
                self.conn.execute("DELETE FROM raw_realtime WHERE timestamp < ?", [cutoff_date])
                logger.info(f"✅ Removed old data from main database")
            
            archive_conn.close()
            return str(archive_path)
        except Exception as e:
            logger.error(f"Failed to archive data: {e}")
            return None
    
    def get_disk_space_info(self):
        """Get detailed disk space information"""
        try:
            info = {
                'hdd_path': DatabaseConfig.HDD_PATH,
                'database_path': str(self.db_path),
                'backup_dir': DatabaseConfig.BACKUP_DIR,
                'archive_dir': DatabaseConfig.ARCHIVE_DIR,
                'temp_dir': DatabaseConfig.DUCKDB_TEMP_DIR
            }
            
            # Disk usage
            usage = DatabaseConfig.get_disk_usage()
            info['disk_usage'] = usage
            
            # Directory sizes
            for key, path in [
                ('db_size', self.db_path.parent),
                ('backup_size', Path(DatabaseConfig.BACKUP_DIR)),
                ('archive_size', Path(DatabaseConfig.ARCHIVE_DIR))
            ]:
                if path.exists():
                    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    info[key + '_mb'] = round(total_size / (1024*1024), 2)
                else:
                    info[key + '_mb'] = 0
            
            return info
        except Exception as e:
            logger.error(f"Failed to get disk space info: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

# Global database instance
db_manager = DuckDBManager()
