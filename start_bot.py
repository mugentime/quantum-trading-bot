#!/usr/bin/env python3
"""
Simple bot starter with proper environment loading
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify API keys are loaded
api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')
testnet = os.getenv('BINANCE_TESTNET', 'true')

print("="*50)
print("QUANTUM TRADING BOT - STARTING")
print("="*50)

if api_key and secret_key:
    print(f"[OK] API Key loaded: {api_key[:10]}...")
    print(f"[OK] Secret Key loaded: {secret_key[:10]}...")
    print(f"[OK] Testnet mode: {testnet}")
else:
    print("[ERROR] API keys not found in environment")
    sys.exit(1)

print("\nStarting bot...")

# Try to import and run the clean live testnet bot
try:
    # Set environment variables explicitly
    os.environ['BINANCE_API_KEY'] = api_key
    os.environ['BINANCE_SECRET_KEY'] = secret_key
    os.environ['BINANCE_TESTNET'] = testnet
    
    # Import and run the clean bot
    from live_testnet_bot_clean import main
    main()
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative approach...")
    
    # Fallback: run the script directly
    os.system(f'python live_testnet_bot_clean.py')
    
except Exception as e:
    print(f"Error starting bot: {e}")
    sys.exit(1)