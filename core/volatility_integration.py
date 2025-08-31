#!/usr/bin/env python3
"""
VOLATILITY SYSTEM INTEGRATION LAYER
Integration between the advanced volatility scanner and the existing
high-volatility trading system for seamless operation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import os

from core.volatility_scanner import AdvancedVolatilityScanner, VolatilityProfile, TradingOpportunity
from core.volatility_alerts import VolatilityAlertSystem, setup_alert_system_from_env
from strategies.high_volatility_strategy import HighVolatilityStrategy
from config.volatility_config import HighVolatilityConfig, PairConfig
from monitoring.volatility_monitor import VolatilityMonitor

logger = logging.getLogger(__name__)

@dataclass
class IntegrationConfig:
    """Configuration for volatility system integration"""
    enable_dynamic_pairs: bool = True
    enable_auto_alerts: bool = True
    enable_opportunity_signals: bool = True
    
    # Pair management
    min_opportunity_score: float = 60.0
    min_volume_usd: float = 10_000_000
    max_active_pairs: int = 15
    pair_rotation_hours: int = 24
    
    # Signal filtering
    min_signal_confidence: float = 0.7
    require_volume_confirmation: bool = True
    require_breakout_confirmation: bool = True
    
    # Integration thresholds
    volatility_threshold_multiplier: float = 1.2
    opportunity_score_threshold: float = 70.0
    risk_score_limit: float = 80.0
    
    # Performance tracking
    track_integration_metrics: bool = True
    log_pair_changes: bool = True
    log_signal_generation: bool = True

class VolatilitySystemIntegration:
    """
    Integration layer between volatility scanner and trading system
    Manages dynamic pair addition/removal and signal generation
    """
    
    def __init__(self, 
                 trading_config: HighVolatilityConfig,
                 integration_config: IntegrationConfig = None):
        """
        Initialize integration system
        
        Args:
            trading_config: High volatility trading configuration
            integration_config: Integration-specific configuration
        """
        self.trading_config = trading_config
        self.integration_config = integration_config or IntegrationConfig()
        
        # Component instances
        self.scanner: Optional[AdvancedVolatilityScanner] = None
        self.alert_system: Optional[VolatilityAlertSystem] = None
        self.trading_strategy: Optional[HighVolatilityStrategy] = None
        self.monitor: Optional[VolatilityMonitor] = None
        
        # Integration state
        self.integrated_pairs: Set[str] = set()
        self.pair_performance: Dict[str, Dict] = {}
        self.last_pair_update: Optional[datetime] = None
        self.signal_history: List[Dict] = []
        
        # Performance tracking
        self.integration_metrics = {
            'pairs_added': 0,
            'pairs_removed': 0,
            'signals_generated': 0,
            'opportunities_processed': 0,
            'alerts_triggered': 0
        }
        
        # Running state
        self.running = False
        self.integration_task = None
        
        logger.info("Volatility System Integration initialized")
    
    async def initialize(self) -> bool:
        """Initialize all components"""
        try:
            # Get API credentials
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_SECRET_KEY')
            testnet = self.trading_config.trading_mode.value == 'testnet'
            
            if not api_key or not api_secret:
                logger.error("Missing Binance API credentials")
                return False
            
            # Initialize scanner
            self.scanner = AdvancedVolatilityScanner(
                api_key=api_key,
                api_secret=api_secret,
                testnet=testnet,
                scan_interval=30,
                max_monitored_pairs=50
            )
            
            if not await self.scanner.start():
                logger.error("Failed to start volatility scanner")
                return False
            
            # Initialize alert system
            if self.integration_config.enable_auto_alerts:
                self.alert_system = setup_alert_system_from_env()
                logger.info("Alert system initialized")
            
            # Initialize trading strategy
            self.trading_strategy = HighVolatilityStrategy(self.trading_config.to_dict())
            await self.trading_strategy.initialize_exchange()
            
            # Get initial pairs from config
            self.integrated_pairs = set(self.trading_config.get_primary_pairs())
            
            logger.info(f"Integration initialized with {len(self.integrated_pairs)} initial pairs")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize integration: {e}")
            return False
    
    async def start_integration(self):
        """Start the integration system"""
        if self.running:
            logger.warning("Integration already running")
            return
        
        if not await self.initialize():
            logger.error("Failed to initialize integration")
            return
        
        self.running = True
        self.integration_task = asyncio.create_task(self._run_integration_loop())
        
        logger.info("Volatility system integration started")
    
    async def stop_integration(self):
        """Stop the integration system"""
        logger.info("Stopping volatility system integration...")
        
        self.running = False
        
        if self.integration_task:
            self.integration_task.cancel()
            try:
                await self.integration_task
            except asyncio.CancelledError:
                pass
        
        # Stop components
        if self.scanner:
            await self.scanner.stop()
        
        if self.trading_strategy:
            await self.trading_strategy.stop_trading()
        
        logger.info("Volatility system integration stopped")
    
    async def _run_integration_loop(self):
        """Main integration loop"""
        logger.info("Starting integration main loop")
        
        while self.running:
            try:
                # Process volatility data
                await self._process_volatility_data()
                
                # Update pairs if enabled
                if self.integration_config.enable_dynamic_pairs:
                    await self._update_dynamic_pairs()
                
                # Process opportunities
                if self.integration_config.enable_opportunity_signals:
                    await self._process_opportunities()
                
                # Send alerts
                if self.alert_system:
                    await self._process_alerts()
                
                # Update performance metrics
                await self._update_metrics()
                
                # Log status periodically
                await self._log_status()
                
                # Sleep before next iteration
                await asyncio.sleep(60)  # 1 minute intervals
                
            except Exception as e:
                logger.error(f"Integration loop error: {e}")
                await asyncio.sleep(30)  # Brief pause on error
    
    async def _process_volatility_data(self):
        """Process volatility data from scanner"""
        try:
            if not self.scanner or not self.scanner.volatility_profiles:
                return
            
            # Get fresh volatility profiles
            profiles = list(self.scanner.volatility_profiles.values())
            
            if not profiles:
                return
            
            # Update pair performance tracking
            for profile in profiles:
                if profile.symbol in self.integrated_pairs:
                    self.pair_performance[profile.symbol] = {
                        'volatility_score': profile.volatility_score,
                        'opportunity_score': profile.opportunity_score,
                        'risk_score': profile.risk_score,
                        'volume_24h': profile.volume_24h,
                        'price_change_24h': profile.price_change_24h,
                        'last_updated': datetime.now(),
                        'state': profile.volatility_state.value,
                        'condition': profile.market_condition.value
                    }
            
            logger.debug(f"Processed {len(profiles)} volatility profiles")
            
        except Exception as e:
            logger.error(f"Error processing volatility data: {e}")
    
    async def _update_dynamic_pairs(self):
        """Update trading pairs based on volatility data"""
        try:
            if not self.scanner:
                return
            
            # Check if it's time for pair update
            now = datetime.now()
            if (self.last_pair_update and 
                (now - self.last_pair_update).total_seconds() < 3600):  # 1 hour minimum
                return
            
            # Get top opportunities by score
            top_opportunities = []
            for symbol, profile in self.scanner.volatility_profiles.items():
                if (profile.opportunity_score >= self.integration_config.min_opportunity_score and
                    profile.volume_24h >= self.integration_config.min_volume_usd):
                    top_opportunities.append((symbol, profile))
            
            # Sort by opportunity score
            top_opportunities.sort(key=lambda x: x[1].opportunity_score, reverse=True)
            
            # Get current best pairs
            best_pairs = set([symbol for symbol, _ in top_opportunities[:self.integration_config.max_active_pairs]])
            
            # Identify pairs to add/remove
            pairs_to_add = best_pairs - self.integrated_pairs
            pairs_to_remove = self.integrated_pairs - best_pairs
            
            # Remove underperforming pairs
            for symbol in pairs_to_remove:
                if symbol not in self.trading_config.get_primary_pairs():  # Don't remove primary pairs
                    await self._remove_trading_pair(symbol)
                    self.integrated_pairs.remove(symbol)
                    self.integration_metrics['pairs_removed'] += 1
                    
                    if self.integration_config.log_pair_changes:
                        logger.info(f"Removed trading pair: {symbol}")
            
            # Add high-opportunity pairs
            for symbol in pairs_to_add:
                if len(self.integrated_pairs) < self.integration_config.max_active_pairs:
                    await self._add_trading_pair(symbol, top_opportunities)
                    self.integrated_pairs.add(symbol)
                    self.integration_metrics['pairs_added'] += 1
                    
                    if self.integration_config.log_pair_changes:
                        logger.info(f"Added trading pair: {symbol}")
            
            self.last_pair_update = now
            
            if pairs_to_add or pairs_to_remove:
                logger.info(f"Pair update completed: +{len(pairs_to_add)}, -{len(pairs_to_remove)}, "
                           f"total: {len(self.integrated_pairs)}")
            
        except Exception as e:
            logger.error(f"Error updating dynamic pairs: {e}")
    
    async def _add_trading_pair(self, symbol: str, opportunities: List[Tuple[str, VolatilityProfile]]):
        """Add a new trading pair to the system"""
        try:
            # Find the profile for this symbol
            profile = None
            for sym, prof in opportunities:
                if sym == symbol:
                    profile = prof
                    break
            
            if not profile:
                return
            
            # Create pair configuration based on volatility profile
            pair_config = self._create_pair_config_from_profile(symbol, profile)
            
            # Update trading config
            self.trading_config.pair_configs[symbol] = pair_config
            
            # Notify trading strategy if available
            if self.trading_strategy:
                await self.trading_strategy.add_trading_pair(symbol, pair_config)
            
            logger.info(f"Added pair {symbol} with opportunity score {profile.opportunity_score:.1f}")
            
        except Exception as e:
            logger.error(f"Error adding trading pair {symbol}: {e}")
    
    async def _remove_trading_pair(self, symbol: str):
        """Remove a trading pair from the system"""
        try:
            # Remove from config
            if symbol in self.trading_config.pair_configs:
                del self.trading_config.pair_configs[symbol]
            
            # Notify trading strategy
            if self.trading_strategy:
                await self.trading_strategy.remove_trading_pair(symbol)
            
            # Clean up performance data
            if symbol in self.pair_performance:
                del self.pair_performance[symbol]
            
            logger.info(f"Removed pair {symbol}")
            
        except Exception as e:
            logger.error(f"Error removing trading pair {symbol}: {e}")
    
    def _create_pair_config_from_profile(self, symbol: str, profile: VolatilityProfile) -> PairConfig:
        """Create pair configuration from volatility profile"""
        
        # Base configuration
        base_config = PairConfig(
            symbol=symbol,
            min_volatility_threshold=0.05,  # 5% default
            max_position_size_pct=0.03,     # 3% default for new pairs
            base_leverage=3,
            max_leverage=8,
            stop_loss_range=(0.012, 0.025), # Wider stops for new pairs
            liquidity_requirement=profile.volume_24h,
            correlation_limit=0.6,
            priority=3  # Lower priority for dynamic pairs
        )
        
        # Adjust based on volatility characteristics
        if profile.volatility_state.value in ['extreme', 'breakout']:
            base_config.max_position_size_pct *= 0.8  # Reduce size for extreme volatility
            base_config.stop_loss_range = (0.015, 0.030)  # Wider stops
            base_config.max_leverage = 6  # Lower leverage
        
        if profile.risk_score > 70:
            base_config.max_position_size_pct *= 0.7
            base_config.max_leverage = min(base_config.max_leverage, 5)
        
        # Volume-based adjustments
        if profile.volume_24h < 50_000_000:  # Lower liquidity
            base_config.max_position_size_pct *= 0.6
            base_config.max_leverage = min(base_config.max_leverage, 4)
        
        return base_config
    
    async def _process_opportunities(self):
        """Process trading opportunities from scanner"""
        try:
            if not self.scanner:
                return
            
            opportunities = self.scanner.get_top_opportunities(limit=20)
            
            for opportunity in opportunities:
                # Filter opportunities
                if not self._should_process_opportunity(opportunity):
                    continue
                
                # Generate trading signal
                signal = await self._generate_trading_signal(opportunity)
                
                if signal:
                    self.signal_history.append(signal)
                    self.integration_metrics['signals_generated'] += 1
                    
                    if self.integration_config.log_signal_generation:
                        logger.info(f"Generated signal: {signal['symbol']} {signal['side']} "
                                  f"(confidence: {signal['confidence']:.2f})")
                
                self.integration_metrics['opportunities_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing opportunities: {e}")
    
    def _should_process_opportunity(self, opportunity: TradingOpportunity) -> bool:
        """Check if opportunity should be processed"""
        
        # Basic filters
        if opportunity.confidence < self.integration_config.min_signal_confidence:
            return False
        
        if opportunity.volatility_profile.opportunity_score < self.integration_config.opportunity_score_threshold:
            return False
        
        if opportunity.volatility_profile.risk_score > self.integration_config.risk_score_limit:
            return False
        
        # Volume confirmation
        if (self.integration_config.require_volume_confirmation and
            opportunity.volatility_profile.volume_spike_ratio < 1.5):
            return False
        
        # Breakout confirmation
        if (self.integration_config.require_breakout_confirmation and
            not opportunity.volatility_profile.breakout_detected and
            opportunity.volatility_profile.volatility_state.value not in ['high', 'extreme']):
            return False
        
        # Check if symbol is in our trading universe
        if opportunity.symbol not in self.integrated_pairs:
            return False
        
        return True
    
    async def _generate_trading_signal(self, opportunity: TradingOpportunity) -> Optional[Dict]:
        """Generate trading signal from opportunity"""
        try:
            profile = opportunity.volatility_profile
            
            # Calculate position size based on volatility
            base_size = 0.02  # 2% base position
            volatility_adjustment = min(profile.atr_percent / 100, 0.5)  # Max 50% reduction
            position_size = base_size * (1 - volatility_adjustment)
            
            # Calculate stop loss based on ATR
            atr_multiplier = 1.5 if profile.volatility_state.value == 'extreme' else 1.2
            stop_distance = profile.atr_percent * atr_multiplier / 100
            
            # Entry price (current price)
            entry_price = profile.price_change_5min  # Use latest price data
            
            signal = {
                'symbol': opportunity.symbol,
                'side': opportunity.entry_signal,
                'confidence': opportunity.confidence,
                'position_size_pct': position_size,
                'entry_price': entry_price,
                'stop_loss_pct': stop_distance,
                'take_profit_ratio': opportunity.risk_reward_ratio,
                'timestamp': datetime.now(),
                'opportunity_score': profile.opportunity_score,
                'volatility_score': profile.volatility_score,
                'expected_move': opportunity.expected_move,
                'metadata': {
                    'volatility_state': profile.volatility_state.value,
                    'market_condition': profile.market_condition.value,
                    'breakout_detected': profile.breakout_detected,
                    'volume_spike_ratio': profile.volume_spike_ratio
                }
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating trading signal: {e}")
            return None
    
    async def _process_alerts(self):
        """Process alerts from volatility data"""
        try:
            if not self.alert_system or not self.scanner:
                return
            
            # Check volatility profiles
            for profile in self.scanner.volatility_profiles.values():
                await self.alert_system.check_volatility_profile(profile)
            
            # Check opportunities
            opportunities = self.scanner.get_top_opportunities(limit=10)
            for opportunity in opportunities:
                await self.alert_system.check_trading_opportunity(opportunity)
                self.integration_metrics['alerts_triggered'] += 1
            
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
    
    async def _update_metrics(self):
        """Update integration performance metrics"""
        try:
            # Clean old signal history (keep last 100)
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
            
            # Update pair performance
            for symbol in list(self.pair_performance.keys()):
                perf = self.pair_performance[symbol]
                if (datetime.now() - perf['last_updated']).total_seconds() > 7200:  # 2 hours
                    # Mark as stale
                    perf['stale'] = True
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    async def _log_status(self):
        """Log integration status periodically"""
        try:
            # Log every 10 minutes
            if not hasattr(self, '_last_status_log'):
                self._last_status_log = datetime.now()
                return
            
            if (datetime.now() - self._last_status_log).total_seconds() < 600:
                return
            
            if not self.integration_config.track_integration_metrics:
                return
            
            # Get current statistics
            scanner_status = self.scanner.get_scanner_status() if self.scanner else {}
            alert_stats = self.alert_system.get_alert_statistics() if self.alert_system else {}
            
            status_summary = {
                'integrated_pairs': len(self.integrated_pairs),
                'pairs_added': self.integration_metrics['pairs_added'],
                'pairs_removed': self.integration_metrics['pairs_removed'],
                'signals_generated': self.integration_metrics['signals_generated'],
                'opportunities_processed': self.integration_metrics['opportunities_processed'],
                'scanner_opportunities': scanner_status.get('current_opportunities', 0),
                'alerts_sent': alert_stats.get('alerts_sent', 0)
            }
            
            logger.info(f"Integration Status: {status_summary}")
            self._last_status_log = datetime.now()
            
        except Exception as e:
            logger.error(f"Error logging status: {e}")
    
    def get_integration_status(self) -> Dict:
        """Get comprehensive integration status"""
        return {
            'running': self.running,
            'integrated_pairs': list(self.integrated_pairs),
            'pair_count': len(self.integrated_pairs),
            'last_pair_update': self.last_pair_update.isoformat() if self.last_pair_update else None,
            'metrics': self.integration_metrics.copy(),
            'recent_signals': len([s for s in self.signal_history 
                                 if (datetime.now() - s['timestamp']).total_seconds() < 3600]),
            'pair_performance': {
                symbol: {
                    **perf,
                    'last_updated': perf['last_updated'].isoformat()
                }
                for symbol, perf in self.pair_performance.items()
            },
            'scanner_status': self.scanner.get_scanner_status() if self.scanner else {},
            'alert_stats': self.alert_system.get_alert_statistics() if self.alert_system else {}
        }
    
    def get_recent_signals(self, limit: int = 20) -> List[Dict]:
        """Get recent trading signals"""
        signals = sorted(self.signal_history, key=lambda x: x['timestamp'], reverse=True)
        return [{**signal, 'timestamp': signal['timestamp'].isoformat()} 
                for signal in signals[:limit]]
    
    def export_integration_data(self, filepath: str):
        """Export integration data to file"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'status': self.get_integration_status(),
            'signals': self.get_recent_signals(100)
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Integration data exported to {filepath}")

# Factory function for easy setup
async def create_integrated_volatility_system(
    trading_config: HighVolatilityConfig,
    integration_config: IntegrationConfig = None
) -> VolatilitySystemIntegration:
    """
    Create and initialize a complete integrated volatility system
    
    Args:
        trading_config: High volatility trading configuration
        integration_config: Integration configuration
        
    Returns:
        Initialized VolatilitySystemIntegration instance
    """
    
    integration = VolatilitySystemIntegration(trading_config, integration_config)
    
    if await integration.initialize():
        await integration.start_integration()
        return integration
    else:
        raise RuntimeError("Failed to initialize integrated volatility system")