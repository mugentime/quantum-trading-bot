"""Environment Manager - Strict separation of test/production environments"""
import os
import logging
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Trading environment types"""
    PRODUCTION = "production"
    TESTNET = "testnet"
    TESTING = "testing"
    DEVELOPMENT = "development"

class EnvironmentError(Exception):
    """Raised when environment violations occur"""
    pass

class EnvironmentManager:
    """Manages strict environment separation and validation"""
    
    def __init__(self):
        self._current_env = None
        self._env_validated = False
        self._production_safeguards = True
        self._alert_callback = None
        
    def initialize_environment(self, env_type: Environment, force: bool = False) -> bool:
        """Initialize and validate environment"""
        try:
            if self._current_env and not force:
                logger.warning(f"Environment already set to {self._current_env.value}")
                return True
            
            # Validate environment setup
            if not self._validate_environment_setup(env_type):
                raise EnvironmentError(f"Invalid environment setup for {env_type.value}")
            
            self._current_env = env_type
            self._env_validated = True
            
            # Set appropriate safeguards
            self._configure_environment_safeguards(env_type)
            
            logger.info(f"Environment initialized: {env_type.value}")
            
            # Send alert for production environment
            if env_type == Environment.PRODUCTION and self._alert_callback:
                self._alert_callback(f"PRODUCTION ENVIRONMENT ACTIVATED - LIVE TRADING ENABLED")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize environment {env_type.value}: {e}")
            raise EnvironmentError(f"Environment initialization failed: {e}")
    
    def require_environment(self, allowed_envs: list):
        """Require specific environment(s) or raise exception"""
        if not self._env_validated:
            raise EnvironmentError("Environment not initialized")
        
        if self._current_env not in allowed_envs:
            current = self._current_env.value if self._current_env else "unknown"
            allowed = [env.value for env in allowed_envs]
            raise EnvironmentError(f"Operation not allowed in {current} environment. Allowed: {allowed}")
    
    def require_testnet_only(self):
        """Require testnet environment only"""
        self.require_environment([Environment.TESTNET])
    
    def require_non_production(self):
        """Require non-production environment"""
        self.require_environment([Environment.TESTNET, Environment.TESTING, Environment.DEVELOPMENT])
    
    def is_production(self) -> bool:
        """Check if current environment is production"""
        return self._current_env == Environment.PRODUCTION
    
    def is_safe_for_testing(self) -> bool:
        """Check if environment is safe for testing"""
        return self._current_env in [Environment.TESTING, Environment.DEVELOPMENT]
    
    def get_current_environment(self) -> Optional[Environment]:
        """Get current environment"""
        return self._current_env
    
    def set_alert_callback(self, callback):
        """Set callback for environment alerts"""
        self._alert_callback = callback
    
    def _validate_environment_setup(self, env_type: Environment) -> bool:
        """Validate environment configuration"""
        try:
            if env_type == Environment.PRODUCTION:
                return self._validate_production_environment()
            elif env_type == Environment.TESTNET:
                return self._validate_testnet_environment()
            elif env_type in [Environment.TESTING, Environment.DEVELOPMENT]:
                return self._validate_test_environment()
            
            return False
            
        except Exception as e:
            logger.error(f"Environment validation error: {e}")
            return False
    
    def _validate_production_environment(self) -> bool:
        """Validate production environment setup"""
        # Check for production API keys
        prod_api_key = os.getenv('BINANCE_PROD_API_KEY')
        prod_secret = os.getenv('BINANCE_PROD_SECRET_KEY')
        
        if not prod_api_key or not prod_secret:
            logger.error("Production API keys not configured")
            return False
        
        # Check that testnet flag is disabled
        testnet_flag = os.getenv('BINANCE_TESTNET', 'false').lower()
        if testnet_flag == 'true':
            logger.error("BINANCE_TESTNET=true in production environment")
            return False
        
        # Additional production validations
        if not self._validate_production_safety_checks():
            return False
        
        logger.info("Production environment validation passed")
        return True
    
    def _validate_testnet_environment(self) -> bool:
        """Validate testnet environment setup"""
        # Check for testnet API keys
        testnet_api_key = os.getenv('BINANCE_API_KEY')
        testnet_secret = os.getenv('BINANCE_SECRET_KEY')
        
        if not testnet_api_key or not testnet_secret:
            logger.error("Testnet API keys not configured")
            return False
        
        # Check that testnet flag is enabled
        testnet_flag = os.getenv('BINANCE_TESTNET', 'false').lower()
        if testnet_flag != 'true':
            logger.error("BINANCE_TESTNET=false in testnet environment")
            return False
        
        logger.info("Testnet environment validation passed")
        return True
    
    def _validate_test_environment(self) -> bool:
        """Validate test environment setup"""
        # Test environments should not have production keys
        if os.getenv('BINANCE_PROD_API_KEY') or os.getenv('BINANCE_PROD_SECRET_KEY'):
            logger.error("Production API keys found in test environment")
            return False
        
        logger.info("Test environment validation passed")
        return True
    
    def _validate_production_safety_checks(self) -> bool:
        """Additional safety checks for production"""
        try:
            # Check that we're not in a development directory
            current_path = os.path.abspath('.')
            dev_indicators = ['test', 'dev', 'debug', 'temp']
            
            for indicator in dev_indicators:
                if indicator in current_path.lower():
                    logger.error(f"Production environment in development path: {current_path}")
                    return False
            
            # Check for test files in current directory
            test_files = [f for f in os.listdir('.') if f.startswith('test_')]
            if test_files:
                logger.warning(f"Test files found in production directory: {test_files[:3]}")
            
            return True
            
        except Exception as e:
            logger.error(f"Production safety check failed: {e}")
            return False
    
    def _configure_environment_safeguards(self, env_type: Environment):
        """Configure environment-specific safeguards"""
        if env_type == Environment.PRODUCTION:
            self._production_safeguards = True
            # Enable strictest validation
            from .data_authenticity_validator import authenticity_validator
            authenticity_validator.enable_strict_mode()
            
        elif env_type == Environment.TESTNET:
            self._production_safeguards = True
            # Enable normal validation
            from .data_authenticity_validator import authenticity_validator
            authenticity_validator.enable_strict_mode()
            
        else:  # Testing/Development
            self._production_safeguards = False
            # Allow more relaxed validation for testing
            
    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment configuration"""
        return {
            'current_environment': self._current_env.value if self._current_env else None,
            'environment_validated': self._env_validated,
            'production_safeguards': self._production_safeguards,
            'api_endpoint': self._get_api_endpoint(),
            'trading_enabled': self._is_trading_enabled(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_api_endpoint(self) -> str:
        """Get appropriate API endpoint for environment"""
        if self._current_env == Environment.PRODUCTION:
            return "https://api.binance.com"
        elif self._current_env == Environment.TESTNET:
            return "https://testnet.binancefuture.com"
        else:
            return "mock://localhost"
    
    def _is_trading_enabled(self) -> bool:
        """Check if trading is enabled in current environment"""
        return self._current_env in [Environment.PRODUCTION, Environment.TESTNET]
    
    def create_environment_report(self) -> str:
        """Create detailed environment report"""
        config = self.get_environment_config()
        
        report = f"""
=== ENVIRONMENT REPORT ===
Environment: {config['current_environment']}
Validated: {config['environment_validated']}
Safeguards: {config['production_safeguards']}
API Endpoint: {config['api_endpoint']}
Trading Enabled: {config['trading_enabled']}
Timestamp: {config['timestamp']}

Environment Variables:
- BINANCE_TESTNET: {os.getenv('BINANCE_TESTNET', 'not set')}
- BINANCE_API_KEY: {'set' if os.getenv('BINANCE_API_KEY') else 'not set'}
- BINANCE_SECRET_KEY: {'set' if os.getenv('BINANCE_SECRET_KEY') else 'not set'}
- BINANCE_PROD_API_KEY: {'set' if os.getenv('BINANCE_PROD_API_KEY') else 'not set'}

Security Status:
- Production safeguards: {'ACTIVE' if self._production_safeguards else 'DISABLED'}
- Environment locked: {'YES' if self._env_validated else 'NO'}
"""
        return report

# Global environment manager
environment_manager = EnvironmentManager()

def require_testnet():
    """Require testnet environment"""
    environment_manager.require_testnet_only()

def require_non_production():
    """Require non-production environment"""
    environment_manager.require_non_production()

def is_production() -> bool:
    """Check if in production environment"""
    return environment_manager.is_production()

def initialize_environment(env_type: Environment) -> bool:
    """Initialize trading environment"""
    return environment_manager.initialize_environment(env_type)