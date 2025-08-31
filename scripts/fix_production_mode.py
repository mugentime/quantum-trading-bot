#!/usr/bin/env python3
"""
Script to fix production mode and enable real trading
THIS WILL ENABLE REAL MONEY TRADING - USE WITH CAUTION
"""

import os
import sys
from pathlib import Path

def fix_production_mode():
    """Fix testnet mode and enable production trading"""
    
    print("="*80)
    print("FIXING PRODUCTION MODE - ENABLING REAL TRADING")
    print("WARNING: This will enable REAL MONEY trading!")
    print("="*80)
    
    # Find .env file
    env_path = Path(__file__).parent.parent / '.env'
    
    if not env_path.exists():
        print(f"[X] .env file not found at {env_path}")
        print("\nCreate .env file with:")
        print("""
# Binance API (PRODUCTION - REAL MONEY)
BINANCE_API_KEY=your_production_api_key_here
BINANCE_SECRET_KEY=your_production_secret_key_here
BINANCE_TESTNET=false  # CRITICAL: Set to false for real trading

# Environment
ENVIRONMENT=production
DEBUG=false

# Telegram (optional but recommended)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Risk Settings (conservative for production)
RISK_PER_TRADE=0.02  # Start with 2% risk per trade
MAX_CONCURRENT_POSITIONS=3  # Limit positions initially
DEFAULT_LEVERAGE=5  # Lower leverage for safety
        """)
        return
    
    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Fix critical settings
    updated_lines = []
    settings_found = {
        'BINANCE_TESTNET': False,
        'ENVIRONMENT': False,
        'DEBUG': False
    }
    
    for line in lines:
        if line.strip().startswith('BINANCE_TESTNET'):
            updated_lines.append('BINANCE_TESTNET=false  # PRODUCTION MODE - REAL MONEY\n')
            settings_found['BINANCE_TESTNET'] = True
            print("[OK] Changed BINANCE_TESTNET to false")
        elif line.strip().startswith('ENVIRONMENT'):
            updated_lines.append('ENVIRONMENT=production\n')
            settings_found['ENVIRONMENT'] = True
            print("[OK] Changed ENVIRONMENT to production")
        elif line.strip().startswith('DEBUG'):
            updated_lines.append('DEBUG=false\n')
            settings_found['DEBUG'] = True
            print("[OK] Changed DEBUG to false")
        else:
            updated_lines.append(line)
    
    # Add missing settings
    if not settings_found['BINANCE_TESTNET']:
        updated_lines.append('\n# CRITICAL SETTING\n')
        updated_lines.append('BINANCE_TESTNET=false  # PRODUCTION MODE - REAL MONEY\n')
        print("[OK] Added BINANCE_TESTNET=false")
    
    if not settings_found['ENVIRONMENT']:
        updated_lines.append('ENVIRONMENT=production\n')
        print("[OK] Added ENVIRONMENT=production")
    
    if not settings_found['DEBUG']:
        updated_lines.append('DEBUG=false\n')
        print("[OK] Added DEBUG=false")
    
    # Backup original .env
    backup_path = env_path.with_suffix('.env.backup')
    with open(backup_path, 'w') as f:
        f.writelines(lines)
    print(f"\n[OK] Original .env backed up to {backup_path}")
    
    # Write updated .env
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)
    print(f"[OK] Updated .env file at {env_path}")
    
    print("\n" + "="*80)
    print("PRODUCTION MODE ENABLED")
    print("="*80)
    print("\nNEXT STEPS:")
    print("1. Ensure you have PRODUCTION API keys (not testnet keys)")
    print("2. Enable trading permissions on Binance:")
    print("   - Log into Binance")
    print("   - Go to API Management")
    print("   - Enable 'Enable Trading' permission")
    print("   - Add Railway's IP to whitelist (if using IP restrictions)")
    print("3. Verify you have USDT balance in your account")
    print("4. Redeploy to Railway with: railway up")
    print("\nWARNING: The bot will now trade with REAL MONEY!")
    print("Start with small amounts to test first!")

if __name__ == "__main__":
    response = input("\nAre you sure you want to enable PRODUCTION trading? (yes/no): ")
    if response.lower() == 'yes':
        fix_production_mode()
    else:
        print("Aborted. Staying in testnet mode.")