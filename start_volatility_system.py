#!/usr/bin/env python3
"""
VOLATILITY SYSTEM LAUNCHER
Easy-to-use launcher for the Advanced Volatility Trading System
with interactive setup and configuration.
"""

import os
import sys
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import argparse

def print_banner():
    """Print system banner"""
    print("🌊" + "=" * 78)
    print("  🚀 ADVANCED VOLATILITY SCREENING & DETECTION SYSTEM")
    print("=" * 80)
    print("  📊 Real-time monitoring of 50+ cryptocurrency pairs")
    print("  ⚡ Dynamic volatility breakout detection")
    print("  🔔 Multi-channel alert system")
    print("  📡 Comprehensive REST API & WebSocket")
    print("  🤖 Seamless trading system integration")
    print("=" * 80)

def check_environment():
    """Check if required environment variables are set"""
    required_vars = {
        'BINANCE_API_KEY': 'Binance API Key',
        'BINANCE_SECRET_KEY': 'Binance Secret Key'
    }
    
    optional_vars = {
        'TELEGRAM_BOT_TOKEN': 'Telegram Bot Token (for alerts)',
        'TELEGRAM_CHAT_ID': 'Telegram Chat ID (for alerts)',
        'DISCORD_WEBHOOK_URL': 'Discord Webhook URL (for alerts)',
        'EMAIL_USERNAME': 'Email Username (for alerts)',
        'EMAIL_PASSWORD': 'Email Password (for alerts)',
        'EMAIL_RECIPIENT': 'Email Recipient (for alerts)'
    }
    
    print("\n🔧 Environment Check:")
    print("-" * 40)
    
    missing_required = []
    for var, desc in required_vars.items():
        if os.getenv(var):
            if var == 'BINANCE_API_KEY':
                masked = f"{os.getenv(var)[:8]}...{os.getenv(var)[-8:]}"
                print(f"  ✅ {desc}: {masked}")
            else:
                print(f"  ✅ {desc}: Set")
        else:
            print(f"  ❌ {desc}: Missing")
            missing_required.append(var)
    
    print(f"\n📞 Optional Alert Channels:")
    for var, desc in optional_vars.items():
        if os.getenv(var):
            print(f"  ✅ {desc}: Configured")
        else:
            print(f"  ⚪ {desc}: Not configured")
    
    return len(missing_required) == 0

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing Dependencies:")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements_advanced_volatility.txt'
        ], check=True, capture_output=True, text=True)
        
        print("  ✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to install dependencies: {e}")
        print(f"  Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("  ❌ Requirements file not found: requirements_advanced_volatility.txt")
        return False

def create_env_file():
    """Interactive creation of .env file"""
    print("\n⚙️ Environment Setup:")
    print("-" * 40)
    
    env_path = Path('.env')
    if env_path.exists():
        overwrite = input("  .env file exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            return True
    
    print("  Please provide your Binance API credentials:")
    api_key = input("  Binance API Key: ").strip()
    if not api_key:
        print("  ❌ API Key is required")
        return False
    
    secret_key = input("  Binance Secret Key: ").strip()
    if not secret_key:
        print("  ❌ Secret Key is required")
        return False
    
    trading_mode = input("  Trading Mode (testnet/mainnet) [testnet]: ").strip() or "testnet"
    
    # Optional configurations
    print("\n  📞 Alert Configuration (Optional - press Enter to skip):")
    telegram_token = input("  Telegram Bot Token: ").strip()
    telegram_chat_id = input("  Telegram Chat ID: ").strip()
    discord_webhook = input("  Discord Webhook URL: ").strip()
    
    # Create .env content
    env_content = f"""# Binance API Configuration
BINANCE_API_KEY={api_key}
BINANCE_SECRET_KEY={secret_key}

# Trading Mode
TRADING_MODE={trading_mode}
"""
    
    if telegram_token and telegram_chat_id:
        env_content += f"""
# Telegram Alerts
TELEGRAM_BOT_TOKEN={telegram_token}
TELEGRAM_CHAT_ID={telegram_chat_id}
"""
    
    if discord_webhook:
        env_content += f"""
# Discord Alerts
DISCORD_WEBHOOK_URL={discord_webhook}
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("  ✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"  ❌ Failed to create .env file: {e}")
        return False

def get_launch_options():
    """Get launch configuration from user"""
    print("\n🚀 Launch Configuration:")
    print("-" * 40)
    
    options = {}
    
    # Trading mode
    mode_input = input("  Trading Mode (testnet/mainnet) [testnet]: ").strip()
    options['mode'] = mode_input if mode_input in ['testnet', 'mainnet'] else 'testnet'
    
    # Features
    print("\n  📊 Features (y/n):")
    options['enable_dynamic_pairs'] = input("    Enable dynamic pair discovery [y]: ").lower() != 'n'
    options['enable_alerts'] = input("    Enable alert system [y]: ").lower() != 'n'
    options['enable_signals'] = input("    Enable trading signals [y]: ").lower() != 'n'
    options['enable_api'] = input("    Enable API server [y]: ").lower() != 'n'
    
    # Parameters
    print("\n  ⚙️ Parameters:")
    try:
        min_score = input("    Minimum opportunity score [60]: ").strip()
        options['min_opportunity_score'] = float(min_score) if min_score else 60.0
    except ValueError:
        options['min_opportunity_score'] = 60.0
    
    try:
        max_pairs = input("    Maximum active pairs [15]: ").strip()
        options['max_active_pairs'] = int(max_pairs) if max_pairs else 15
    except ValueError:
        options['max_active_pairs'] = 15
    
    # API settings
    if options['enable_api']:
        api_port = input("    API server port [8000]: ").strip()
        options['api_port'] = int(api_port) if api_port.isdigit() else 8000
    
    # Log level
    log_level = input("    Log level (DEBUG/INFO/WARNING/ERROR) [INFO]: ").strip().upper()
    options['log_level'] = log_level if log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR'] else 'INFO'
    
    return options

def build_command(options: Dict) -> List[str]:
    """Build command line from options"""
    cmd = [sys.executable, 'volatility_main.py']
    
    # Mode
    cmd.extend(['--mode', options['mode']])
    
    # Features
    if not options.get('enable_dynamic_pairs', True):
        cmd.append('--disable-dynamic-pairs')
    if not options.get('enable_alerts', True):
        cmd.append('--disable-alerts')
    if not options.get('enable_signals', True):
        cmd.append('--disable-signals')
    if not options.get('enable_api', True):
        cmd.append('--disable-api')
    
    # Parameters
    if 'min_opportunity_score' in options:
        cmd.extend(['--min-opportunity-score', str(options['min_opportunity_score'])])
    if 'max_active_pairs' in options:
        cmd.extend(['--max-active-pairs', str(options['max_active_pairs'])])
    if 'api_port' in options:
        cmd.extend(['--api-port', str(options['api_port'])])
    
    # Log level
    cmd.extend(['--log-level', options.get('log_level', 'INFO')])
    
    return cmd

def save_launch_config(options: Dict):
    """Save launch configuration for future use"""
    config_path = Path('volatility_config.json')
    
    try:
        with open(config_path, 'w') as f:
            json.dump(options, f, indent=2)
        print(f"  ✅ Configuration saved to {config_path}")
    except Exception as e:
        print(f"  ⚠️  Could not save configuration: {e}")

def load_launch_config() -> Optional[Dict]:
    """Load saved launch configuration"""
    config_path = Path('volatility_config.json')
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠️  Could not load saved configuration: {e}")
        return None

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(description="Advanced Volatility System Launcher")
    parser.add_argument('--quick', action='store_true', help='Quick launch with defaults')
    parser.add_argument('--install-deps', action='store_true', help='Install dependencies only')
    parser.add_argument('--setup-env', action='store_true', help='Setup environment only')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Install dependencies only
    if args.install_deps:
        success = install_dependencies()
        sys.exit(0 if success else 1)
    
    # Setup environment only
    if args.setup_env:
        success = create_env_file()
        sys.exit(0 if success else 1)
    
    # Check if dependencies are installed
    try:
        import fastapi
        import ccxt
        import pandas
        print("  ✅ Core dependencies found")
    except ImportError as e:
        print(f"  ❌ Missing dependencies: {e}")
        install = input("  Install dependencies now? (y/n): ").lower()
        if install == 'y':
            if not install_dependencies():
                sys.exit(1)
        else:
            print("  Please install dependencies manually:")
            print("  pip install -r requirements_advanced_volatility.txt")
            sys.exit(1)
    
    # Check environment
    if not check_environment():
        setup = input("\n  Setup environment file now? (y/n): ").lower()
        if setup == 'y':
            if not create_env_file():
                sys.exit(1)
        else:
            print("  Please set required environment variables manually")
            sys.exit(1)
    
    # Get launch options
    if args.quick:
        print("\n🚀 Quick Launch Mode - Using defaults")
        options = {
            'mode': 'testnet',
            'enable_dynamic_pairs': True,
            'enable_alerts': True,
            'enable_signals': True,
            'enable_api': True,
            'min_opportunity_score': 60.0,
            'max_active_pairs': 15,
            'api_port': 8000,
            'log_level': 'INFO'
        }
    else:
        # Try to load saved config
        saved_config = load_launch_config()
        if saved_config:
            use_saved = input(f"\n  Use saved configuration? (y/n): ").lower()
            if use_saved == 'y':
                options = saved_config
            else:
                options = get_launch_options()
        else:
            options = get_launch_options()
        
        # Save configuration
        save_launch_config(options)
    
    # Build and display command
    cmd = build_command(options)
    
    print(f"\n🎯 Launch Summary:")
    print("-" * 40)
    print(f"  Mode: {options['mode'].upper()}")
    print(f"  Dynamic Pairs: {'✅' if options.get('enable_dynamic_pairs') else '❌'}")
    print(f"  Alerts: {'✅' if options.get('enable_alerts') else '❌'}")
    print(f"  Trading Signals: {'✅' if options.get('enable_signals') else '❌'}")
    print(f"  API Server: {'✅' if options.get('enable_api') else '❌'}")
    if options.get('enable_api'):
        print(f"  API Port: {options.get('api_port', 8000)}")
    print(f"  Min Opportunity Score: {options.get('min_opportunity_score', 60)}")
    print(f"  Max Active Pairs: {options.get('max_active_pairs', 15)}")
    print(f"  Log Level: {options.get('log_level', 'INFO')}")
    
    # Mainnet warning
    if options['mode'] == 'mainnet':
        print("\n🚨 WARNING: MAINNET MODE - REAL MONEY TRADING")
        print("  This will trade with real funds on your account!")
        confirm = input("  Are you absolutely sure? (type 'YES' to continue): ")
        if confirm != 'YES':
            print("  Launch aborted")
            sys.exit(0)
    
    # Final confirmation
    print(f"\n🚀 Ready to launch!")
    if not args.quick:
        launch = input("  Start the system now? (y/n): ").lower()
        if launch != 'y':
            print("  Launch cancelled")
            sys.exit(0)
    
    # Launch system
    print("\n" + "=" * 80)
    print("🚀 LAUNCHING ADVANCED VOLATILITY TRADING SYSTEM...")
    print("=" * 80)
    print(f"Command: {' '.join(cmd)}")
    print("=" * 80)
    
    try:
        # Change to script directory
        os.chdir(Path(__file__).parent)
        
        # Launch with real-time output
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 universal_newlines=True, bufsize=1)
        
        # Stream output in real-time
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 System interrupted by user")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"\n❌ Launch failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()