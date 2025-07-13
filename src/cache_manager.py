"""
Cache manager for Redis operations
"""
import redis
import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import os
from logger_config import logger

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )
        
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache value with TTL"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            
            self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
            
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
                
            # Try to parse as JSON
            try:
                return json.loads(value)
            except:
                return value
                
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
            
    def delete(self, key: str) -> bool:
        """Delete cache key"""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
            
    def exists(self, key: str) -> bool:
        """Check if cache key exists"""
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
            
    def get_ttl(self, key: str) -> int:
        """Get TTL for cache key"""
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for key {key}: {e}")
            return -1
            
    def set_hash(self, key: str, mapping: Dict, ttl: int = 3600) -> bool:
        """Set hash value"""
        try:
            # Convert values to strings
            str_mapping = {k: json.dumps(v, default=str) if isinstance(v, (dict, list)) else str(v) 
                          for k, v in mapping.items()}
            
            self.redis_client.hmset(key, str_mapping)
            if ttl > 0:
                self.redis_client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set hash {key}: {e}")
            return False
            
    def get_hash(self, key: str) -> Optional[Dict]:
        """Get hash value"""
        try:
            result = self.redis_client.hgetall(key)
            if not result:
                return None
                
            # Try to parse JSON values
            parsed_result = {}
            for k, v in result.items():
                try:
                    parsed_result[k] = json.loads(v)
                except:
                    parsed_result[k] = v
                    
            return parsed_result
        except Exception as e:
            logger.error(f"Failed to get hash {key}: {e}")
            return None
            
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment key {key}: {e}")
            return 0
            
    def set_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Set rate limit counter"""
        try:
            current = self.redis_client.incr(key)
            if current == 1:
                self.redis_client.expire(key, window)
            return current <= limit
        except Exception as e:
            logger.error(f"Failed to set rate limit {key}: {e}")
            return False
            
    def get_rate_limit_status(self, key: str) -> Dict:
        """Get rate limit status"""
        try:
            current = self.redis_client.get(key)
            ttl = self.redis_client.ttl(key)
            
            return {
                'current': int(current) if current else 0,
                'ttl': ttl,
                'remaining_time': ttl if ttl > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit status {key}: {e}")
            return {'current': 0, 'ttl': -1, 'remaining_time': 0}
            
    def cache_stock_data(self, symbol: str, data: Dict, ttl: int = 300) -> bool:
        """Cache stock data with symbol-specific key"""
        key = f"stock_data:{symbol}"
        data['cached_at'] = datetime.now().isoformat()
        return self.set(key, data, ttl)
        
    def get_cached_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get cached stock data"""
        key = f"stock_data:{symbol}"
        return self.get(key)
        
    def cache_technical_indicators(self, symbol: str, indicators: Dict, ttl: int = 600) -> bool:
        """Cache technical indicators"""
        key = f"indicators:{symbol}"
        indicators['calculated_at'] = datetime.now().isoformat()
        return self.set(key, indicators, ttl)
        
    def get_cached_indicators(self, symbol: str) -> Optional[Dict]:
        """Get cached technical indicators"""
        key = f"indicators:{symbol}"
        return self.get(key)
        
    def cache_watchlist(self, tier: str, symbols: List[str], ttl: int = 3600) -> bool:
        """Cache watchlist for a tier"""
        key = f"watchlist:{tier}"
        data = {
            'symbols': symbols,
            'updated_at': datetime.now().isoformat()
        }
        return self.set(key, data, ttl)
        
    def get_cached_watchlist(self, tier: str) -> Optional[List[str]]:
        """Get cached watchlist"""
        key = f"watchlist:{tier}"
        data = self.get(key)
        if data and isinstance(data, dict):
            return data.get('symbols', [])
        return None
        
    def cache_trading_signal(self, symbol: str, signal: Dict, ttl: int = 1800) -> bool:
        """Cache trading signal"""
        key = f"signal:{symbol}"
        signal['generated_at'] = datetime.now().isoformat()
        return self.set(key, signal, ttl)
        
    def get_cached_signal(self, symbol: str) -> Optional[Dict]:
        """Get cached trading signal"""
        key = f"signal:{symbol}"
        return self.get(key)
        
    def cleanup_expired_keys(self, pattern: str = "*") -> int:
        """Clean up expired keys matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            deleted = 0
            
            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -1:  # Keys without expiration
                    continue
                elif ttl == -2:  # Expired keys
                    self.redis_client.delete(key)
                    deleted += 1
                    
            logger.info(f"Cleaned up {deleted} expired keys")
            return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            return 0
            
    def get_memory_usage(self) -> Dict:
        """Get Redis memory usage statistics"""
        try:
            info = self.redis_client.info('memory')
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'used_memory_rss': info.get('used_memory_rss', 0),
                'used_memory_rss_human': info.get('used_memory_rss_human', '0B'),
                'maxmemory': info.get('maxmemory', 0),
                'maxmemory_human': info.get('maxmemory_human', '0B')
            }
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {}
            
    def get_connection_info(self) -> Dict:
        """Get Redis connection information"""
        try:
            info = self.redis_client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)) * 100
            }
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return {}
            
    def ping(self) -> bool:
        """Test Redis connection"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

# Global cache manager instance
cache_manager = CacheManager()
