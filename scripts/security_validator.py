#!/usr/bin/env python3
"""
Security Validation for Mainnet Deployment
Comprehensive security checks before production deployment
"""

import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any
import subprocess
import hashlib
import requests
from cryptography.fernet import Fernet

class SecurityValidator:
    def __init__(self):
        self.logger = self._setup_logging()
        self.security_issues = []
        self.warnings = []
        self.validation_results = {}
        
    def _setup_logging(self):
        """Setup security validation logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - SECURITY - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('security_validation.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def validate_api_keys(self) -> Tuple[bool, List[str]]:
        """Validate API key security"""
        self.logger.info("🔑 Validating API key security...")
        
        issues = []
        
        # Check for hardcoded API keys in code
        sensitive_patterns = [
            r'api[_-]?key\s*=\s*[\'"][^\'\"]{20,}[\'"]',
            r'secret[_-]?key\s*=\s*[\'"][^\'\"]{20,}[\'"]',
            r'binance[_-]?api[_-]?key\s*=\s*[\'"][^\'\"]{20,}[\'"]',
            r'telegram[_-]?bot[_-]?token\s*=\s*[\'"][^\'\"]{20,}[\'"]'
        ]
        
        # Scan Python files for hardcoded secrets
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in sensitive_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                issues.append(f"Hardcoded secret found in {filepath}")
                    except Exception as e:
                        continue
        
        # Check environment variable usage
        env_file_exists = os.path.exists('.env')
        if not env_file_exists:
            self.warnings.append("No .env file found - ensure environment variables are properly configured in Railway")
        
        # Check for secure key storage practices
        required_env_vars = [
            'BINANCE_API_KEY',
            'BINANCE_SECRET_KEY',
            'TELEGRAM_BOT_TOKEN'
        ]
        
        for var in required_env_vars:
            if os.getenv(var):
                # Keys are available in environment
                pass
            else:
                self.warnings.append(f"Environment variable {var} not set")
        
        return len(issues) == 0, issues
    
    def validate_network_security(self) -> Tuple[bool, List[str]]:
        """Validate network security configurations"""
        self.logger.info("🌐 Validating network security...")
        
        issues = []
        
        # Check SSL/TLS configuration
        ssl_verify_patterns = [
            r'ssl[_-]?verify\s*=\s*False',
            r'verify\s*=\s*False',
            r'CERT_NONE'
        ]
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in ssl_verify_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                issues.append(f"SSL verification disabled in {filepath}")
                    except Exception as e:
                        continue
        
        # Check for secure API endpoint usage
        insecure_patterns = [
            r'http://[^\\s\'\"]+binance',
            r'http://[^\\s\'\"]+api\\.',
        ]
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in insecure_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                issues.append(f"Insecure HTTP endpoint found in {filepath}")
                    except Exception as e:
                        continue
        
        return len(issues) == 0, issues
    
    def validate_input_sanitization(self) -> Tuple[bool, List[str]]:
        """Validate input sanitization and validation"""
        self.logger.info("🧹 Validating input sanitization...")
        
        issues = []
        
        # Check for SQL injection vulnerabilities
        sql_patterns = [
            r'execute\\s*\\(\\s*[\'"].*%s.*[\'"]',
            r'query\\s*\\(\\s*[\'"].*\\+.*[\'"]',
            r'cursor\\.execute\\s*\\(.*\\+.*\\)'
        ]
        
        # Check for command injection vulnerabilities
        command_patterns = [
            r'os\\.system\\s*\\(.*\\+',
            r'subprocess\\.[a-z]+\\s*\\(.*\\+',
            r'eval\\s*\\(',
            r'exec\\s*\\('
        ]
        
        all_patterns = sql_patterns + command_patterns
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in all_patterns:
                            if re.search(pattern, content):
                                issues.append(f"Potential injection vulnerability in {filepath}")
                    except Exception as e:
                        continue
        
        return len(issues) == 0, issues
    
    def validate_error_handling(self) -> Tuple[bool, List[str]]:
        """Validate error handling and information disclosure"""
        self.logger.info("⚠️ Validating error handling...")
        
        issues = []
        
        # Check for information disclosure in error messages
        disclosure_patterns = [
            r'print\\s*\\(.*exception.*\\)',
            r'logger\\.[a-z]+\\s*\\(.*traceback',
            r'raise\\s+Exception\\s*\\(.*\\+.*\\)'
        ]
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in disclosure_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                self.warnings.append(f"Potential information disclosure in {filepath}")
                    except Exception as e:
                        continue
        
        return True, issues  # Warnings only, not critical
    
    def validate_dependency_security(self) -> Tuple[bool, List[str]]:
        """Validate dependency security"""
        self.logger.info("📦 Validating dependency security...")
        
        issues = []
        
        try:
            # Check if requirements.txt exists
            if not os.path.exists('requirements.txt'):
                issues.append("requirements.txt not found")
                return False, issues
            
            # Run safety check if available
            try:
                result = subprocess.run(['safety', 'check', '-r', 'requirements.txt'],
                                      capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    if "vulnerabilities found" in result.stdout.lower():
                        issues.append("Known vulnerabilities found in dependencies")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self.warnings.append("Safety check not available - consider running: pip install safety")
            
            # Check for pinned versions
            with open('requirements.txt', 'r') as f:
                requirements = f.read().strip().split('\\n')
            
            unpinned = []
            for req in requirements:
                if req.strip() and not req.startswith('#'):
                    if '==' not in req and '>=' not in req and '~=' not in req:
                        unpinned.append(req.strip())
            
            if unpinned:
                self.warnings.append(f"Unpinned dependencies: {', '.join(unpinned)}")
        
        except Exception as e:
            issues.append(f"Failed to validate dependencies: {str(e)}")
        
        return len(issues) == 0, issues
    
    def validate_logging_security(self) -> Tuple[bool, List[str]]:
        """Validate logging security"""
        self.logger.info("📝 Validating logging security...")
        
        issues = []
        
        # Check for sensitive data in logs
        sensitive_log_patterns = [
            r'logger\\.[a-z]+\\s*\\(.*api[_-]?key',
            r'logger\\.[a-z]+\\s*\\(.*secret',
            r'logger\\.[a-z]+\\s*\\(.*password',
            r'print\\s*\\(.*api[_-]?key',
            r'print\\s*\\(.*secret'
        ]
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in sensitive_log_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                issues.append(f"Potential sensitive data logging in {filepath}")
                    except Exception as e:
                        continue
        
        return len(issues) == 0, issues
    
    def validate_configuration_security(self) -> Tuple[bool, List[str]]:
        """Validate configuration security"""
        self.logger.info("⚙️ Validating configuration security...")
        
        issues = []
        
        # Check Railway configuration
        if os.path.exists('railway.json'):
            try:
                with open('railway.json', 'r') as f:
                    config = json.load(f)
                
                # Check for secure environment settings
                if config.get('deploy', {}).get('healthcheckPath'):
                    # Health check is configured - good
                    pass
                else:
                    self.warnings.append("Health check not configured in railway.json")
                
                # Check restart policy
                restart_policy = config.get('deploy', {}).get('restartPolicyType')
                if restart_policy != 'ON_FAILURE':
                    self.warnings.append("Consider using ON_FAILURE restart policy")
                    
            except Exception as e:
                issues.append(f"Failed to validate railway.json: {str(e)}")
        
        # Check for debug mode in production
        debug_patterns = [
            r'debug\\s*=\\s*True',
            r'DEBUG\\s*=\\s*True',
            r'flask.*debug.*True'
        ]
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in debug_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                issues.append(f"Debug mode enabled in {filepath}")
                    except Exception as e:
                        continue
        
        return len(issues) == 0, issues
    
    def validate_trading_security(self) -> Tuple[bool, List[str]]:
        """Validate trading-specific security"""
        self.logger.info("💰 Validating trading security...")
        
        issues = []
        
        # Check for proper risk management
        risk_checks = [
            "MAX_POSITION_SIZE",
            "STOP_LOSS",
            "MAX_DAILY_LOSS",
            "POSITION_SIZE_LIMIT"
        ]
        
        found_risk_controls = 0
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for control in risk_checks:
                            if control in content:
                                found_risk_controls += 1
                                break
                    except Exception as e:
                        continue
        
        if found_risk_controls == 0:
            issues.append("No risk management controls found in code")
        
        # Check for testnet/mainnet switching logic
        testnet_patterns = [
            r'TESTNET\\s*=\\s*True',
            r'testnet.*True',
            r'sandbox.*True'
        ]
        
        testnet_logic_found = False
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in testnet_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                testnet_logic_found = True
                                break
                    except Exception as e:
                        continue
        
        if not testnet_logic_found:
            self.warnings.append("No testnet/mainnet switching logic found")
        
        return len(issues) == 0, issues
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive security validation"""
        self.logger.info("🔒 Starting comprehensive security validation...")
        
        start_time = datetime.utcnow()
        
        validation_functions = [
            ("API Keys", self.validate_api_keys),
            ("Network Security", self.validate_network_security),
            ("Input Sanitization", self.validate_input_sanitization),
            ("Error Handling", self.validate_error_handling),
            ("Dependency Security", self.validate_dependency_security),
            ("Logging Security", self.validate_logging_security),
            ("Configuration Security", self.validate_configuration_security),
            ("Trading Security", self.validate_trading_security)
        ]
        
        results = {}
        total_issues = []
        
        for check_name, validation_func in validation_functions:
            try:
                passed, issues = validation_func()
                results[check_name] = {
                    "passed": passed,
                    "issues": issues,
                    "status": "✅ PASS" if passed else "❌ FAIL"
                }
                
                self.logger.info(f"{results[check_name]['status']} {check_name}")
                
                if issues:
                    total_issues.extend(issues)
                    for issue in issues:
                        self.logger.error(f"  - {issue}")
                        
            except Exception as e:
                results[check_name] = {
                    "passed": False,
                    "issues": [f"Validation failed: {str(e)}"],
                    "status": "❌ ERROR"
                }
                total_issues.append(f"{check_name}: {str(e)}")
        
        # Overall assessment
        total_checks = len(validation_functions)
        passed_checks = sum(1 for r in results.values() if r["passed"])
        
        overall_passed = len(total_issues) == 0
        security_score = (passed_checks / total_checks) * 100
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "overall_status": "SECURE" if overall_passed else "INSECURE",
            "security_score": security_score,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "total_issues": len(total_issues),
            "total_warnings": len(self.warnings),
            "validation_time": duration,
            "timestamp": end_time.isoformat(),
            "details": results,
            "critical_issues": total_issues,
            "warnings": self.warnings
        }
        
        # Log summary
        self.logger.info(f"🔒 Security Validation Complete")
        self.logger.info(f"Security Score: {security_score:.1f}%")
        self.logger.info(f"Status: {summary['overall_status']}")
        self.logger.info(f"Issues: {len(total_issues)}, Warnings: {len(self.warnings)}")
        
        return summary
    
    def generate_security_report(self, results: Dict[str, Any]) -> str:
        """Generate detailed security report"""
        report_lines = [
            "=" * 60,
            "QUANTUM TRADING BOT - SECURITY VALIDATION REPORT",
            "=" * 60,
            f"Timestamp: {results['timestamp']}",
            f"Overall Status: {results['overall_status']}",
            f"Security Score: {results['security_score']:.1f}%",
            f"Validation Time: {results['validation_time']:.2f}s",
            "",
            "SUMMARY:",
            f"  Total Checks: {results['total_checks']}",
            f"  Passed: {results['passed_checks']}",
            f"  Failed: {results['failed_checks']}",
            f"  Issues: {results['total_issues']}",
            f"  Warnings: {results['total_warnings']}",
            "",
            "DETAILED RESULTS:",
            "-" * 40
        ]
        
        for check_name, details in results['details'].items():
            report_lines.append(f"\\n{check_name}: {details['status']}")
            if details['issues']:
                for issue in details['issues']:
                    report_lines.append(f"  - {issue}")
        
        if results['critical_issues']:
            report_lines.extend([
                "",
                "CRITICAL ISSUES:",
                "-" * 20
            ])
            for issue in results['critical_issues']:
                report_lines.append(f"❌ {issue}")
        
        if results['warnings']:
            report_lines.extend([
                "",
                "WARNINGS:",
                "-" * 20
            ])
            for warning in results['warnings']:
                report_lines.append(f"⚠️ {warning}")
        
        report_lines.extend([
            "",
            "RECOMMENDATIONS:",
            "-" * 20,
            "✅ Fix all critical security issues before mainnet deployment",
            "✅ Review and address warnings where applicable",
            "✅ Implement additional monitoring and alerting",
            "✅ Regular security audits and penetration testing",
            "✅ Keep dependencies updated and monitor for vulnerabilities",
            "=" * 60
        ])
        
        return "\\n".join(report_lines)

async def main():
    """Main security validation entry point"""
    validator = SecurityValidator()
    
    # Run comprehensive validation
    results = await validator.run_comprehensive_validation()
    
    # Generate and save report
    report = validator.generate_security_report(results)
    
    # Save report to file
    report_filename = f"security_validation_report_{int(datetime.utcnow().timestamp())}.txt"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"\\nSecurity validation report saved to: {report_filename}")
    
    # Return appropriate exit code
    if results['overall_status'] == 'INSECURE':
        print("\\n❌ SECURITY VALIDATION FAILED - Do not deploy to mainnet!")
        sys.exit(1)
    else:
        print("\\n✅ SECURITY VALIDATION PASSED - Ready for mainnet deployment")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())