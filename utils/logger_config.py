"""Enhanced logging configuration for monitoring systems"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

def setup_logger(name: str, level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """Setup enhanced logger with color support and file logging"""
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create formatters
    if COLORLOG_AVAILABLE:
        # Colored formatter for console
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        # Standard formatter if colorlog not available
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # File formatter (no colors)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    else:
        # Default file logging for monitoring
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Create dated log file
        date_str = datetime.now().strftime("%Y%m%d")
        log_filename = logs_dir / f"{name.lower()}_{date_str}.log"
        
        file_handler = logging.FileHandler(log_filename, mode='a')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    return logger

def setup_monitoring_logger(name: str) -> logging.Logger:
    """Setup logger specifically for monitoring components"""
    return setup_logger(
        name=name, 
        level=logging.INFO,
        log_file=f"logs/monitoring_{datetime.now().strftime('%Y%m%d')}.log"
    )

# For backward compatibility
def get_logger(name: str) -> logging.Logger:
    """Get or create a logger instance"""
    return setup_logger(name)