"""
Logging configuration
"""
import os
import sys
from loguru import logger
from datetime import datetime

def setup_logging():
    """Setup logging configuration"""
    
    # Remove default logger
    logger.remove()
    
    # Console logging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=os.getenv("LOG_LEVEL", "INFO"),
        colorize=True
    )
    
    # File logging
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # General application logs
    logger.add(
        f"{log_dir}/app.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        compression="zip"
    )
    
    # Error logs
    logger.add(
        f"{log_dir}/error.log",
        rotation="1 day",
        retention="30 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        compression="zip"
    )
    
    # Trading signals logs
    logger.add(
        f"{log_dir}/signals.log",
        rotation="1 day",
        retention="90 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        compression="zip",
        filter=lambda record: "SIGNAL" in record["message"]
    )

# Initialize logging
setup_logging()

# Export logger
__all__ = ['logger']
