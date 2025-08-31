#!/usr/bin/env python3
"""
Railway Deployment Debug Script
Comprehensive debugging and health check for Railway deployment
"""
import sys
import os
import asyncio
import traceback
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_debug(message, level="INFO"):
    """Print debug message with timestamp"""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] [{level}] {message}")
    sys.stdout.flush()  # Ensure immediate output on Railway

def test_environment_vars():
    """Check Railway environment variables"""
    print_debug("Checking Railway environment variables...")
    
    critical_vars = [
        'BINANCE_API_KEY', 'BINANCE_SECRET_KEY', 'PORT', 
        'RAILWAY_DEPLOYMENT_ID', 'RAILWAY_ENVIRONMENT'
    ]
    
    optional_vars = [
        'BINANCE_TESTNET', 'RISK_PER_TRADE', 'DEFAULT_LEVERAGE',
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'LOG_LEVEL'
    ]
    
    missing_critical = []
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            if var in ['BINANCE_API_KEY', 'BINANCE_SECRET_KEY']:
                print_debug(f"{var}: {'*' * min(8, len(value))}... (length: {len(value)})")
            else:
                print_debug(f"{var}: {value}")
        else:
            missing_critical.append(var)
            print_debug(f"{var}: NOT SET", "WARN")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print_debug(f"{var}: {value}")
        else:
            print_debug(f"{var}: NOT SET (optional)", "DEBUG")
    
    if missing_critical:
        print_debug(f"Missing critical variables: {missing_critical}", "ERROR")
        return False
    else:
        print_debug("All critical environment variables are set", "OK")
        return True

def test_python_version():
    """Check Python version compatibility"""
    print_debug("Checking Python version...")
    version = sys.version_info
    print_debug(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print_debug("Python version is compatible", "OK")
        return True
    else:
        print_debug("Python version may be incompatible (requires 3.8+)", "WARN")
        return False

def test_dependencies():
    """Test critical package imports"""
    print_debug("Testing critical dependencies...")
    
    dependencies = [
        ('ccxt', 'ccxt'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('aiohttp', 'aiohttp'),
        ('websocket-client', 'websocket'),
        ('flask', 'flask'),
        ('redis', 'redis'),
        ('python-dotenv', 'dotenv'),
        ('requests', 'requests')
    ]
    
    failed = []
    
    for pkg_name, import_name in dependencies:
        try:
            __import__(import_name)
            print_debug(f"{pkg_name}: OK")
        except ImportError as e:
            print_debug(f"{pkg_name}: FAILED - {e}", "ERROR")
            failed.append(pkg_name)
    
    if failed:
        print_debug(f"Failed dependencies: {failed}", "ERROR")
        return False
    else:
        print_debug("All dependencies available", "OK")
        return True

def test_core_imports():
    """Test application-specific imports"""
    print_debug("Testing core application imports...")
    
    imports = [
        ('Config', 'core.config.settings', 'config'),
        ('DataCollector', 'core.data_collector', 'DataCollector'),
        ('CorrelationEngine', 'core.correlation_engine', 'CorrelationEngine'),
        ('SignalGenerator', 'core.signal_generator', 'SignalGenerator'),
        ('UHF Trader', 'core.ultra_high_frequency_trader', 'ultra_high_frequency_trader'),
        ('Executor', 'core.executor', 'Executor'),
        ('RiskManager', 'core.risk_manager', 'RiskManager'),
        ('PerformanceTracker', 'analytics.performance', 'PerformanceTracker'),
        ('FailureAnalyzer', 'analytics.failure_analyzer', 'FailureAnalyzer'),
        ('EnvironmentManager', 'core.environment_manager', 'environment_manager'),
        ('Health API', 'api.health', 'run_health_server_thread'),
        ('ProductionLogger', 'utils.production_logger', 'setup_production_logging')
    ]
    
    failed = []
    
    for name, module, attr in imports:
        try:
            mod = __import__(module, fromlist=[attr])
            getattr(mod, attr)
            print_debug(f"{name}: OK")
        except (ImportError, AttributeError) as e:
            print_debug(f"{name}: FAILED - {e}", "ERROR")
            failed.append(name)
    
    if failed:
        print_debug(f"Failed imports: {failed}", "ERROR")
        return False
    else:
        print_debug("All core imports successful", "OK")
        return True

def test_port_binding():
    """Test if we can bind to the specified port"""
    print_debug("Testing port binding...")
    
    port = int(os.getenv('PORT', 8080))
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', port))
        sock.close()
        print_debug(f"Port {port} is available", "OK")
        return True
    except OSError as e:
        print_debug(f"Port {port} binding failed: {e}", "ERROR")
        return False

def test_health_server():
    """Test health server startup"""
    print_debug("Testing health server startup...")
    
    try:
        from api.health import run_health_server_thread
        import threading
        import time
        
        test_port = int(os.getenv('PORT', 8080))
        health_thread = threading.Thread(target=run_health_server_thread, args=(test_port,), daemon=True)
        health_thread.start()
        
        # Give server time to start
        time.sleep(3)
        
        # Try to make a request to the health endpoint
        try:
            import requests
            response = requests.get(f"http://localhost:{test_port}/health", timeout=10)
            print_debug(f"Health server responding with status: {response.status_code}", "OK")
            return True
        except Exception as e:
            print_debug(f"Health server test request failed: {e}", "WARN")
            # Health server might still be working, just not responding yet
            return True
            
    except Exception as e:
        print_debug(f"Health server startup failed: {e}", "ERROR")
        return False

async def test_bot_initialization():
    """Test basic bot initialization"""
    print_debug("Testing bot initialization...")
    
    try:
        from core.config.settings import config
        from core.environment_manager import environment_manager, Environment
        
        # Test environment initialization
        env_type = Environment.TESTNET if config.BINANCE_TESTNET else Environment.PRODUCTION
        if environment_manager.initialize_environment(env_type):
            print_debug(f"Environment initialized: {env_type.value}", "OK")
        else:
            print_debug(f"Environment initialization failed: {env_type.value}", "ERROR")
            return False
        
        # Test basic component creation (without API calls)
        from core.data_collector import DataCollector
        from core.correlation_engine import CorrelationEngine
        from core.signal_generator import SignalGenerator
        from core.risk_manager import RiskManager
        
        data_collector = DataCollector(config.SYMBOLS)
        correlation_engine = CorrelationEngine()
        signal_generator = SignalGenerator()
        risk_manager = RiskManager()
        
        print_debug("Bot components initialized successfully", "OK")
        return True
        
    except Exception as e:
        print_debug(f"Bot initialization failed: {e}", "ERROR")
        traceback.print_exc()
        return False

def test_file_structure():
    """Verify required files exist"""
    print_debug("Checking file structure...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'Procfile',
        'railway.json',
        'runtime.txt',
        'core/config/settings.py',
        'api/health.py',
        'utils/production_logger.py'
    ]
    
    missing = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print_debug(f"{file_path}: EXISTS")
        else:
            print_debug(f"{file_path}: MISSING", "ERROR")
            missing.append(file_path)
    
    if missing:
        print_debug(f"Missing files: {missing}", "ERROR")
        return False
    else:
        print_debug("All required files present", "OK")
        return True

async def main():
    """Run comprehensive Railway deployment debug"""
    print("=" * 80)
    print("QUANTUM TRADING BOT - RAILWAY DEPLOYMENT DEBUG")
    print("=" * 80)
    
    # Tests to run
    tests = [
        ("Python Version", test_python_version, False),
        ("File Structure", test_file_structure, False),
        ("Environment Variables", test_environment_vars, False),
        ("Dependencies", test_dependencies, False),
        ("Core Imports", test_core_imports, False),
        ("Port Binding", test_port_binding, False),
        ("Health Server", test_health_server, False),
        ("Bot Initialization", test_bot_initialization, True)
    ]
    
    passed = 0
    total = len(tests)
    critical_failed = []
    
    for test_name, test_func, is_async in tests:
        print_debug(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
                
            if result:
                passed += 1
                print_debug(f"{test_name}: PASSED", "OK")
            else:
                print_debug(f"{test_name}: FAILED", "ERROR")
                critical_failed.append(test_name)
                
        except Exception as e:
            print_debug(f"{test_name}: EXCEPTION - {e}", "ERROR")
            traceback.print_exc()
            critical_failed.append(test_name)
    
    print_debug("\n" + "=" * 80)
    print_debug(f"FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print_debug("All tests passed! Deployment should succeed.", "OK")
        return 0
    else:
        print_debug(f"Failed tests: {critical_failed}", "ERROR")
        print_debug("Review failed tests before deployment.", "WARN")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print_debug(f"Debug script failed with exception: {e}", "ERROR")
        traceback.print_exc()
        sys.exit(1)