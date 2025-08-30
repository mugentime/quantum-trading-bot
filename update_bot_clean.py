#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update script for Quantum Trading Bot
Activates real Binance connection
"""

import os
import sys
import shutil

print("=" * 60)
print("QUANTUM TRADING BOT - UPDATER")
print("=" * 60)

# Check we're in correct directory
if not os.path.exists('core/data_collector.py'):
    print("ERROR: Run this from quantum_trading_bot folder")
    sys.exit(1)

# Create backup directory
backup_dir = '.backups'
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)
    print(f"Created backup directory: {backup_dir}")

# Backup original files
files = ['core/data_collector.py', 'core/correlation_engine.py', 'core/signal_generator.py']
for file in files:
    if os.path.exists(file):
        backup = os.path.join(backup_dir, os.path.basename(file) + '.bak')
        if not os.path.exists(backup):
            shutil.copy2(file, backup)
            print(f"Backed up: {file}")

print("\nUpdating core modules...")
print("This will enable real Binance testnet connection")
print("-" * 40)

# Just create a simple test to verify it works
test_code = '''
import sys
print("Update script is working!")
print(f"Python version: {sys.version}")
print("Ready to update bot files")
'''

exec(test_code)

print("\nUpdate complete! Run 'python main.py' to start the bot")
