#!/usr/bin/env python3
"""
Railway Bot Monitoring Demo
Quick demonstration of monitoring capabilities
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def demo_health_monitoring():
    """Demonstrate health monitoring for 60 seconds"""
    print("DEMO: Health Monitoring (60 seconds)")
    print("-" * 50)
    
    try:
        from monitoring.health_checker import HealthChecker
        railway_url = "https://railway-up-production-f151.up.railway.app"
        
        async with HealthChecker(railway_url) as checker:
            for i in range(6):  # 6 checks, 10 seconds apart
                print(f"Health Check {i+1}/6...")
                
                results = await checker._check_all_endpoints()
                overall_health = await checker._analyze_health_results(results)
                
                status = "HEALTHY" if overall_health['overall_healthy'] else "PARTIAL"
                print(f"Status: {status}")
                print(f"Success Rate: {overall_health['health_percentage']:.1f}%")
                print(f"Avg Response: {overall_health['avg_response_time']:.0f}ms")
                print(f"Working Endpoints: {overall_health['successful_endpoints']}/{overall_health['total_endpoints']}")
                
                if overall_health['failing_endpoints']:
                    print(f"Failing: {', '.join(overall_health['failing_endpoints'])}")
                
                print()
                
                if i < 5:  # Don't sleep after last iteration
                    await asyncio.sleep(10)
        
        print("Health monitoring demo completed")
        return True
        
    except Exception as e:
        print(f"Demo failed: {e}")
        return False

async def demo_performance_tracking():
    """Demonstrate performance data collection"""
    print("DEMO: Performance Data Collection")
    print("-" * 50)
    
    try:
        from monitoring.performance_tracker import PerformanceTracker
        railway_url = "https://railway-up-production-f151.up.railway.app"
        
        async with PerformanceTracker(railway_url) as tracker:
            # Collect performance data
            trading_data = await tracker._collect_trading_performance()
            system_data = await tracker._collect_system_performance()
            
            print("TRADING PERFORMANCE:")
            if trading_data:
                print(f"  Total Trades: {trading_data.get('total_trades', 0)}")
                print(f"  Win Rate: {trading_data.get('win_rate', 0):.1f}%")
                print(f"  Daily P&L: {trading_data.get('daily_pnl', 0):.2f}%")
                print(f"  Daily Target Progress: {trading_data.get('daily_target_progress', 0):.1f}%")
                print(f"  Monthly Target Progress: {trading_data.get('monthly_target_progress', 0):.1f}%")
                print(f"  Max Drawdown: {trading_data.get('max_drawdown', 0):.2f}%")
            else:
                print("  No trading data available")
            
            print("\nSYSTEM PERFORMANCE:")
            if system_data:
                print(f"  Memory Usage: {system_data.get('memory_usage_percent', 0):.1f}%")
                print(f"  CPU Usage: {system_data.get('cpu_usage_percent', 0):.1f}%")
                print(f"  Response Time: {system_data.get('average_response_time', 0):.0f}ms")
                print(f"  Error Rate: {system_data.get('error_rate', 0):.1f}%")
                print(f"  Uptime: {system_data.get('uptime_hours', 0):.1f} hours")
                print(f"  Health Status: {system_data.get('status', 'unknown')}")
            else:
                print("  No system data available")
        
        print("\nPerformance tracking demo completed")
        return True
        
    except Exception as e:
        print(f"Performance demo failed: {e}")
        return False

async def demo_comprehensive_monitoring():
    """Demonstrate comprehensive monitoring for 30 seconds"""
    print("DEMO: Comprehensive Monitoring (30 seconds)")
    print("-" * 50)
    
    try:
        from monitoring.railway_monitor import RailwayBotMonitor
        railway_url = "https://railway-up-production-f151.up.railway.app"
        
        async with RailwayBotMonitor(railway_url) as monitor:
            for i in range(3):  # 3 comprehensive checks, 10 seconds apart
                print(f"Comprehensive Check {i+1}/3...")
                
                # Check all endpoints
                health_data = await monitor._check_all_health_endpoints()
                trading_data = await monitor._get_trading_metrics()
                metrics_data = await monitor._get_detailed_metrics()
                
                print(f"Health Data: {'Available' if health_data else 'Unavailable'}")
                print(f"Trading Data: {'Available' if trading_data else 'Unavailable'}")
                print(f"Metrics Data: {'Available' if metrics_data else 'Unavailable'}")
                
                if health_data:
                    overall_health = health_data.get('overall_healthy', False)
                    print(f"Overall Health: {'Good' if overall_health else 'Issues Detected'}")
                
                if trading_data:
                    total_trades = trading_data.get('total_trades', 0)
                    print(f"Trading Activity: {total_trades} trades")
                
                print()
                
                if i < 2:  # Don't sleep after last iteration
                    await asyncio.sleep(10)
        
        print("Comprehensive monitoring demo completed")
        return True
        
    except Exception as e:
        print(f"Comprehensive demo failed: {e}")
        return False

async def main():
    """Main demo runner"""
    print("Railway Bot Monitoring System Demo")
    print("=" * 60)
    print("Demonstrating monitoring capabilities on Railway bot:")
    print("https://railway-up-production-f151.up.railway.app")
    print("=" * 60)
    
    demos = [
        ("Health Monitoring", demo_health_monitoring),
        ("Performance Tracking", demo_performance_tracking),
        ("Comprehensive Monitoring", demo_comprehensive_monitoring),
    ]
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n{'='*20} {demo_name} {'='*20}")
            success = await demo_func()
            if success:
                print(f"{demo_name} demo completed successfully")
            else:
                print(f"{demo_name} demo had issues")
        except KeyboardInterrupt:
            print(f"\n{demo_name} demo interrupted by user")
            break
        except Exception as e:
            print(f"{demo_name} demo failed: {e}")
    
    print(f"\n{'='*60}")
    print("DEMO COMPLETED")
    print("=" * 60)
    print("The monitoring system is ready for production use!")
    print("\nTo start full monitoring:")
    print("  python monitoring/start_monitoring.py --all")
    print("\nTo start interactive dashboard:")
    print("  python monitoring/start_monitoring.py --dashboard")
    print("\nTo run health checks:")
    print("  python monitoring/start_monitoring.py --check")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed: {e}")
        sys.exit(1)