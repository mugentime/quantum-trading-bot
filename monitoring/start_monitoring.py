#!/usr/bin/env python3
"""
Railway Bot Monitoring Launcher
Launch all monitoring components with options for different monitoring modes
"""
import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger_config import setup_logger
from monitoring.railway_monitor import RailwayBotMonitor
from monitoring.railway_dashboard import RailwayDashboard
from monitoring.performance_tracker import PerformanceTracker
from monitoring.health_checker import HealthChecker

# Set up logging
logger = setup_logger("MonitoringLauncher", level=logging.INFO)

class MonitoringLauncher:
    """Comprehensive monitoring launcher for Railway bot"""
    
    def __init__(self, railway_url: str):
        """Initialize the monitoring launcher"""
        self.railway_url = railway_url
        self.monitors = {}
        
    async def start_all_monitoring(self):
        """Start all monitoring components"""
        logger.info("🚀 Starting comprehensive Railway bot monitoring...")
        
        try:
            # Create all monitoring components
            monitors = {}
            
            async with RailwayBotMonitor(self.railway_url) as main_monitor:
                monitors['main'] = main_monitor
                
                async with PerformanceTracker(self.railway_url) as perf_tracker:
                    monitors['performance'] = perf_tracker
                    
                    async with HealthChecker(self.railway_url) as health_checker:
                        monitors['health'] = health_checker
                        
                        # Start all monitoring tasks
                        tasks = [
                            asyncio.create_task(main_monitor.start_monitoring(), name="main_monitor"),
                            asyncio.create_task(perf_tracker.start_tracking(), name="performance_tracker"),
                            asyncio.create_task(health_checker.start_health_monitoring(), name="health_checker")
                        ]
                        
                        logger.info("✅ All monitoring components started")
                        
                        # Wait for all tasks
                        await asyncio.gather(*tasks, return_exceptions=True)
        
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in comprehensive monitoring: {e}", exc_info=True)
        finally:
            logger.info("All monitoring components stopped")
    
    async def start_dashboard_only(self):
        """Start only the dashboard"""
        logger.info("🚀 Starting Railway bot dashboard...")
        
        try:
            async with RailwayDashboard(self.railway_url) as dashboard:
                await dashboard.start_dashboard()
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        except Exception as e:
            logger.error(f"Error in dashboard: {e}", exc_info=True)
    
    async def start_performance_only(self):
        """Start only performance tracking"""
        logger.info("🚀 Starting Railway bot performance tracking...")
        
        try:
            async with PerformanceTracker(self.railway_url) as tracker:
                await tracker.start_tracking()
        except KeyboardInterrupt:
            logger.info("Performance tracking stopped by user")
        except Exception as e:
            logger.error(f"Error in performance tracking: {e}", exc_info=True)
    
    async def start_health_only(self):
        """Start only health checking"""
        logger.info("🚀 Starting Railway bot health checking...")
        
        try:
            async with HealthChecker(self.railway_url) as checker:
                await checker.start_health_monitoring()
        except KeyboardInterrupt:
            logger.info("Health checking stopped by user")
        except Exception as e:
            logger.error(f"Error in health checking: {e}", exc_info=True)
    
    async def start_basic_monitoring(self):
        """Start basic monitoring (health + main monitor)"""
        logger.info("🚀 Starting basic Railway bot monitoring...")
        
        try:
            async with RailwayBotMonitor(self.railway_url) as main_monitor:
                async with HealthChecker(self.railway_url) as health_checker:
                    # Start monitoring tasks
                    tasks = [
                        asyncio.create_task(main_monitor.start_monitoring(), name="main_monitor"),
                        asyncio.create_task(health_checker.start_health_monitoring(), name="health_checker")
                    ]
                    
                    logger.info("✅ Basic monitoring components started")
                    
                    # Wait for all tasks
                    await asyncio.gather(*tasks, return_exceptions=True)
        
        except KeyboardInterrupt:
            logger.info("Basic monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in basic monitoring: {e}", exc_info=True)
    
    async def run_quick_health_check(self):
        """Run a quick one-time health check"""
        logger.info("🔍 Running quick health check...")
        
        try:
            async with HealthChecker(self.railway_url) as checker:
                # Perform single health check
                results = await checker._check_all_endpoints()
                overall_health = await checker._analyze_health_results(results)
                
                # Display results
                status = "✅ HEALTHY" if overall_health['overall_healthy'] else "❌ UNHEALTHY"
                print(f"\n{status} - Railway Bot Health Check")
                print(f"URL: {self.railway_url}")
                print(f"Health: {overall_health['health_percentage']:.1f}%")
                print(f"Response Time: {overall_health['avg_response_time']:.0f}ms")
                print(f"Successful Endpoints: {overall_health['successful_endpoints']}/{overall_health['total_endpoints']}")
                
                if overall_health['failing_endpoints']:
                    print(f"Failing Endpoints: {', '.join(overall_health['failing_endpoints'])}")
                
                print("\nEndpoint Details:")
                for endpoint, result in results.items():
                    status_icon = "✅" if result['success'] else "❌"
                    response_time = f"{result['response_time']:.0f}ms" if result['response_time'] else "N/A"
                    error = f" ({result['error']})" if result['error'] else ""
                    print(f"  {status_icon} {endpoint}: {response_time}{error}")
                
                return overall_health['overall_healthy']
                
        except Exception as e:
            logger.error(f"Error in quick health check: {e}", exc_info=True)
            return False

def create_argument_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Railway Bot Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_monitoring.py --all                    # Start all monitoring components
  python start_monitoring.py --dashboard              # Start interactive dashboard only
  python start_monitoring.py --performance            # Start performance tracking only
  python start_monitoring.py --health                 # Start health checking only
  python start_monitoring.py --basic                  # Start basic monitoring (health + main)
  python start_monitoring.py --check                  # Run single health check
  python start_monitoring.py --url https://mybot.com  # Use custom bot URL
        """
    )
    
    # URL configuration
    parser.add_argument(
        '--url', 
        default='https://railway-up-production-f151.up.railway.app',
        help='Railway bot URL to monitor (default: https://railway-up-production-f151.up.railway.app)'
    )
    
    # Monitoring modes (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--all', 
        action='store_true',
        help='Start all monitoring components (recommended for production)'
    )
    mode_group.add_argument(
        '--dashboard', 
        action='store_true',
        help='Start interactive dashboard only'
    )
    mode_group.add_argument(
        '--performance', 
        action='store_true',
        help='Start performance tracking only'
    )
    mode_group.add_argument(
        '--health', 
        action='store_true',
        help='Start health checking only'
    )
    mode_group.add_argument(
        '--basic', 
        action='store_true',
        help='Start basic monitoring (health + main monitor)'
    )
    mode_group.add_argument(
        '--check', 
        action='store_true',
        help='Run single health check and exit'
    )
    
    # Additional options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser

async def main():
    """Main entry point for monitoring launcher"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Create monitoring launcher
    launcher = MonitoringLauncher(args.url)
    
    print(f"🚀 Railway Bot Monitoring System")
    print(f"Target: {args.url}")
    print("Press Ctrl+C to stop monitoring\n")
    
    try:
        # Route to appropriate monitoring mode
        if args.all:
            await launcher.start_all_monitoring()
        elif args.dashboard:
            await launcher.start_dashboard_only()
        elif args.performance:
            await launcher.start_performance_only()
        elif args.health:
            await launcher.start_health_only()
        elif args.basic:
            await launcher.start_basic_monitoring()
        elif args.check:
            success = await launcher.run_quick_health_check()
            return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Fatal monitoring error: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nMonitoring terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)