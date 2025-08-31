#!/usr/bin/env python3
"""
Production Logging Configuration
Optimized for Railway deployment with structured logging and monitoring
"""

import logging
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback

class ProductionFormatter(logging.Formatter):
    """Custom formatter for production logging with structured output"""
    
    def __init__(self):
        super().__init__()
        self.hostname = os.getenv('RAILWAY_DEPLOYMENT_ID', 'local')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
    def format(self, record):
        """Format log record as structured JSON for production"""
        
        # Base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'hostname': self.hostname,
            'environment': self.environment,
            'python_module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        # Add trading-specific context if available
        if hasattr(record, 'trading_context'):
            log_entry['trading_context'] = record.trading_context
            
        return json.dumps(log_entry, ensure_ascii=False)

class TradingLogger:
    """Enhanced logger for trading operations with context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.trading_context = {}
        
    def set_trading_context(self, context: Dict[str, Any]):
        """Set trading context for all subsequent log entries"""
        self.trading_context.update(context)
        
    def clear_trading_context(self):
        """Clear trading context"""
        self.trading_context = {}
        
    def _log_with_context(self, level: int, message: str, extra: Optional[Dict] = None):
        """Log with trading context"""
        extra = extra or {}
        extra['trading_context'] = self.trading_context
        self.logger.log(level, message, extra={'extra_fields': extra})
        
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, kwargs)
        
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, kwargs)
        
    def error(self, message: str, **kwargs):
        self._log_with_context(logging.ERROR, message, kwargs)
        
    def critical(self, message: str, **kwargs):
        self._log_with_context(logging.CRITICAL, message, kwargs)
        
    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, kwargs)
        
    def trade_executed(self, trade_data: Dict[str, Any]):
        """Log trade execution with structured data"""
        self.info("Trade executed", trade_data=trade_data, event_type="trade_execution")
        
    def signal_generated(self, signal_data: Dict[str, Any]):
        """Log signal generation with structured data"""
        self.info("Trading signal generated", signal_data=signal_data, event_type="signal_generation")
        
    def position_opened(self, position_data: Dict[str, Any]):
        """Log position opening with structured data"""
        self.info("Position opened", position_data=position_data, event_type="position_opened")
        
    def position_closed(self, position_data: Dict[str, Any]):
        """Log position closing with structured data"""
        self.info("Position closed", position_data=position_data, event_type="position_closed")
        
    def risk_violation(self, risk_data: Dict[str, Any]):
        """Log risk management violations"""
        self.warning("Risk management violation", risk_data=risk_data, event_type="risk_violation")
        
    def system_alert(self, alert_data: Dict[str, Any]):
        """Log system alerts"""
        self.critical("System alert", alert_data=alert_data, event_type="system_alert")

def setup_production_logging(log_level: str = None) -> None:
    """Setup production logging configuration for Railway"""
    
    # Determine log level
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
    level = getattr(logging, log_level, logging.INFO)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []
    
    # Setup production handler
    if os.getenv('ENVIRONMENT') == 'production':
        # Production: JSON structured logging to stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ProductionFormatter())
    else:
        # Development: Human-readable logging
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('ccxt').setLevel(logging.INFO)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    
    # Log startup information
    startup_logger = TradingLogger('production_logger')
    startup_logger.info("Production logging initialized", 
                       log_level=log_level,
                       environment=os.getenv('ENVIRONMENT', 'unknown'),
                       deployment_id=os.getenv('RAILWAY_DEPLOYMENT_ID', 'local'))

def get_trading_logger(name: str) -> TradingLogger:
    """Get a trading logger instance"""
    return TradingLogger(name)

class PerformanceTimer:
    """Context manager for timing operations with automatic logging"""
    
    def __init__(self, logger: TradingLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.debug(f"Starting {self.operation}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"Completed {self.operation}", 
                           duration_seconds=duration,
                           event_type="performance_timing")
        else:
            self.logger.error(f"Failed {self.operation}", 
                            duration_seconds=duration,
                            error_type=exc_type.__name__,
                            error_message=str(exc_val),
                            event_type="performance_timing")

# Example usage and testing
if __name__ == "__main__":
    # Test the production logging setup
    setup_production_logging()
    
    # Test trading logger
    logger = get_trading_logger("test")
    logger.set_trading_context({"symbol": "ETHUSDT", "strategy": "scalping"})
    
    logger.info("Testing production logging")
    logger.trade_executed({
        "symbol": "ETHUSDT",
        "side": "buy",
        "quantity": 0.1,
        "price": 2500.0,
        "profit": 15.25
    })
    
    # Test performance timer
    with PerformanceTimer(logger, "test operation"):
        import time
        time.sleep(0.1)  # Simulate work
    
    print("Production logging test completed")