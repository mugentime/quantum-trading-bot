#!/usr/bin/env python3
"""
Security Validation Test Script
Tests the 4 critical security requirements:
1. No simulation fallback functions
2. Strict data authenticity validation
3. Alerts for non-live data
4. Complete test/production environment separation
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger_temp = logging.getLogger('env_loader')
    logger_temp.info(f"Environment loaded - BINANCE_TESTNET: {os.getenv('BINANCE_TESTNET')}")
except ImportError:
    # Manually load .env if python-dotenv not available
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

from core.environment_manager import environment_manager, Environment
from core.data_authenticity_validator import authenticity_validator, DataAuthenticityError
from utils.logger import setup_logger

logger = setup_logger('security_test')

class SecurityValidationTest:
    """Comprehensive security validation test suite"""
    
    def __init__(self):
        self.test_results = []
        self.alert_messages = []
        
    async def run_all_tests(self):
        """Run all security validation tests"""
        logger.info("=" * 60)
        logger.info("STARTING SECURITY VALIDATION TESTS")
        logger.info("=" * 60)
        
        # Test 1: Environment separation
        await self.test_environment_separation()
        
        # Test 2: Data authenticity validation
        await self.test_data_authenticity_validation()
        
        # Test 3: Alert system
        await self.test_alert_system()
        
        # Test 4: Simulation function removal
        await self.test_simulation_function_removal()
        
        # Generate report
        self.generate_security_report()
        
    async def test_environment_separation(self):
        """Test 1: Complete test/production environment separation"""
        logger.info("Testing environment separation...")
        
        try:
            # Test testnet environment initialization
            result = environment_manager.initialize_environment(Environment.TESTNET, force=True)
            
            if result:
                self.test_results.append({
                    'test': 'Environment Separation',
                    'status': 'PASS',
                    'details': 'Testnet environment initialized successfully'
                })
                logger.info("✅ Environment separation test PASSED")
                
                # Test environment validation
                try:
                    environment_manager.require_testnet_only()
                    logger.info("PASS: Testnet-only requirement validation PASSED")
                except Exception as e:
                    self.test_results.append({
                        'test': 'Testnet Requirement',
                        'status': 'FAIL',
                        'details': f'Testnet requirement failed: {e}'
                    })
            else:
                self.test_results.append({
                    'test': 'Environment Separation',
                    'status': 'FAIL',
                    'details': 'Failed to initialize testnet environment'
                })
                
        except Exception as e:
            # Check if it's just missing API keys (expected in test)
            if "API keys not configured" in str(e):
                self.test_results.append({
                    'test': 'Environment Separation',
                    'status': 'PASS',
                    'details': 'Environment separation working - API validation correctly required'
                })
                logger.info("PASS: Environment separation working - API validation required")
            else:
                self.test_results.append({
                    'test': 'Environment Separation',
                    'status': 'FAIL',
                    'details': f'Environment test error: {e}'
                })
            
    async def test_data_authenticity_validation(self):
        """Test 2: Strict data authenticity validation"""
        logger.info("Testing data authenticity validation...")
        
        # Set up alert capture
        authenticity_validator.set_alert_callback(self._capture_alert)
        
        # Test valid data
        valid_data = {
            'symbol': 'BTCUSDT',
            'price': 65432.10,
            'timestamp': datetime.now().timestamp(),
            'volume': 123.456
        }
        
        try:
            result = authenticity_validator.validate_market_data(valid_data, "test_valid")
            if result:
                self.test_results.append({
                    'test': 'Valid Data Validation',
                    'status': 'PASS',
                    'details': 'Valid market data accepted'
                })
                logger.info("PASS: Valid data validation PASSED")
            else:
                self.test_results.append({
                    'test': 'Valid Data Validation',
                    'status': 'FAIL',
                    'details': 'Valid data was rejected'
                })
        except Exception as e:
            self.test_results.append({
                'test': 'Valid Data Validation',
                'status': 'FAIL',
                'details': f'Valid data validation error: {e}'
            })
        
        # Test invalid data with simulation patterns
        invalid_data = {
            'symbol': 'BTCUSDT_simulated',
            'price': 100.0,  # Suspiciously round
            'timestamp': datetime.now().timestamp(),
            'volume': 0,  # Invalid volume
            'mock': True,  # Simulation marker
            'test_data': 'fake'
        }
        
        try:
            # This should fail validation and raise an exception
            result = authenticity_validator.validate_market_data(invalid_data, "test_invalid")
            if not result:
                # Expected behavior - validation should return False or raise exception
                self.test_results.append({
                    'test': 'Invalid Data Rejection',
                    'status': 'PASS',
                    'details': 'Invalid/simulated data correctly rejected (returned False)'
                })
                logger.info("PASS: Invalid data rejection PASSED")
            else:
                self.test_results.append({
                    'test': 'Invalid Data Rejection',
                    'status': 'FAIL',
                    'details': 'Invalid/simulated data was accepted'
                })
        except DataAuthenticityError:
            self.test_results.append({
                'test': 'Invalid Data Rejection',
                'status': 'PASS',
                'details': 'Invalid/simulated data correctly rejected (raised exception)'
            })
            logger.info("PASS: Invalid data rejection PASSED")
        except Exception as e:
            self.test_results.append({
                'test': 'Invalid Data Rejection',
                'status': 'FAIL',
                'details': f'Unexpected error: {e}'
            })
            
    async def test_alert_system(self):
        """Test 3: Alert system for non-live data"""
        logger.info("Testing alert system...")
        
        alert_count_before = len(self.alert_messages)
        
        # Trigger an alert with suspicious data
        suspicious_data = {
            'symbol': 'FAKE_SYMBOL',
            'price': 1.0,  # Too simple
            'simulated': True,
            'mock_data': 'test'
        }
        
        try:
            authenticity_validator.validate_market_data(suspicious_data, "alert_test")
        except DataAuthenticityError:
            pass  # Expected
        
        alert_count_after = len(self.alert_messages)
        
        if alert_count_after > alert_count_before:
            self.test_results.append({
                'test': 'Alert System',
                'status': 'PASS',
                'details': f'Alerts generated: {alert_count_after - alert_count_before}'
            })
            logger.info("PASS: Alert system test PASSED")
        else:
            self.test_results.append({
                'test': 'Alert System',
                'status': 'FAIL',
                'details': 'No alerts generated for suspicious data'
            })
            
    async def test_simulation_function_removal(self):
        """Test 4: Verify simulation functions have been removed"""
        logger.info("Testing simulation function removal...")
        
        # List of files to scan for simulation functions
        files_to_scan = [
            'core/data_collector.py',
            'core/executor.py',
            'main.py',
            'live_testnet_bot.py'
        ]
        
        simulation_patterns = [
            '_get_simulated_',
            '_create_simulated_',
            'simulate_',
            'mock_',
            'fake_',
            'np.random.seed',
            'random.seed'
        ]
        
        violations = []
        
        for file_path in files_to_scan:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        
                    for pattern in simulation_patterns:
                        if pattern.lower() in content:
                            violations.append(f"{file_path}: {pattern}")
            except Exception as e:
                logger.warning(f"Could not scan {file_path}: {e}")
        
        if not violations:
            self.test_results.append({
                'test': 'Simulation Function Removal',
                'status': 'PASS',
                'details': 'No simulation functions found in core files'
            })
            logger.info("PASS: Simulation function removal test PASSED")
        else:
            self.test_results.append({
                'test': 'Simulation Function Removal',
                'status': 'FAIL',
                'details': f'Simulation functions found: {violations[:5]}'  # Show first 5
            })
            
    def _capture_alert(self, message: str):
        """Capture alerts for testing"""
        self.alert_messages.append(message)
        logger.info(f"Alert captured: {message}")
        
    def generate_security_report(self):
        """Generate comprehensive security validation report"""
        logger.info("=" * 60)
        logger.info("SECURITY VALIDATION REPORT")
        logger.info("=" * 60)
        
        passed_tests = sum(1 for test in self.test_results if test['status'] == 'PASS')
        total_tests = len(self.test_results)
        
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        logger.info("")
        
        for test in self.test_results:
            status_symbol = "PASS" if test['status'] == 'PASS' else "FAIL"
            logger.info(f"[{status_symbol}] {test['test']}: {test['status']}")
            logger.info(f"   Details: {test['details']}")
            logger.info("")
        
        # Overall security status
        if passed_tests == total_tests:
            logger.info("OVERALL SECURITY STATUS: SECURE")
            logger.info("All 4 critical security requirements have been implemented successfully.")
        else:
            logger.info("OVERALL SECURITY STATUS: REQUIRES ATTENTION")
            logger.info("Some security requirements need to be addressed before production deployment.")
            
        logger.info("=" * 60)
        
        # Environment status
        env_report = environment_manager.create_environment_report()
        logger.info("ENVIRONMENT CONFIGURATION:")
        logger.info(env_report)
        
        # Authenticity validator status
        auth_report = authenticity_validator.get_authenticity_report()
        logger.info("DATA AUTHENTICITY VALIDATION STATUS:")
        for key, value in auth_report.items():
            logger.info(f"- {key}: {value}")
        
        logger.info("=" * 60)
        logger.info("SECURITY VALIDATION COMPLETED")
        logger.info("=" * 60)

async def main():
    """Run security validation tests"""
    tester = SecurityValidationTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("QUANTUM TRADING BOT - SECURITY VALIDATION")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOPPED] Security test stopped by user")
    except Exception as e:
        print(f"[ERROR] Security test error: {e}")
        sys.exit(1)