"""
Kafka Configuration Settings
"""
import os
from typing import Dict, List

class KafkaConfig:
    # Kafka Broker Settings
    BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    
    # Topics Configuration
    TOPICS = {
        'nasdaq_tier1_realtime': {
            'name': 'nasdaq-tier1-realtime',
            'partitions': 3,
            'replication_factor': 1,
            'config': {
                'cleanup.policy': 'delete',
                'retention.ms': 86400000,  # 1 day
                'segment.ms': 3600000,     # 1 hour
            }
        },
        'nasdaq_tier2_realtime': {
            'name': 'nasdaq-tier2-realtime',
            'partitions': 2,
            'replication_factor': 1,
            'config': {
                'cleanup.policy': 'delete',
                'retention.ms': 86400000,
                'segment.ms': 3600000,
            }
        },
        'nasdaq_tier3_realtime': {
            'name': 'nasdaq-tier3-realtime',
            'partitions': 1,
            'replication_factor': 1,
            'config': {
                'cleanup.policy': 'delete',
                'retention.ms': 86400000,
                'segment.ms': 3600000,
            }
        },
        'trading_signals': {
            'name': 'trading-signals',
            'partitions': 1,
            'replication_factor': 1,
            'config': {
                'cleanup.policy': 'delete',
                'retention.ms': 604800000,  # 7 days
            }
        },
        'portfolio_updates': {
            'name': 'portfolio-updates',
            'partitions': 1,
            'replication_factor': 1,
            'config': {
                'cleanup.policy': 'delete',
                'retention.ms': 2592000000,  # 30 days
            }
        }
    }
    
    # Producer Settings
    PRODUCER_CONFIG = {
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'acks': 'all',
        'retries': 3,
        'batch.size': 16384,
        'linger.ms': 1,
        'buffer.memory': 33554432,
        'compression.type': 'snappy',
        'max.in.flight.requests.per.connection': 5,
        'enable.idempotence': True,
    }
    
    # Consumer Settings
    CONSUMER_CONFIG = {
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': 'stock-processor-group',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
        'max.poll.records': 100,
        'session.timeout.ms': 30000,
        'heartbeat.interval.ms': 3000,
        'fetch.min.bytes': 1,
        'fetch.max.wait.ms': 500,
    }
    
    # Tier Configuration
    TIER_CONFIG = {
        'tier1': {
            'max_symbols': 15,
            'poll_interval': 1,  # seconds
            'priority': 'high'
        },
        'tier2': {
            'max_symbols': 30,
            'poll_interval': 5,
            'priority': 'medium'
        },
        'tier3': {
            'max_symbols': 100,
            'poll_interval': 30,
            'priority': 'low'
        }
    }

    @classmethod
    def get_topic_config(cls, topic_key: str) -> Dict:
        """Get topic configuration by key"""
        return cls.TOPICS.get(topic_key, {})
    
    @classmethod
    def get_all_topic_names(cls) -> List[str]:
        """Get all topic names"""
        return [config['name'] for config in cls.TOPICS.values()]
