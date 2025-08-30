"""Logging configuration"""
import logging
import colorlog
from pathlib import Path

def setup_logger(name: str) -> logging.Logger:
    """Setup colored logger"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Console handler
        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
