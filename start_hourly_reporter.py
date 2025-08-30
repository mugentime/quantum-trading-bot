#!/usr/bin/env python3
"""Start the hourly status reporter system"""
import asyncio
import sys
import os
import schedule
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hourly_status_reporter import HourlyStatusReporter

def run_hourly_reporter():
    """Run the hourly report in async context"""
    reporter = HourlyStatusReporter()
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(reporter.send_hourly_report())
    finally:
        loop.close()

def start_reporter_daemon():
    """Start the hourly scheduling system"""
    print("HOURLY STATUS REPORTER STARTING")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Schedule hourly reports
    schedule.every().hour.at(":00").do(run_hourly_reporter)
    
    # Send initial report immediately
    print("Sending initial report...")
    run_hourly_reporter()
    
    print("\nScheduler active - Reports every hour at :00 minutes")
    print("Check Telegram for comprehensive status updates")
    print("\nPress Ctrl+C to stop the scheduler")
    print("=" * 50)
    
    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
            # Optional: Print a heartbeat every 5 minutes
            if datetime.now().minute % 5 == 0 and datetime.now().second < 30:
                print(f"Reporter running... {datetime.now().strftime('%H:%M:%S')}")
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
        return

if __name__ == "__main__":
    start_reporter_daemon()