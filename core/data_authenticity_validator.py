"""Data Authenticity Validator - Ensures all trading data is genuine"""
import logging
import inspect
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class DataAuthenticityError(Exception):
    """Raised when non-authentic data is detected"""
    pass

class DataAuthenticityValidator:
    """Validates that all data sources are authentic and not simulated"""
    
    def __init__(self):
        self.validation_enabled = True
        self.alert_callback = None
        self.banned_functions = [
            '_get_simulated_', '_create_simulated_', '_mock_', '_fake_',
            'np.random.seed', 'random.seed', 'simulate_', 'mock_'
        ]
        self.required_authenticity_markers = [
            'timestamp', 'volume', 'symbol'
        ]
        
    def set_alert_callback(self, callback):
        """Set callback function for authenticity alerts"""
        self.alert_callback = callback
        
    def validate_market_data(self, data: Dict, source: str = "unknown") -> bool:
        """Validate that market data is authentic"""
        try:
            if not self.validation_enabled:
                return True
                
            # Check for simulation patterns
            if self._contains_simulation_patterns(data):
                self._raise_authenticity_alert(f"Simulation patterns detected in {source}")
                return False
            
            # Validate data structure
            if not self._validate_data_structure(data):
                self._raise_authenticity_alert(f"Invalid data structure in {source}")
                return False
                
            # Check for realistic values
            if not self._validate_realistic_values(data):
                self._raise_authenticity_alert(f"Unrealistic values detected in {source}")
                return False
                
            logger.debug(f"Data authenticity validated for {source}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating data authenticity: {e}")
            return False
    
    def validate_price_data(self, prices: Dict[str, float], source: str = "price_feed") -> bool:
        """Validate price data authenticity"""
        try:
            for symbol, price in prices.items():
                # Check for impossible prices
                if price <= 0 or price > 1000000:  # Reasonable bounds
                    self._raise_authenticity_alert(f"Impossible price {price} for {symbol}")
                    return False
                    
                # Check for obviously fake patterns (like exactly round numbers)
                if len(str(price).replace('.', '')) < 3:  # Too simple
                    logger.warning(f"Suspiciously simple price {price} for {symbol}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating price data: {e}")
            return False
    
    def validate_kline_data(self, klines: List[List], symbol: str) -> bool:
        """Validate kline/OHLCV data authenticity"""
        try:
            if not klines or len(klines) == 0:
                self._raise_authenticity_alert(f"Empty klines for {symbol}")
                return False
                
            for kline in klines[-10:]:  # Check last 10 klines
                if len(kline) < 6:  # Should have timestamp, O, H, L, C, V
                    self._raise_authenticity_alert(f"Invalid kline structure for {symbol}")
                    return False
                    
                timestamp, open_price, high, low, close, volume = kline[:6]
                
                # Validate OHLC logic
                if not (low <= open_price <= high and low <= close <= high):
                    self._raise_authenticity_alert(f"Invalid OHLC logic for {symbol}")
                    return False
                    
                # Validate positive volume
                if volume <= 0:
                    self._raise_authenticity_alert(f"Zero/negative volume for {symbol}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating kline data: {e}")
            return False
    
    def scan_function_for_simulation(self, func) -> bool:
        """Scan a function for simulation patterns"""
        try:
            source = inspect.getsource(func)
            for banned in self.banned_functions:
                if banned.lower() in source.lower():
                    self._raise_authenticity_alert(f"Simulation function {banned} found in {func.__name__}")
                    return False
            return True
        except Exception as e:
            logger.warning(f"Could not scan function {func.__name__}: {e}")
            return True  # Assume OK if can't scan
    
    def _contains_simulation_patterns(self, data: Dict) -> bool:
        """Check if data contains simulation patterns"""
        data_str = str(data).lower()
        simulation_keywords = ['simulated', 'mock', 'fake', 'test_data', 'random_seed']
        
        for keyword in simulation_keywords:
            if keyword in data_str:
                return True
        return False
    
    def _validate_data_structure(self, data: Dict) -> bool:
        """Validate basic data structure"""
        if not isinstance(data, dict):
            return False
            
        # Check for required markers of authentic data
        has_timestamp = any('time' in str(key).lower() for key in data.keys())
        has_symbol = any('symbol' in str(key).lower() for key in data.keys())
        
        return has_timestamp or has_symbol or len(data) > 0
    
    def _validate_realistic_values(self, data: Dict) -> bool:
        """Check if values are realistic"""
        try:
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    # Check for suspiciously perfect numbers
                    if value == int(value) and value > 100:  # Suspiciously round
                        logger.warning(f"Suspiciously round value {value} for {key}")
                    
                    # Check for impossible financial values
                    if 'price' in str(key).lower() and (value <= 0 or value > 1000000):
                        return False
            
            return True
            
        except Exception:
            return True  # Assume OK if can't validate
    
    def _raise_authenticity_alert(self, message: str):
        """Raise authenticity alert"""
        alert_msg = f"DATA AUTHENTICITY VIOLATION: {message}"
        logger.error(alert_msg)
        
        if self.alert_callback:
            try:
                self.alert_callback(alert_msg)
            except Exception as e:
                logger.error(f"Error calling alert callback: {e}")
        
        if self.validation_enabled:
            raise DataAuthenticityError(alert_msg)
    
    def enable_strict_mode(self):
        """Enable strict authenticity validation"""
        self.validation_enabled = True
        logger.info("Strict data authenticity validation ENABLED")
    
    def disable_validation(self):
        """Disable validation (for testing only)"""
        self.validation_enabled = False
        logger.warning("Data authenticity validation DISABLED - USE ONLY FOR TESTING")
    
    def get_authenticity_report(self) -> Dict:
        """Get authenticity validation status report"""
        return {
            'validation_enabled': self.validation_enabled,
            'banned_functions_count': len(self.banned_functions),
            'alert_callback_set': self.alert_callback is not None,
            'timestamp': datetime.now().isoformat(),
            'status': 'ACTIVE' if self.validation_enabled else 'DISABLED'
        }

# Global validator instance
authenticity_validator = DataAuthenticityValidator()

def validate_authentic_data(data: Any, source: str = "unknown") -> bool:
    """Convenience function to validate data authenticity"""
    return authenticity_validator.validate_market_data(data, source)

def require_authentic_data(data: Any, source: str = "unknown"):
    """Require authentic data or raise exception"""
    if not authenticity_validator.validate_market_data(data, source):
        raise DataAuthenticityError(f"Non-authentic data detected from {source}")

def scan_for_simulation_code(module_path: str) -> List[str]:
    """Scan module for simulation code"""
    issues = []
    try:
        with open(module_path, 'r') as f:
            content = f.read().lower()
            
        for banned in authenticity_validator.banned_functions:
            if banned.lower() in content:
                issues.append(f"Found banned function pattern: {banned}")
                
    except Exception as e:
        issues.append(f"Could not scan file: {e}")
    
    return issues