#!/usr/bin/env python3
"""
Railway Bot Monitoring Test Script (Windows Compatible)
Test and demonstrate all monitoring components without emojis
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger_config import setup_logger

# Set up logging
logger = setup_logger("MonitoringTest", level=logging.INFO)

async def test_basic_connection():
    """Test basic connection to Railway bot"""
    print("Testing basic connection to Railway bot...")
    
    try:
        import aiohttp
        railway_url = "https://railway-up-production-f151.up.railway.app"
        
        async with aiohttp.ClientSession() as session:
            # Test root endpoint
            async with session.get(f"{railway_url}/") as response:
                if response.status == 200:
                    print(f"[OK] Root endpoint accessible: {response.status}")
                    return True
                else:
                    print(f"[FAIL] Root endpoint failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"[ERROR] Connection test failed: {e}")
        return False

async def test_health_endpoints():
    """Test all health endpoints"""
    print("Testing health endpoints...")
    
    try:
        import aiohttp
        railway_url = "https://railway-up-production-f151.up.railway.app"
        
        endpoints = ['/health', '/health/detailed', '/ready', '/live', '/metrics']
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    url = f"{railway_url}{endpoint}"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        results[endpoint] = response.status == 200
                        status = "OK" if response.status == 200 else "FAIL"
                        print(f"[{status}] {endpoint}: {response.status}")
                except Exception as e:
                    results[endpoint] = False
                    print(f"[ERROR] {endpoint}: {e}")
        
        successful = sum(results.values())
        total = len(results)
        print(f"Health endpoints: {successful}/{total} successful")
        
        return successful > 0  # At least one endpoint working
        
    except Exception as e:
        print(f"[ERROR] Health endpoint test failed: {e}")
        return False

async def test_monitoring_components():
    """Test monitoring components can be imported and initialized"""
    print("Testing monitoring components...")
    
    try:
        # Test imports
        from monitoring.railway_monitor import RailwayBotMonitor
        from monitoring.railway_dashboard import RailwayDashboard
        from monitoring.performance_tracker import PerformanceTracker
        from monitoring.health_checker import HealthChecker
        
        print("[OK] All monitoring components imported successfully")
        
        # Test initialization
        railway_url = "https://railway-up-production-f151.up.railway.app"
        
        components = [
            ("RailwayBotMonitor", RailwayBotMonitor(railway_url)),
            ("RailwayDashboard", RailwayDashboard(railway_url)),
            ("PerformanceTracker", PerformanceTracker(railway_url)),
            ("HealthChecker", HealthChecker(railway_url))
        ]
        
        for name, component in components:
            if component:
                print(f"[OK] {name} initialized successfully")
            else:
                print(f"[FAIL] {name} initialization failed")
                return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Component test failed: {e}")
        return False

async def test_quick_health_check():
    """Run a quick health check using the health checker"""
    print("Running quick health check...")
    
    try:
        from monitoring.health_checker import HealthChecker
        railway_url = "https://railway-up-production-f151.up.railway.app"
        
        async with HealthChecker(railway_url) as checker:
            # Perform single health check
            results = await checker._check_all_endpoints()
            overall_health = await checker._analyze_health_results(results)
            
            # Display results
            status = "HEALTHY" if overall_health['overall_healthy'] else "UNHEALTHY"
            print(f"Overall Status: {status}")
            print(f"Health Percentage: {overall_health['health_percentage']:.1f}%")
            print(f"Average Response Time: {overall_health['avg_response_time']:.0f}ms")
            print(f"Successful Endpoints: {overall_health['successful_endpoints']}/{overall_health['total_endpoints']}")
            
            if overall_health['failing_endpoints']:
                print(f"Failing Endpoints: {', '.join(overall_health['failing_endpoints'])}")
            
            return overall_health['overall_healthy']
            
    except Exception as e:
        print(f"[ERROR] Quick health check failed: {e}")
        return False

async def main():
    """Main test runner"""
    print("Railway Bot Monitoring System Test Suite")
    print("=" * 60)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Health Endpoints", test_health_endpoints),
        ("Monitoring Components", test_monitoring_components),
        ("Quick Health Check", test_quick_health_check),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n--- {test_name} ---")
            result = await test_func()
            results[test_name] = result
            status = "PASSED" if result else "FAILED"
            print(f"Test Result: {status}")
        except KeyboardInterrupt:
            print(f"\n{test_name} interrupted by user")
            results[test_name] = False
            break
        except Exception as e:
            print(f"\n{test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\nAll monitoring components are working correctly!")
        print("\nTo start monitoring:")
        print("  python monitoring/start_monitoring.py --all")
        print("  python monitoring/start_monitoring.py --dashboard")
        print("  python monitoring/start_monitoring.py --check")
    else:
        print("\nSome monitoring components have issues.")
        print("Check the Railway bot is running and accessible at:")
        print("https://railway-up-production-f151.up.railway.app")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error in test suite: {e}")
        sys.exit(1)