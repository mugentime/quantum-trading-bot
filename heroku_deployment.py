#!/usr/bin/env python3
"""
Emergency Heroku Deployment for AXSUSDT Ultra-High Frequency Trading Bot
Recovery Token: c45618c0-7e36-4600-b4c1-eb8918326179
"""

import os
import sys
import subprocess
import json
from datetime import datetime

class HerokuEmergencyDeployer:
    def __init__(self):
        self.app_name = f"quantum-trading-bot-{int(datetime.now().timestamp())}"
        self.recovery_token = "c45618c0-7e36-4600-b4c1-eb8918326179"
        
    def check_heroku_cli(self):
        """Check if Heroku CLI is available"""
        try:
            result = subprocess.run(['heroku', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"[SUCCESS] Heroku CLI found: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[ERROR] Heroku CLI not found. Please install: https://devcenter.heroku.com/articles/heroku-cli")
            return False
            
    def heroku_login(self):
        """Login to Heroku"""
        try:
            result = subprocess.run(['heroku', 'auth:whoami'], 
                                  capture_output=True, text=True, check=True)
            print(f"[SUCCESS] Already logged in as: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError:
            print("[AUTH] Please login to Heroku")
            try:
                subprocess.run(['heroku', 'auth:login'], check=True)
                return True
            except subprocess.CalledProcessError:
                print("[ERROR] Heroku login failed")
                return False
                
    def create_heroku_app(self):
        """Create Heroku application"""
        print(f"[HEROKU] Creating app: {self.app_name}")
        try:
            subprocess.run(['heroku', 'create', self.app_name, '--region', 'us'], 
                         check=True)
            print(f"[SUCCESS] Heroku app created: {self.app_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to create Heroku app: {e}")
            return False
            
    def set_heroku_config(self):
        """Set environment variables for AXSUSDT trading"""
        print("[CONFIG] Setting Heroku environment variables...")
        
        config_vars = {
            'ENVIRONMENT': 'production',
            'BINANCE_TESTNET': 'false',
            'PYTHONUNBUFFERED': '1',
            'PYTHONPATH': '.',
            'PORT': '8080',
            'TZ': 'UTC',
            
            # AXSUSDT Ultra-High Frequency Configuration
            'RISK_PER_TRADE': '0.15',
            'DEFAULT_LEVERAGE': '8.5',
            'MAX_LEVERAGE': '10',
            'MIN_LEVERAGE': '8',
            'MAX_CONCURRENT_POSITIONS': '1',
            'STOP_LOSS_PERCENT': '0.012',
            'TAKE_PROFIT_RATIO': '1.5',
            
            # High-frequency optimization
            'SIGNAL_GENERATION_INTERVAL': '30',
            'MIN_SIGNAL_INTERVAL': '15',
            'ORDER_TIMEOUT': '5',
            'TARGET_TRADES_PER_DAY': '22'
        }
        
        for key, value in config_vars.items():
            try:
                subprocess.run(['heroku', 'config:set', f'{key}={value}', 
                              '--app', self.app_name], check=True, capture_output=True)
                print(f"[SUCCESS] Set {key}")
            except subprocess.CalledProcessError as e:
                print(f"[WARNING] Failed to set {key}: {e}")
        
        print("[MANUAL] CRITICAL: Set these manually in Heroku dashboard:")
        print(f"  heroku config:set BINANCE_API_KEY=YOUR_KEY --app {self.app_name}")
        print(f"  heroku config:set BINANCE_SECRET_KEY=YOUR_SECRET --app {self.app_name}")
        
        return True
        
    def create_heroku_procfile(self):
        """Create Procfile for Heroku"""
        procfile_content = "web: python -u main.py"
        
        with open('Procfile', 'w') as f:
            f.write(procfile_content)
            
        print("[SUCCESS] Procfile created for Heroku")
        return True
        
    def deploy_to_heroku(self):
        """Deploy to Heroku"""
        print("[DEPLOY] Deploying to Heroku...")
        
        try:
            # Add files to git
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 
                          f'Emergency Heroku deployment - Recovery: {self.recovery_token}'], 
                         check=True)
            
            # Add Heroku remote
            subprocess.run(['heroku', 'git:remote', '-a', self.app_name], check=True)
            
            # Push to Heroku
            result = subprocess.run(['git', 'push', 'heroku', 'main'], 
                                  capture_output=True, text=True, check=True)
            print("[SUCCESS] Deployed to Heroku")
            
            # Scale dyno
            subprocess.run(['heroku', 'ps:scale', 'web=1', '--app', self.app_name], 
                         check=True)
            print("[SUCCESS] Dyno scaled")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Heroku deployment failed: {e}")
            if hasattr(e, 'stdout') and e.stdout:
                print(f"STDOUT: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"STDERR: {e.stderr}")
            return False
            
    def get_app_url(self):
        """Get Heroku app URL"""
        try:
            result = subprocess.run(['heroku', 'apps:info', '--app', self.app_name, '--json'], 
                                  capture_output=True, text=True, check=True)
            app_info = json.loads(result.stdout)
            app_url = app_info.get('web_url', f'https://{self.app_name}.herokuapp.com/')
            return app_url
        except:
            return f'https://{self.app_name}.herokuapp.com/'
            
    def verify_deployment(self):
        """Verify Heroku deployment"""
        print("[VERIFY] Checking deployment status...")
        
        try:
            # Check dyno status
            result = subprocess.run(['heroku', 'ps', '--app', self.app_name], 
                                  capture_output=True, text=True, check=True)
            print(f"[STATUS] Dynos: {result.stdout}")
            
            # Get logs
            result = subprocess.run(['heroku', 'logs', '--tail', '20', '--app', self.app_name], 
                                  capture_output=True, text=True, check=True)
            
            if "Trading bot started" in result.stdout or "Health server thread started" in result.stdout:
                print("[SUCCESS] Bot appears to be running")
                return True
            else:
                print("[WARNING] Bot may not be running properly")
                print(f"Recent logs: {result.stdout}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Verification failed: {e}")
            return False
            
    def emergency_deploy(self):
        """Execute emergency deployment"""
        print("=" * 60)
        print(f"EMERGENCY HEROKU DEPLOYMENT - AXSUSDT Bot")
        print(f"Recovery Token: {self.recovery_token}")
        print("=" * 60)
        
        steps = [
            ("Check Heroku CLI", self.check_heroku_cli),
            ("Heroku Login", self.heroku_login),
            ("Create Heroku App", self.create_heroku_app),
            ("Set Configuration", self.set_heroku_config),
            ("Create Procfile", self.create_heroku_procfile),
            ("Deploy to Heroku", self.deploy_to_heroku),
            ("Verify Deployment", self.verify_deployment)
        ]
        
        for step_name, step_func in steps:
            print(f"\\n[STEP] {step_name}")
            if not step_func():
                print(f"[ERROR] Failed at step: {step_name}")
                return False
                
        # Success summary
        app_url = self.get_app_url()
        print("\\n" + "=" * 60)
        print("[SUCCESS] HEROKU DEPLOYMENT COMPLETE")
        print("=" * 60)
        print(f"App Name: {self.app_name}")
        print(f"App URL: {app_url}")
        print(f"Health Check: {app_url}health")
        print(f"Metrics: {app_url}metrics")
        print("\\n[NEXT STEPS]:")
        print(f"1. Set API keys: heroku config:set BINANCE_API_KEY=YOUR_KEY --app {self.app_name}")
        print(f"2. Monitor: heroku logs --tail --app {self.app_name}")
        print(f"3. Check health: curl {app_url}health")
        
        return True

if __name__ == "__main__":
    deployer = HerokuEmergencyDeployer()
    success = deployer.emergency_deploy()
    sys.exit(0 if success else 1)