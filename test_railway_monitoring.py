#!/usr/bin/env python3
"""
Railway Bot Monitoring Test Script
Test and demonstrate all monitoring components
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger_config import setup_logger
from monitoring.railway_monitor import RailwayBotMonitor
from monitoring.railway_dashboard import RailwayDashboard
from monitoring.performance_tracker import PerformanceTracker
from monitoring.health_checker import HealthChecker

# Set up logging
logger = setup_logger("MonitoringTest", level=logging.INFO)

async def test_health_check():
    """Test health checking functionality"""
    print("🔍 Testing Health Checker...")
    railway_url = "https://railway-up-production-f151.up.railway.app"
    
    try:
        async with HealthChecker(railway_url) as checker:
            # Run single health check
            results = await checker._check_all_endpoints()
            overall_health = await checker._analyze_health_results(results)
            
            print(f"✅ Health Check Results:")
            print(f"   Overall Health: {'✅ HEALTHY' if overall_health['overall_healthy'] else '❌ UNHEALTHY'}")
            print(f"   Health Percentage: {overall_health['health_percentage']:.1f}%")
            print(f"   Average Response Time: {overall_health['avg_response_time']:.0f}ms")
            print(f"   Successful Endpoints: {overall_health['successful_endpoints']}/{overall_health['total_endpoints']}")
            
            print("\n📊 Endpoint Details:")
            for endpoint, result in results.items():
                status = "✅" if result['success'] else "❌"
                response_time = f"{result['response_time']:.0f}ms" if result['response_time'] else "N/A"
                error_msg = f" ({result['error']})" if result.get('error') else ""
                print(f"   {status} {endpoint}: {response_time}{error_msg}")
            
            return overall_health['overall_healthy']
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def test_performance_tracking():
    """Test performance tracking functionality"""
    print("\n📊 Testing Performance Tracker...")
    railway_url = "https://railway-up-production-f151.up.railway.app"
    
    try:
        async with PerformanceTracker(railway_url) as tracker:
            # Collect single performance snapshot
            trading_data = await tracker._collect_trading_performance()
            system_data = await tracker._collect_system_performance()
            
            if trading_data:
                print(f"✅ Trading Performance Data:")
                print(f"   Total Trades: {trading_data.get('total_trades', 0)}")
                print(f"   Win Rate: {trading_data.get('win_rate', 0):.1f}%")
                print(f"   Daily P&L: {trading_data.get('daily_pnl', 0):.2f}%")
                print(f"   Daily Target Progress: {trading_data.get('daily_target_progress', 0):.1f}%")
                print(f"   Monthly Target Progress: {trading_data.get('monthly_target_progress', 0):.1f}%")
            else:
                print("❌ No trading performance data available")
            
            if system_data:
                print(f"\n✅ System Performance Data:")
                print(f"   Memory Usage: {system_data.get('memory_usage_percent', 0):.1f}%")
                print(f"   CPU Usage: {system_data.get('cpu_usage_percent', 0):.1f}%")
                print(f"   Response Time: {system_data.get('average_response_time', 0):.0f}ms")
                print(f"   Error Rate: {system_data.get('error_rate', 0):.1f}%")
                print(f"   Uptime: {system_data.get('uptime_hours', 0):.1f} hours")
            else:
                print("❌ No system performance data available")
            
            return True
            
    except Exception as e:
        print(f"❌ Performance tracking test failed: {e}")
        return False

async def test_railway_monitor():
    """Test main railway monitor functionality"""
    print("\n🔍 Testing Railway Monitor...")
    railway_url = "https://railway-up-production-f151.up.railway.app"
    
    try:
        async with RailwayBotMonitor(railway_url) as monitor:
            # Test individual methods
            health_data = await monitor._check_all_health_endpoints()
            trading_data = await monitor._get_trading_metrics()
            metrics_data = await monitor._get_detailed_metrics()
            
            print(f"✅ Railway Monitor Test Results:")
            print(f"   Health Data Available: {'✅' if health_data else '❌'}")
            print(f"   Trading Data Available: {'✅' if trading_data else '❌'}")
            print(f"   Metrics Data Available: {'✅' if metrics_data else '❌'}")
            
            if health_data:
                print(f"   Overall Health: {'✅ HEALTHY' if health_data.get('overall_healthy') else '❌ UNHEALTHY'}")
                successful_endpoints = len([e for e in health_data.get('endpoints', {}).values() if e.get('success')])
                total_endpoints = len(health_data.get('endpoints', {}))
                print(f"   Endpoints: {successful_endpoints}/{total_endpoints} successful")
            
            # Get monitor status
            status = monitor.get_status_summary()
            print(f"\n📊 Monitor Status:")
            print(f"   Consecutive Failures: {status['consecutive_failures']}")
            print(f"   Alert Sent: {status['alert_sent']}")
            print(f"   Health Check Records: {status['total_health_checks']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Railway monitor test failed: {e}")
        return False

async def test_dashboard_data():
    """Test dashboard data collection"""
    print("\n📱 Testing Dashboard Data Collection...")
    railway_url = "https://railway-up-production-f151.up.railway.app"
    
    try:
        async with RailwayDashboard(railway_url) as dashboard:
            # Update dashboard data
            await dashboard._update_all_data()
            
            print(f"✅ Dashboard Data Collection:")
            print(f"   Health Data: {'✅' if dashboard.health_data else '❌'}")
            print(f"   Trading Data: {'✅' if dashboard.trading_data else '❌'}")
            print(f"   Performance Data: {'✅' if dashboard.performance_data else '❌'}")
            print(f"   System Data: {'✅' if dashboard.system_data else '❌'}")
            print(f"   Last Update: {dashboard.last_update or 'Never'}")
            
            # Show sample data if available
            if dashboard.trading_data:
                print(f"\n📊 Sample Trading Data:")
                for key, value in list(dashboard.trading_data.items())[:5]:
                    print(f"   {key}: {value}")
            
            return True
            
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        return False

async def demonstrate_monitoring():
    """Demonstrate monitoring capabilities with short runtime"""
    print("\n🚀 Demonstrating Live Monitoring (30 seconds)...")
    railway_url = "https://railway-up-production-f151.up.railway.app"
    
    try:
        async with HealthChecker(railway_url) as checker:
            print("   Starting health monitoring demonstration...")
            
            # Run monitoring for 30 seconds
            for i in range(6):  # 6 checks, 5 seconds apart
                print(f"   Check {i+1}/6...")
                
                results = await checker._check_all_endpoints()
                overall_health = await checker._analyze_health_results(results)
                
                status = "✅" if overall_health['overall_healthy'] else "❌"
                print(f"   {status} Health: {overall_health['health_percentage']:.1f}% | "
                      f"Response: {overall_health['avg_response_time']:.0f}ms")
                
                if i < 5:  # Don't sleep after last iteration
                    await asyncio.sleep(5)
            
            print("✅ Monitoring demonstration completed")
            return True
            
    except Exception as e:
        print(f"❌ Monitoring demonstration failed: {e}")
        return False

async def main():
    """Main test runner"""
    print("🚀 Railway Bot Monitoring System Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Performance Tracking", test_performance_tracking),
        ("Railway Monitor", test_railway_monitor),
        ("Dashboard Data", test_dashboard_data),
        ("Live Monitoring Demo", demonstrate_monitoring),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = await test_func()
            results[test_name] = result
        except KeyboardInterrupt:
            print(f"\n❌ {test_name} interrupted by user")
            results[test_name] = False
            break
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All monitoring components are working correctly!")
        print("\nTo start monitoring:")
        print("  python monitoring/start_monitoring.py --all")
        print("  python monitoring/start_monitoring.py --dashboard")
        print("  python monitoring/start_monitoring.py --check")
    else:
        print("\n⚠️ Some monitoring components have issues.")
        print("Check the Railway bot is running and accessible at:")
        print("https://railway-up-production-f151.up.railway.app")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Test suite interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Fatal error in test suite: {e}")
        sys.exit(1)