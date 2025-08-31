#!/usr/bin/env python3
"""
Comprehensive diagnostic script for Railway deployment
Checks what's actually happening with the trading bot
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

DEPLOYMENT_URL = "https://railway-up-production-f151.up.railway.app"

def check_endpoint(endpoint: str) -> Dict[str, Any]:
    """Check a specific endpoint and return response details"""
    url = f"{DEPLOYMENT_URL}{endpoint}"
    try:
        response = requests.get(url, timeout=10)
        return {
            "url": url,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text[:500] if response.text else None,
            "json": response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
            "success": response.status_code == 200
        }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }

def analyze_health_data(health_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze health endpoint data for issues"""
    issues = []
    warnings = []
    
    if health_data.get('success'):
        data = health_data.get('json', {})
        
        # Check if trading system is really active
        checks = data.get('checks', {})
        if not checks.get('trading_system'):
            issues.append("Trading system check is failing")
        
        # Check metrics from detailed health
        metrics = data.get('metrics', {})
        trading_metrics = metrics.get('trading', {})
        
        if trading_metrics.get('active_positions', 0) == 0:
            warnings.append("No active positions")
        
        if trading_metrics.get('total_trades', 0) == 0:
            issues.append("Zero total trades - NO TRADING ACTIVITY")
        
        if trading_metrics.get('last_trade_time') is None:
            issues.append("No last trade time - NEVER TRADED")
        
        # Check system resources
        system_metrics = metrics.get('system', {})
        if system_metrics.get('cpu_percent', 0) < 5:
            warnings.append("Very low CPU usage - might not be actively processing")
        
        # Check uptime
        uptime = data.get('uptime_seconds', 0)
        if uptime > 3600 and trading_metrics.get('total_trades', 0) == 0:
            issues.append(f"Running for {uptime/3600:.1f} hours with ZERO trades")
    
    return {
        "issues": issues,
        "warnings": warnings,
        "has_critical_issues": len(issues) > 0
    }

def generate_report():
    """Generate comprehensive diagnostic report"""
    print("="*80)
    print("QUANTUM TRADING BOT - RAILWAY DEPLOYMENT DIAGNOSTIC")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target URL: {DEPLOYMENT_URL}")
    print("="*80)
    
    # Check all endpoints
    endpoints = [
        "/",
        "/health",
        "/health/detailed",
        "/health/ready",
        "/health/live",
        "/metrics",
        "/api",
        "/api/status",
        "/api/positions",
        "/api/trades",
        "/trading",
        "/trading/status",
        "/trading/positions",
        "/status",
        "/positions",
        "/trades",
        "/logs",
        "/dashboard"
    ]
    
    print("\nENDPOINT SCAN:")
    print("-"*80)
    
    available_endpoints = []
    for endpoint in endpoints:
        result = check_endpoint(endpoint)
        status = "[OK]" if result['success'] else "[FAIL]"
        print(f"{status} {endpoint:30} - ", end="")
        
        if result['success']:
            available_endpoints.append(endpoint)
            if result.get('json'):
                print(f"JSON response received")
            else:
                print(f"HTTP {result['status_code']}")
        else:
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                print(f"HTTP {result.get('status_code', 'N/A')}")
    
    print(f"\nFound {len(available_endpoints)} working endpoints")
    
    # Detailed analysis of health endpoints
    print("\nDETAILED HEALTH ANALYSIS:")
    print("-"*80)
    
    detailed_health = check_endpoint("/health/detailed")
    if detailed_health['success'] and detailed_health.get('json'):
        health_data = detailed_health['json']
        
        print(f"Status: {health_data.get('status', 'unknown')}")
        print(f"Version: {health_data.get('version', 'unknown')}")
        print(f"Environment: {health_data.get('environment', 'unknown')}")
        print(f"Uptime: {health_data.get('uptime_seconds', 0)/3600:.2f} hours")
        
        # Trading metrics
        print("\nTRADING METRICS:")
        trading = health_data.get('metrics', {}).get('trading', {})
        print(f"  Active Positions: {trading.get('active_positions', 'N/A')}")
        print(f"  Total Trades: {trading.get('total_trades', 'N/A')}")
        print(f"  Win Rate: {trading.get('win_rate', 'N/A')}")
        print(f"  P&L Today: {trading.get('pnl_today', 'N/A')}")
        print(f"  Last Trade: {trading.get('last_trade_time', 'NEVER')}")
        
        # System metrics
        print("\nSYSTEM METRICS:")
        system = health_data.get('metrics', {}).get('system', {})
        print(f"  CPU Usage: {system.get('cpu_percent', 'N/A')}%")
        print(f"  Memory Usage: {system.get('memory_percent', 'N/A')}%")
        print(f"  Disk Usage: {system.get('disk_usage', 'N/A')}%")
        print(f"  Network Connections: {system.get('network_connections', 'N/A')}")
        
        # Analyze for issues
        analysis = analyze_health_data(detailed_health)
        
        if analysis['issues']:
            print("\nCRITICAL ISSUES DETECTED:")
            for issue in analysis['issues']:
                print(f"  [X] {issue}")
        
        if analysis['warnings']:
            print("\nWARNINGS:")
            for warning in analysis['warnings']:
                print(f"  [!] {warning}")
    
    # Check metrics endpoint for Prometheus data
    print("\nPROMETHEUS METRICS:")
    print("-"*80)
    
    metrics = check_endpoint("/metrics")
    if metrics['success'] and metrics.get('body'):
        lines = metrics['body'].split('\n')
        for line in lines[:20]:  # Show first 20 metrics
            if line and not line.startswith('#'):
                print(f"  {line}")
    
    # Final diagnosis
    print("\nDIAGNOSIS SUMMARY:")
    print("="*80)
    
    if not available_endpoints:
        print("[X] CRITICAL: No endpoints responding - deployment may be down")
    elif '/health' in available_endpoints or '/health/detailed' in available_endpoints:
        if detailed_health['success'] and detailed_health.get('json'):
            trading = detailed_health['json'].get('metrics', {}).get('trading', {})
            
            if trading.get('total_trades', 0) == 0:
                print("[X] CRITICAL: Bot is running but NOT EXECUTING ANY TRADES")
                print("   - Health checks pass but trading logic is not active")
                print("   - Signal generation may be happening but execution is blocked")
                print("   - Check: API keys, trading permissions, risk management blocks")
            elif trading.get('active_positions', 0) == 0:
                print("[!] WARNING: No active positions but bot appears operational")
                print("   - May be waiting for signals or all positions closed")
            else:
                print("[OK] Bot appears to be running with active trading")
        else:
            print("[!] Health endpoint exists but detailed data unavailable")
    else:
        print("[X] No health endpoints available - cannot determine bot status")
    
    print("\nRECOMMENDATIONS:")
    print("-"*80)
    print("1. NO FRONTEND: Deploy a web dashboard for monitoring")
    print("2. NO TRADES: Check executor.py - execution logic may be disabled")
    print("3. NO POSITIONS: Verify API keys have trading permissions")
    print("4. NO PAIRS: Check if volatile pairs are actually being monitored")
    print("5. LOGGING: Add comprehensive logging to track signal->execution flow")
    print("6. MONITORING: Implement real-time trade execution monitoring")

if __name__ == "__main__":
    generate_report()