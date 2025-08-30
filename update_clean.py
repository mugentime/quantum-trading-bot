#!/usr/bin/env python3
"""Update bot with real Binance connection - Clean version"""
import os
import sys
import shutil

print("=" * 60)
print("BOT UPDATE SCRIPT - CLEAN VERSION")
print("=" * 60)

# Check we're in the right directory
if not os.path.exists('core/data_collector.py'):
    print("ERROR: Run this from the quantum_trading_bot directory")
    sys.exit(1)

# Create backup directory
backup_dir = '.backups'
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)
    print(f"Created backup directory: {backup_dir}")

# Backup files
files = ['core/data_collector.py', 'core/correlation_engine.py', 'core/signal_generator.py']
for file in files:
    if os.path.exists(file):
        backup = os.path.join(backup_dir, os.path.basename(file) + '.bak')
        if not os.path.exists(backup):
            shutil.copy2(file, backup)
            print(f"Backed up: {file}")

print("\nUpdating files...")
updates_done = 0

# Simple test update to verify it works
test_content = '''"""Test file to verify update works"""
print("Update successful")
'''

try:
    with open('test_update.py', 'w') as f:
        f.write(test_content)
    print("Test file created successfully")
    updates_done += 1
except Exception as e:
    print(f"Error: {e}")

print(f"\nUpdate complete! {updates_done} files updated")
print("Now we need to update the actual bot files...")
