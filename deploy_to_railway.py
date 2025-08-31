#!/usr/bin/env python3
"""
Railway Production Deployment Script
Automates the deployment of Quantum Trading Bot to Railway
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import requests

class RailwayDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deployment_config = {
            "app_name": "quantum-trading-bot",
            "region": "us-west1",
            "environment": "production"
        }
        
    def validate_environment(self):
        """Validate local environment and files before deployment"""
        print("[VALIDATION] Validating deployment environment...")
        
        required_files = [
            'main.py',
            'scalping_main.py',
            'requirements.txt',
            'railway.json',
            'Procfile',
            '.env.production'
        ]
        
        missing_files = []
        for file in required_files:
            if not (self.project_root / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"[ERROR] Missing required files: {', '.join(missing_files)}")
            return False
            
        # Validate Python syntax of main files
        for py_file in ['main.py', 'scalping_main.py']:
            if not self._validate_python_syntax(py_file):
                return False
                
        print("[SUCCESS] Environment validation passed")
        return True
        
    def _validate_python_syntax(self, filename):
        """Validate Python syntax of a file"""
        try:
            with open(self.project_root / filename, 'r') as f:
                compile(f.read(), filename, 'exec')
            return True
        except SyntaxError as e:
            print(f"[ERROR] Syntax error in {filename}: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Error validating {filename}: {e}")
            return False
            
    def check_railway_cli(self):
        """Check if Railway CLI is installed and authenticated"""
        print("[RAILWAY] Checking Railway CLI...")
        
        try:
            result = subprocess.run(['railway', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"[SUCCESS] Railway CLI found: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[ERROR] Railway CLI not found. Installing...")
            return self._install_railway_cli()
            
        # Check authentication
        try:
            result = subprocess.run(['railway', 'whoami'], 
                                  capture_output=True, text=True, check=True)
            print(f"[SUCCESS] Authenticated as: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError:
            print("[ERROR] Not authenticated with Railway")
            return self._authenticate_railway()
            
    def _install_railway_cli(self):
        """Install Railway CLI via npm"""
        try:
            subprocess.run(['npm', 'install', '-g', '@railway/cli'], check=True)
            print("[SUCCESS] Railway CLI installed successfully")
            return self._authenticate_railway()
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install Railway CLI: {e}")
            return False
            
    def _authenticate_railway(self):
        """Authenticate with Railway"""
        print("🔐 Please authenticate with Railway...")
        print("This will open your browser for login.")
        
        try:
            subprocess.run(['railway', 'login'], check=True)
            print("✅ Railway authentication successful")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Railway authentication failed: {e}")
            return False
            
    def create_railway_project(self):
        """Create or connect to Railway project"""
        print("📁 Setting up Railway project...")
        
        try:
            # Try to link existing project first
            result = subprocess.run(['railway', 'status'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Already connected to Railway project")
                return True
                
            # Create new project
            print("Creating new Railway project...")
            subprocess.run(['railway', 'init'], check=True)
            print("✅ Railway project created")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to setup Railway project: {e}")
            return False
            
    def set_environment_variables(self):
        """Set required environment variables in Railway"""
        print("🔧 Configuring environment variables...")
        
        env_vars = {
            # Core settings
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'PYTHONUNBUFFERED': '1',
            'PYTHONPATH': '.',
            'PORT': '8080',
            'HEALTH_CHECK_PORT': '8080',
            'TZ': 'UTC',
            
            # Trading configuration
            'RISK_PER_TRADE': '0.15',
            'DEFAULT_LEVERAGE': '8.5',
            'MAX_LEVERAGE': '10',
            'MIN_LEVERAGE': '8',
            'MAX_CONCURRENT_POSITIONS': '1',
            'STOP_LOSS_PERCENT': '0.012',
            'TAKE_PROFIT_RATIO': '1.5',
            'BINANCE_TESTNET': 'false',
            
            # Performance settings
            'SIGNAL_GENERATION_INTERVAL': '30',
            'MIN_SIGNAL_INTERVAL': '15',
            'ORDER_TIMEOUT': '5',
            'TARGET_TRADES_PER_DAY': '22'
        }
        
        # Set variables that don't require secrets
        for key, value in env_vars.items():
            try:
                subprocess.run(['railway', 'variables', 'set', f'{key}={value}'], 
                             check=True, capture_output=True)
                print(f"✅ Set {key}")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Warning: Failed to set {key}: {e}")
                
        # Prompt for sensitive variables
        sensitive_vars = ['BINANCE_API_KEY', 'BINANCE_SECRET_KEY']
        
        print("\\n🔐 REQUIRED: Please set these sensitive variables manually in Railway dashboard:")
        for var in sensitive_vars:
            print(f"   - {var}: (Your actual Binance API credentials)")
            
        print("\\n📱 OPTIONAL: For notifications (recommended):")
        print("   - TELEGRAM_BOT_TOKEN: (Your Telegram bot token)")
        print("   - TELEGRAM_CHAT_ID: (Your Telegram chat ID)")
        
        return True
        
    def deploy_to_railway(self):
        """Deploy the application to Railway"""
        print("🚀 Deploying to Railway...")
        
        try:
            # Deploy
            result = subprocess.run(['railway', 'up', '--detach'], 
                                  capture_output=True, text=True, check=True)
            print("✅ Deployment initiated")
            
            # Get deployment URL
            url_result = subprocess.run(['railway', 'status', '--json'], 
                                      capture_output=True, text=True)
            
            if url_result.returncode == 0:
                try:
                    status_data = json.loads(url_result.stdout)
                    if 'url' in status_data:
                        deployment_url = status_data['url']
                        print(f"🌐 Deployment URL: {deployment_url}")
                        self.deployment_config['url'] = deployment_url
                except json.JSONDecodeError:
                    pass
                    
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Deployment failed: {e}")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            return False
            
    def verify_deployment(self):
        """Verify deployment is working correctly"""
        print("🔍 Verifying deployment...")
        
        # Wait for deployment to be ready
        print("⏳ Waiting for deployment to be ready...")
        time.sleep(60)  # Give it time to start
        
        # Check health endpoint
        if 'url' in self.deployment_config:
            health_url = f"{self.deployment_config['url']}/health"
            
            for attempt in range(5):
                try:
                    response = requests.get(health_url, timeout=30)
                    if response.status_code == 200:
                        health_data = response.json()
                        print(f"✅ Health check passed: {health_data.get('status', 'unknown')}")
                        
                        # Check metrics endpoint
                        metrics_url = f"{self.deployment_config['url']}/metrics"
                        metrics_response = requests.get(metrics_url, timeout=30)
                        if metrics_response.status_code == 200:
                            print("✅ Metrics endpoint working")
                        
                        return True
                    else:
                        print(f"⚠️ Health check returned {response.status_code}")
                        
                except requests.RequestException as e:
                    print(f"⚠️ Attempt {attempt + 1}/5 failed: {e}")
                    
                if attempt < 4:
                    time.sleep(30)
                    
        # Alternative verification via Railway CLI
        try:
            result = subprocess.run(['railway', 'logs', '--tail', '10'], 
                                  capture_output=True, text=True, check=True)
            if "Trading bot started" in result.stdout or "Health server thread started" in result.stdout:
                print("✅ Bot appears to be running (found in logs)")
                return True
            else:
                print("⚠️ Bot may not be running properly (check logs)")
                
        except subprocess.CalledProcessError:
            pass
            
        return False
        
    def generate_deployment_summary(self):
        """Generate deployment summary and next steps"""
        print("\\n" + "="*60)
        print("[SUCCESS] QUANTUM TRADING BOT DEPLOYMENT COMPLETE")
        print("="*60)
        
        if 'url' in self.deployment_config:
            print(f"Application URL: {self.deployment_config['url']}")
            print(f"Health Check: {self.deployment_config['url']}/health")
            print(f"Metrics: {self.deployment_config['url']}/metrics")
        
        print("\\nNEXT STEPS:")
        print("1. Set your BINANCE_API_KEY and BINANCE_SECRET_KEY in Railway dashboard")
        print("2. Monitor logs: railway logs --follow")
        print("3. Check health endpoint to verify bot is running")
        print("4. Set up Telegram notifications (optional but recommended)")
        print("5. Monitor trading performance via metrics endpoint")
        
        print("\\n[WARNING] IMPORTANT REMINDERS:")
        print("- Verify BINANCE_TESTNET=false for real trading")
        print("- Ensure sufficient USDT balance in your Binance account")
        print("- Bot will trade with 8.5x leverage - understand the risks")
        print("- Monitor the bot closely, especially in the first few hours")
        
        print("\\n[EMERGENCY] EMERGENCY COMMANDS:")
        print("- Stop bot: railway service delete")
        print("- View logs: railway logs --follow")
        print("- Update env vars: railway variables")
        
        return True
        
    def run_deployment(self):
        """Run the complete deployment process"""
        print("Starting Quantum Trading Bot deployment to Railway...")
        print(f"Deployment started at: {datetime.now()}")
        
        steps = [
            ("Validate Environment", self.validate_environment),
            ("Check Railway CLI", self.check_railway_cli),
            ("Setup Railway Project", self.create_railway_project),
            ("Configure Environment Variables", self.set_environment_variables),
            ("Deploy to Railway", self.deploy_to_railway),
            ("Verify Deployment", self.verify_deployment),
            ("Generate Summary", self.generate_deployment_summary)
        ]
        
        for step_name, step_func in steps:
            print(f"\\n[STEP] {step_name}")
            if not step_func():
                print(f"[ERROR] Deployment failed at step: {step_name}")
                return False
                
        print("\\n[SUCCESS] Deployment completed successfully!")
        return True

def main():
    """Main deployment function"""
    deployer = RailwayDeployer()
    
    try:
        success = deployer.run_deployment()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\\n[CANCELLED] Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error during deployment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()