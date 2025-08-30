#!/usr/bin/env python3
"""Test the hourly status report - send one report immediately"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hourly_status_reporter import HourlyStatusReporter

async def test_report():
    reporter = HourlyStatusReporter()
    await reporter.send_hourly_report()
    print("Test report completed!")

if __name__ == "__main__":
    asyncio.run(test_report())