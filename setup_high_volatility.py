#!/usr/bin/env python3
"""
HIGH VOLATILITY STRATEGY SETUP SCRIPT
Automated setup and configuration for the high volatility pairs trading strategy
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HighVolatilitySetup:
    """Setup manager for high volatility trading strategy"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.required_dirs = [
            'strategies',
            'config', 
            'backtesting',
            'monitoring',
            'backtest_results',
            'monitoring_logs',
            'monitoring_reports',
            'logs'
        ]
        
        self.required_files = [
            'strategies/high_volatility_strategy.py',
            'config/volatility_config.py',
            'backtesting/volatility_backtester.py',
            'monitoring/volatility_monitor.py',
            'main_high_volatility_bot.py',
            'requirements_volatility.txt'
        ]
        
        self.env_template = {
            'BINANCE_API_KEY': 'your_binance_api_key_here',
            'BINANCE_SECRET_KEY': 'your_binance_secret_key_here', 
            'BINANCE_TESTNET': 'true',
            'TELEGRAM_BOT_TOKEN': 'your_telegram_bot_token_here',
            'TELEGRAM_CHAT_ID': 'your_telegram_chat_id_here',
            'MONITOR_WEBHOOK_URL': 'https://your-webhook-url.com/alerts'
        }
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            logger.error(f"Python 3.8+ required, found {version.major}.{version.minor}")
            return False
        
        logger.info(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def create_directories(self):
        """Create required directory structure"""
        logger.info("📁 Creating directory structure...")
        
        for directory in self.required_dirs:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            logger.info(f"  Created: {directory}/")
        
        # Create __init__.py files for Python modules
        module_dirs = ['strategies', 'config', 'backtesting', 'monitoring']
        for module_dir in module_dirs:
            init_file = self.project_root / module_dir / '__init__.py'
            if not init_file.exists():
                init_file.touch()
    
    def check_required_files(self) -> bool:
        """Check if all required files exist"""
        logger.info("📄 Checking required files...")
        
        missing_files = []
        for file_path in self.required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error("❌ Missing required files:")
            for file_path in missing_files:
                logger.error(f"  - {file_path}")
            return False
        
        logger.info("✅ All required files present")
        return True
    
    def setup_environment_file(self):
        """Create .env file with template values"""
        env_file = self.project_root / '.env'
        
        if env_file.exists():
            logger.info("📝 .env file already exists, skipping...")
            return
        
        logger.info("📝 Creating .env template...")
        
        with open(env_file, 'w') as f:
            f.write("# High Volatility Trading Bot Environment Variables\n")
            f.write(f"# Created: {datetime.now().isoformat()}\n\n")
            
            f.write("# Binance API Configuration\n")
            f.write(f"BINANCE_API_KEY={self.env_template['BINANCE_API_KEY']}\n")
            f.write(f"BINANCE_SECRET_KEY={self.env_template['BINANCE_SECRET_KEY']}\n")
            f.write(f"BINANCE_TESTNET={self.env_template['BINANCE_TESTNET']}\n\n")
            
            f.write("# Telegram Alerts Configuration\n")
            f.write(f"TELEGRAM_BOT_TOKEN={self.env_template['TELEGRAM_BOT_TOKEN']}\n")
            f.write(f"TELEGRAM_CHAT_ID={self.env_template['TELEGRAM_CHAT_ID']}\n\n")
            
            f.write("# Monitoring Configuration\n")
            f.write(f"MONITOR_WEBHOOK_URL={self.env_template['MONITOR_WEBHOOK_URL']}\n\n")
            
            f.write("# Optional: Additional Exchange APIs\n")
            f.write("# OKX_API_KEY=your_okx_api_key\n")
            f.write("# OKX_SECRET_KEY=your_okx_secret_key\n")
            f.write("# BYBIT_API_KEY=your_bybit_api_key\n")
            f.write("# BYBIT_SECRET_KEY=your_bybit_secret_key\n")
        
        logger.info("✅ .env template created - please update with your API keys")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        logger.info("📦 Installing Python dependencies...")
        
        requirements_file = self.project_root / 'requirements_volatility.txt'
        if not requirements_file.exists():
            logger.error("❌ requirements_volatility.txt not found")
            return False
        
        try:
            # Upgrade pip first
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
            
            # Install requirements
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)])
            
            logger.info("✅ Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    def check_dependencies(self) -> bool:
        """Check if critical dependencies are available"""
        logger.info("🔍 Checking critical dependencies...")
        
        critical_modules = [
            'ccxt',
            'pandas', 
            'numpy',
            'scipy',
            'aiohttp',
            'websockets',
            'python_telegram_bot',
            'psutil'
        ]
        
        missing_modules = []
        for module in critical_modules:
            try:
                __import__(module.replace('_', '-'))
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            logger.error("❌ Missing critical modules:")
            for module in missing_modules:
                logger.error(f"  - {module}")
            logger.info("Run: pip install -r requirements_volatility.txt")
            return False
        
        logger.info("✅ All critical dependencies available")
        return True
    
    def create_sample_configs(self):
        """Create sample configuration files"""
        logger.info("⚙️ Creating sample configuration files...")
        
        # Create sample high volatility config
        config_dir = self.project_root / 'config'
        sample_config_file = config_dir / 'sample_high_volatility_config.json'
        
        sample_config = {
            "trading_mode": "testnet",
            "exchange": "binance",
            "scan_interval": 30,
            "max_concurrent_positions": 5,
            "volatility_thresholds": {
                "hourly_min": 0.05,
                "daily_min": 0.15,
                "high_volatility_percentile": 95.0,
                "extreme_volatility_percentile": 99.0
            },
            "risk_management": {
                "max_risk_per_trade": 0.02,
                "max_portfolio_risk": 0.08,
                "max_position_size": 0.05,
                "max_daily_loss": 0.03,
                "max_leverage": 10
            },
            "pair_configs": {
                "BTC/USDT": {
                    "min_volatility_threshold": 0.04,
                    "max_position_size_pct": 0.06,
                    "base_leverage": 5,
                    "max_leverage": 8,
                    "priority": 1
                },
                "ETH/USDT": {
                    "min_volatility_threshold": 0.05,
                    "max_position_size_pct": 0.05,
                    "base_leverage": 6,
                    "max_leverage": 10,
                    "priority": 1
                }
            }
        }
        
        with open(sample_config_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        logger.info(f"✅ Sample config created: {sample_config_file}")
    
    def create_startup_scripts(self):
        """Create startup scripts for different platforms"""
        logger.info("🚀 Creating startup scripts...")
        
        # Windows batch script
        windows_script = self.project_root / 'start_high_volatility_bot.bat'
        with open(windows_script, 'w') as f:
            f.write('@echo off\n')
            f.write('echo Starting High Volatility Trading Bot...\n')
            f.write('echo.\n')
            f.write('python main_high_volatility_bot.py --mode testnet\n')
            f.write('pause\n')
        
        # Linux/Mac shell script
        unix_script = self.project_root / 'start_high_volatility_bot.sh'
        with open(unix_script, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('echo "Starting High Volatility Trading Bot..."\n')
            f.write('echo\n')
            f.write('python3 main_high_volatility_bot.py --mode testnet\n')
        
        # Make shell script executable
        if unix_script.exists():
            os.chmod(unix_script, 0o755)
        
        # Backtest script
        backtest_script = self.project_root / 'run_backtest.py'
        with open(backtest_script, 'w') as f:
            f.write('#!/usr/bin/env python3\n')
            f.write('"""Quick backtest runner"""\n\n')
            f.write('import asyncio\n')
            f.write('from main_high_volatility_bot import main\n\n')
            f.write('if __name__ == "__main__":\n')
            f.write('    import sys\n')
            f.write('    sys.argv = ["run_backtest.py", "--backtest-only", "--backtest-days", "30"]\n')
            f.write('    asyncio.run(main())\n')
        
        logger.info("✅ Startup scripts created")
    
    def verify_setup(self) -> bool:
        """Verify the complete setup"""
        logger.info("🔍 Verifying setup...")
        
        verification_steps = [
            ("Python version", self.check_python_version),
            ("Required files", self.check_required_files),
            ("Dependencies", self.check_dependencies)
        ]
        
        all_passed = True
        for step_name, check_func in verification_steps:
            try:
                if not check_func():
                    logger.error(f"❌ {step_name} check failed")
                    all_passed = False
                else:
                    logger.info(f"✅ {step_name} check passed")
            except Exception as e:
                logger.error(f"❌ {step_name} check error: {e}")
                all_passed = False
        
        return all_passed
    
    def print_next_steps(self):
        """Print next steps for user"""
        logger.info("\n" + "=" * 60)
        logger.info("🎉 HIGH VOLATILITY STRATEGY SETUP COMPLETED!")
        logger.info("=" * 60)
        logger.info("\n📋 NEXT STEPS:")
        logger.info("1. 📝 Update .env file with your API credentials:")
        logger.info("   - Get Binance API key from: https://www.binance.com/en/my/settings/api-management")
        logger.info("   - (Optional) Create Telegram bot: https://core.telegram.org/bots#creating-a-new-bot")
        logger.info("")
        logger.info("2. 🧪 Test the setup:")
        logger.info("   python main_high_volatility_bot.py --backtest-only")
        logger.info("")
        logger.info("3. 🚀 Start paper trading:")
        logger.info("   python main_high_volatility_bot.py --mode testnet")
        logger.info("")
        logger.info("4. 💰 When ready for live trading:")
        logger.info("   python main_high_volatility_bot.py --mode mainnet")
        logger.info("")
        logger.info("📚 DOCUMENTATION:")
        logger.info("- Strategy config: config/volatility_config.py")
        logger.info("- Sample config: config/sample_high_volatility_config.json")
        logger.info("- Logs: monitoring_logs/")
        logger.info("- Reports: monitoring_reports/")
        logger.info("")
        logger.info("⚠️  IMPORTANT:")
        logger.info("- Start with testnet mode for testing")
        logger.info("- Review backtest results before live trading")
        logger.info("- Monitor risk metrics continuously")
        logger.info("- Never risk more than you can afford to lose")
        logger.info("")
        logger.info("🎯 TARGET PERFORMANCE:")
        logger.info("- Volatility pairs: >5% hourly, >15% daily")
        logger.info("- Risk per trade: 1-2% with dynamic stops")
        logger.info("- Leverage: 3-10x based on volatility")
        logger.info("- Win rate target: >60%")
        logger.info("=" * 60)
    
    def run_setup(self):
        """Run complete setup process"""
        logger.info("🌊 HIGH VOLATILITY STRATEGY SETUP")
        logger.info("=" * 50)
        
        try:
            # Create directory structure
            self.create_directories()
            
            # Setup environment file
            self.setup_environment_file()
            
            # Install dependencies (optional - user can do manually)
            install_deps = input("\n📦 Install Python dependencies now? (y/n): ").lower().strip()
            if install_deps == 'y':
                self.install_dependencies()
            else:
                logger.info("ℹ️  To install dependencies later, run:")
                logger.info("   pip install -r requirements_volatility.txt")
            
            # Create sample configurations
            self.create_sample_configs()
            
            # Create startup scripts
            self.create_startup_scripts()
            
            # Verify setup
            if self.verify_setup():
                logger.info("✅ Setup verification passed")
            else:
                logger.warning("⚠️  Some verification checks failed")
            
            # Print next steps
            self.print_next_steps()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Setup interrupted by user")
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            logger.error("Please check the error and try again")

def main():
    """Main setup execution"""
    setup = HighVolatilitySetup()
    setup.run_setup()

if __name__ == "__main__":
    main()