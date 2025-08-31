#!/usr/bin/env python3
"""
ADVANCED VOLATILITY TRADING SYSTEM - MAIN ENTRY POINT
Comprehensive volatility scanning, detection, and trading system
with dynamic pair management and intelligent opportunity discovery.
"""

import asyncio
import argparse
import logging
import sys
import os
import signal
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uvicorn
from contextlib import asynccontextmanager

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.volatility_scanner import AdvancedVolatilityScanner
from core.volatility_alerts import setup_alert_system_from_env
from core.volatility_integration import VolatilitySystemIntegration, IntegrationConfig
from api.volatility_api import app as api_app
from config.volatility_config import HighVolatilityConfig, TradingMode
from strategies.high_volatility_strategy import HighVolatilityStrategy

# Configure logging
def setup_logging(log_level: str = "INFO"):
    """Setup comprehensive logging"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / 'volatility_system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('ccxt').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")
    return logger

logger = setup_logging()

class AdvancedVolatilityTradingSystem:
    """
    Main system orchestrator for advanced volatility trading
    Coordinates scanner, alerts, integration, and API components
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.trading_config = None
        self.integration_config = None
        
        # System components
        self.scanner: Optional[AdvancedVolatilityScanner] = None
        self.alert_system = None
        self.integration: Optional[VolatilitySystemIntegration] = None
        self.api_server = None
        
        # System state
        self.running = False
        self.start_time = None
        self.shutdown_event = asyncio.Event()
        
        # Performance tracking
        self.stats = {
            'start_time': None,
            'pairs_discovered': 0,
            'opportunities_found': 0,
            'alerts_sent': 0,
            'api_requests': 0
        }
        
        logger.info("Advanced Volatility Trading System initialized")
    
    def _load_configuration(self):
        """Load and validate configuration"""
        try:
            # Trading configuration
            config_file = self.config.get('trading_config_file')
            if config_file and os.path.exists(config_file):
                self.trading_config = HighVolatilityConfig(config_file)
            else:
                self.trading_config = HighVolatilityConfig()
            
            # Set trading mode
            trading_mode = self.config.get('trading_mode', 'testnet')
            if trading_mode.lower() == 'mainnet':
                self.trading_config.set_trading_mode(TradingMode.MAINNET)
                logger.warning("🚨 MAINNET MODE: Real money trading enabled")
            else:
                self.trading_config.set_trading_mode(TradingMode.TESTNET)
                logger.info("🧪 TESTNET MODE: Paper trading enabled")
            
            # Integration configuration
            self.integration_config = IntegrationConfig(
                enable_dynamic_pairs=self.config.get('enable_dynamic_pairs', True),
                enable_auto_alerts=self.config.get('enable_alerts', True),
                enable_opportunity_signals=self.config.get('enable_signals', True),
                min_opportunity_score=self.config.get('min_opportunity_score', 60.0),
                min_volume_usd=self.config.get('min_volume_usd', 10_000_000),
                max_active_pairs=self.config.get('max_active_pairs', 15)
            )
            
            logger.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False
    
    def _validate_environment(self) -> bool:
        """Validate required environment variables"""
        required_vars = ['BINANCE_API_KEY', 'BINANCE_SECRET_KEY']
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        # Log masked API key for verification
        api_key = os.getenv('BINANCE_API_KEY')
        masked_key = f"{api_key[:8]}...{api_key[-8:]}" if api_key else "None"
        logger.info(f"Using API key: {masked_key}")
        
        return True
    
    async def initialize_components(self) -> bool:
        """Initialize all system components"""
        try:
            logger.info("Initializing system components...")
            
            # Load configuration
            if not self._load_configuration():
                return False
            
            # Validate environment
            if not self._validate_environment():
                return False
            
            # Initialize integration layer (includes scanner)
            logger.info("Initializing volatility integration...")
            self.integration = VolatilitySystemIntegration(
                self.trading_config,
                self.integration_config
            )
            
            if not await self.integration.initialize():
                logger.error("Failed to initialize integration layer")
                return False
            
            # Get scanner reference
            self.scanner = self.integration.scanner
            
            # Initialize alert system if enabled
            if self.integration_config.enable_auto_alerts:
                logger.info("Initializing alert system...")
                self.alert_system = setup_alert_system_from_env()
                self.integration.alert_system = self.alert_system
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            return False
    
    async def start_system(self):
        """Start the complete volatility trading system"""
        if self.running:
            logger.warning("System already running")
            return
        
        logger.info("🚀 STARTING ADVANCED VOLATILITY TRADING SYSTEM")
        logger.info("=" * 80)
        
        try:
            # Initialize components
            if not await self.initialize_components():
                logger.error("System initialization failed")
                return
            
            self.running = True
            self.start_time = datetime.now()
            self.stats['start_time'] = self.start_time
            
            # Start integration layer
            logger.info("Starting volatility integration...")
            await self.integration.start_integration()
            
            # Start API server if enabled
            if self.config.get('enable_api', True):
                await self._start_api_server()
            
            # Log system status
            await self._log_system_startup()
            
            # Main system loop
            await self._run_system_loop()
            
        except Exception as e:
            logger.error(f"System startup failed: {e}")
            await self.stop_system()
    
    async def _start_api_server(self):
        """Start the API server"""
        try:
            api_host = self.config.get('api_host', '0.0.0.0')
            api_port = self.config.get('api_port', 8000)
            
            # Start API server in background
            config = uvicorn.Config(
                api_app,
                host=api_host,
                port=api_port,
                log_level="info"
            )
            
            self.api_server = uvicorn.Server(config)
            
            # Start server task
            asyncio.create_task(self.api_server.serve())
            
            logger.info(f"API server started on http://{api_host}:{api_port}")
            logger.info("API endpoints available:")
            logger.info("  GET  /health - Health check")
            logger.info("  GET  /scanner/status - Scanner status")
            logger.info("  GET  /volatility/profiles - All volatility profiles")
            logger.info("  GET  /opportunities - Trading opportunities")
            logger.info("  GET  /volatility/rankings - Volatility rankings")
            logger.info("  GET  /volatility/breakouts - Breakout detection")
            logger.info("  WebSocket /ws/volatility - Real-time updates")
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
    
    async def _log_system_startup(self):
        """Log comprehensive system startup information"""
        logger.info("📊 SYSTEM STARTUP SUMMARY:")
        logger.info(f"  Trading Mode: {self.trading_config.trading_mode.value.upper()}")
        logger.info(f"  Exchange: {self.trading_config.exchange.value.upper()}")
        logger.info(f"  Scan Interval: {self.scanner.scan_interval}s")
        logger.info(f"  Max Monitored Pairs: {self.scanner.max_monitored_pairs}")
        logger.info(f"  Dynamic Pairs: {'Enabled' if self.integration_config.enable_dynamic_pairs else 'Disabled'}")
        logger.info(f"  Auto Alerts: {'Enabled' if self.integration_config.enable_auto_alerts else 'Disabled'}")
        logger.info(f"  Signal Generation: {'Enabled' if self.integration_config.enable_opportunity_signals else 'Disabled'}")
        logger.info(f"  API Server: {'Running' if self.api_server else 'Disabled'}")
        
        # Trading pairs info
        primary_pairs = self.trading_config.get_primary_pairs()
        logger.info(f"  Primary Pairs ({len(primary_pairs)}): {', '.join(primary_pairs)}")
        
        # Volatility thresholds
        vt = self.trading_config.volatility_thresholds
        logger.info(f"  Volatility Thresholds:")
        logger.info(f"    - 5min: >{self.scanner.volatility_thresholds['min_5min']:.1%}")
        logger.info(f"    - Hourly: >{self.scanner.volatility_thresholds['min_hourly']:.1%}")
        logger.info(f"    - Daily: >{self.scanner.volatility_thresholds['min_daily']:.1%}")
        logger.info(f"    - Volume: >${self.scanner.volatility_thresholds['min_volume_usd']:,}")
        
        logger.info("=" * 80)
        logger.info("🎯 System ready for volatility detection and trading")
        logger.info("⚡ Monitoring market for high-volatility opportunities...")
        logger.info("=" * 80)
    
    async def _run_system_loop(self):
        """Main system monitoring and coordination loop"""
        logger.info("Starting system monitoring loop")
        
        status_interval = 300  # 5 minutes
        last_status_log = datetime.now()
        
        while self.running:
            try:
                # Update statistics
                await self._update_statistics()
                
                # Log status periodically
                now = datetime.now()
                if (now - last_status_log).total_seconds() >= status_interval:
                    await self._log_system_status()
                    last_status_log = now
                
                # Check for shutdown signal
                try:
                    await asyncio.wait_for(self.shutdown_event.wait(), timeout=30)
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Normal operation
                
            except Exception as e:
                logger.error(f"System loop error: {e}")
                await asyncio.sleep(30)
    
    async def _update_statistics(self):
        """Update system statistics"""
        try:
            if self.scanner:
                scanner_status = self.scanner.get_scanner_status()
                self.stats['pairs_discovered'] = scanner_status.get('monitored_pairs', 0)
                self.stats['opportunities_found'] = scanner_status.get('opportunities_found', 0)
            
            if self.alert_system:
                alert_stats = self.alert_system.get_alert_statistics()
                self.stats['alerts_sent'] = alert_stats.get('alerts_sent', 0)
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    async def _log_system_status(self):
        """Log comprehensive system status"""
        try:
            if not self.start_time:
                return
            
            runtime = datetime.now() - self.start_time
            runtime_hours = runtime.total_seconds() / 3600
            
            logger.info("📊 SYSTEM STATUS REPORT:")
            logger.info(f"  Runtime: {runtime_hours:.1f} hours")
            logger.info(f"  System Status: {'Running' if self.running else 'Stopped'}")
            
            # Scanner status
            if self.scanner:
                scanner_status = self.scanner.get_scanner_status()
                logger.info(f"  Scanner Status:")
                logger.info(f"    - Active Pairs: {len(scanner_status.get('active_pairs', []))}")
                logger.info(f"    - Candidate Pairs: {len(scanner_status.get('candidate_pairs', []))}")
                logger.info(f"    - Total Scans: {scanner_status.get('scan_count', 0)}")
                logger.info(f"    - Current Opportunities: {scanner_status.get('current_opportunities', 0)}")
                logger.info(f"    - Success Rate: {scanner_status.get('performance', {}).get('success_rate', 0):.1%}")
            
            # Integration status
            if self.integration:
                integration_status = self.integration.get_integration_status()
                logger.info(f"  Integration Status:")
                logger.info(f"    - Integrated Pairs: {integration_status.get('pair_count', 0)}")
                logger.info(f"    - Pairs Added: {integration_status['metrics']['pairs_added']}")
                logger.info(f"    - Pairs Removed: {integration_status['metrics']['pairs_removed']}")
                logger.info(f"    - Signals Generated: {integration_status['metrics']['signals_generated']}")
                logger.info(f"    - Recent Signals: {integration_status.get('recent_signals', 0)}")
            
            # Alert statistics
            if self.alert_system:
                alert_stats = self.alert_system.get_alert_statistics()
                logger.info(f"  Alert System:")
                logger.info(f"    - Alerts Sent: {alert_stats.get('alerts_sent', 0)}")
                logger.info(f"    - Alerts Suppressed: {alert_stats.get('alerts_suppressed', 0)}")
                logger.info(f"    - Active Rules: {alert_stats.get('active_rules', 0)}")
                logger.info(f"    - Suppression Rate: {alert_stats.get('suppression_rate', 0):.1%}")
            
            # Top opportunities
            if self.scanner:
                opportunities = self.scanner.get_top_opportunities(5)
                if opportunities:
                    logger.info(f"  Top Opportunities:")
                    for i, opp in enumerate(opportunities[:3], 1):
                        logger.info(f"    {i}. {opp.symbol}: {opp.entry_signal.upper()} "
                                  f"(confidence: {opp.confidence:.2f}, "
                                  f"score: {opp.volatility_profile.opportunity_score:.1f})")
            
            logger.info("-" * 60)
            
        except Exception as e:
            logger.error(f"Error logging system status: {e}")
    
    async def stop_system(self):
        """Stop the complete system gracefully"""
        if not self.running:
            return
        
        logger.info("🛑 STOPPING ADVANCED VOLATILITY TRADING SYSTEM")
        
        try:
            self.running = False
            self.shutdown_event.set()
            
            # Stop integration layer
            if self.integration:
                await self.integration.stop_integration()
            
            # Stop API server
            if self.api_server:
                self.api_server.should_exit = True
            
            # Log final statistics
            await self._log_final_statistics()
            
            logger.info("✅ Advanced Volatility Trading System stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during system shutdown: {e}")
    
    async def _log_final_statistics(self):
        """Log final system statistics"""
        try:
            if not self.start_time:
                return
            
            runtime = datetime.now() - self.start_time
            
            logger.info("📊 FINAL SYSTEM STATISTICS:")
            logger.info(f"  Total Runtime: {runtime}")
            logger.info(f"  Pairs Discovered: {self.stats['pairs_discovered']}")
            logger.info(f"  Opportunities Found: {self.stats['opportunities_found']}")
            logger.info(f"  Alerts Sent: {self.stats['alerts_sent']}")
            
            # Export final data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = f"volatility_system_report_{timestamp}.json"
            
            if self.integration:
                self.integration.export_integration_data(export_file)
                logger.info(f"Final system data exported to: {export_file}")
            
        except Exception as e:
            logger.error(f"Error logging final statistics: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.stop_system())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

def create_system_config(args) -> Dict:
    """Create system configuration from command line arguments"""
    return {
        'trading_mode': args.mode,
        'trading_config_file': args.config,
        'enable_dynamic_pairs': not args.disable_dynamic_pairs,
        'enable_alerts': not args.disable_alerts,
        'enable_signals': not args.disable_signals,
        'enable_api': not args.disable_api,
        'api_host': args.api_host,
        'api_port': args.api_port,
        'min_opportunity_score': args.min_opportunity_score,
        'min_volume_usd': args.min_volume_usd,
        'max_active_pairs': args.max_active_pairs,
        'log_level': args.log_level
    }

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Advanced Volatility Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (testnet)
  python volatility_main.py
  
  # Run in mainnet mode with custom config
  python volatility_main.py --mode mainnet --config my_config.json
  
  # Run scanner only with API disabled
  python volatility_main.py --disable-api --disable-signals
  
  # Run with high opportunity threshold
  python volatility_main.py --min-opportunity-score 80 --max-active-pairs 10
        """
    )
    
    # Trading mode and configuration
    parser.add_argument('--mode', choices=['testnet', 'mainnet'], default='testnet',
                       help='Trading mode (default: testnet)')
    parser.add_argument('--config', type=str,
                       help='Path to trading configuration file')
    
    # Feature toggles
    parser.add_argument('--disable-dynamic-pairs', action='store_true',
                       help='Disable dynamic pair addition/removal')
    parser.add_argument('--disable-alerts', action='store_true',
                       help='Disable alert system')
    parser.add_argument('--disable-signals', action='store_true',
                       help='Disable trading signal generation')
    parser.add_argument('--disable-api', action='store_true',
                       help='Disable API server')
    
    # API configuration
    parser.add_argument('--api-host', default='0.0.0.0',
                       help='API server host (default: 0.0.0.0)')
    parser.add_argument('--api-port', type=int, default=8000,
                       help='API server port (default: 8000)')
    
    # System parameters
    parser.add_argument('--min-opportunity-score', type=float, default=60.0,
                       help='Minimum opportunity score for pair inclusion (default: 60.0)')
    parser.add_argument('--min-volume-usd', type=int, default=10000000,
                       help='Minimum daily volume in USD (default: 10000000)')
    parser.add_argument('--max-active-pairs', type=int, default=15,
                       help='Maximum active trading pairs (default: 15)')
    
    # Logging
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging with specified level
    global logger
    logger = setup_logging(args.log_level)
    
    # Display system banner
    print("🌊 ADVANCED VOLATILITY TRADING SYSTEM")
    print("=" * 80)
    print("🎯 Real-time volatility scanning across 50+ pairs")
    print("⚡ Dynamic pair discovery and opportunity detection") 
    print("🛡️ Intelligent risk management and position sizing")
    print("🔔 Multi-channel alert system (Telegram, Discord, Email)")
    print("📊 Comprehensive API and WebSocket endpoints")
    print("🤖 Seamless integration with existing trading systems")
    print("=" * 80)
    
    # Mainnet warning
    if args.mode == 'mainnet':
        print("\n🚨 WARNING: MAINNET MODE - REAL MONEY TRADING")
        print("This system will trade with real funds on your account!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("User aborted mainnet trading")
            return
        print()
    
    try:
        # Create system configuration
        config = create_system_config(args)
        
        # Create and start system
        system = AdvancedVolatilityTradingSystem(config)
        system.setup_signal_handlers()
        
        # Start system
        await system.start_system()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error("Full traceback:", exc_info=True)
    finally:
        logger.info("🏁 Advanced Volatility Trading System session ended")

if __name__ == "__main__":
    # Set up proper event loop policy for Windows
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 System interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal system error: {e}")
        sys.exit(1)