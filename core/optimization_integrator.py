"""
Optimization Integration System
Integrates all optimization enhancements into the main trading system
"""
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .multi_timeframe_analyzer import multi_timeframe_analyzer
from .dynamic_exit_manager import dynamic_exit_manager
from .market_regime_detector import market_regime_detector
from .advanced_risk_manager import advanced_risk_manager
from .correlation_pair_expander import correlation_pair_expander
from .ml_signal_predictor import ml_signal_predictor
from .enhanced_correlation_engine import get_enhanced_correlation_engine
from .config.settings import config

logger = logging.getLogger(__name__)

class OptimizationIntegrator:
    """Integrates all optimization enhancements for improved trading performance"""
    
    def __init__(self):
        self.optimization_active = True
        self.enhancement_weights = {
            'enhanced_correlation': 0.30,  # New enhanced 10-pair correlation system
            'multi_timeframe': 0.20,
            'dynamic_exit': 0.15,
            'market_regime': 0.15,
            'advanced_risk': 0.10,
            'correlation_pairs': 0.05,     # Reduced as enhanced system replaces this
            'ml_prediction': 0.05
        }
        
    async def generate_enhanced_signal(self, base_signal: Dict, symbols: List[str],
                                     exchange = None) -> Dict:
        """
        Generate enhanced trading signal using all optimization systems
        
        Args:
            base_signal: Original correlation breakdown signal
            symbols: List of symbols for analysis
            exchange: Exchange interface
            
        Returns:
            Enhanced signal with optimization improvements
        """
        try:
            if not self.optimization_active:
                logger.info("Optimization disabled, returning base signal")
                return base_signal
            
            logger.info(f"Generating enhanced signal for {base_signal.get('symbol', 'UNKNOWN')}")
            
            # Run all enhancement analyses in parallel (with enhanced correlation system)
            enhancement_tasks = await asyncio.gather(
                self._run_enhanced_correlation_analysis(base_signal, exchange),  # NEW: Enhanced 10-pair correlation
                self._run_multi_timeframe_analysis(base_signal, exchange),
                self._run_market_regime_analysis(symbols, exchange),
                self._run_correlation_pair_analysis(symbols, exchange),
                self._run_ml_signal_prediction(base_signal),
                return_exceptions=True
            )
            
            # Extract results (handle exceptions)
            enhanced_corr_result = enhancement_tasks[0] if not isinstance(enhancement_tasks[0], Exception) else {}
            multi_tf_result = enhancement_tasks[1] if not isinstance(enhancement_tasks[1], Exception) else {}
            regime_result = enhancement_tasks[2] if not isinstance(enhancement_tasks[2], Exception) else {}
            correlation_result = enhancement_tasks[3] if not isinstance(enhancement_tasks[3], Exception) else {}
            ml_result = enhancement_tasks[4] if not isinstance(enhancement_tasks[4], Exception) else {}
            
            # Combine all enhancements (including enhanced correlation)
            enhanced_signal = self._combine_signal_enhancements(
                base_signal, enhanced_corr_result, multi_tf_result, regime_result, correlation_result, ml_result
            )
            
            # Apply regime-based adjustments
            regime_adjusted_signal = self._apply_regime_adjustments(enhanced_signal, regime_result)
            
            logger.info(f"Enhanced signal generated: strength={enhanced_signal.get('final_strength', 0):.3f}, "
                       f"confidence={enhanced_signal.get('confidence', 0):.3f}")
            
            return regime_adjusted_signal
            
        except Exception as e:
            logger.error(f"Error generating enhanced signal: {e}")
            return base_signal
    
    async def validate_enhanced_trade_risk(self, signal: Dict, account_balance: float,
                                         current_positions: Dict = None,
                                         exchange = None) -> Dict:
        """
        Enhanced trade risk validation using advanced risk manager
        
        Args:
            signal: Enhanced trading signal
            account_balance: Current account balance
            current_positions: Currently open positions
            exchange: Exchange interface
            
        Returns:
            Comprehensive risk validation result
        """
        try:
            # Extract proposed parameters from enhanced signal
            proposed_leverage = signal.get('suggested_leverage', config.DEFAULT_LEVERAGE)
            proposed_position_size = signal.get('suggested_position_size', config.RISK_PER_TRADE)
            
            # Run advanced risk validation
            risk_result = await advanced_risk_manager.validate_advanced_trade_risk(
                signal, account_balance, proposed_leverage, proposed_position_size,
                current_positions, exchange
            )
            
            logger.info(f"Enhanced risk validation: approved={risk_result.get('approved', False)}, "
                       f"risk_score={risk_result.get('risk_score', 1.0):.2f}")
            
            return risk_result
            
        except Exception as e:
            logger.error(f"Error in enhanced risk validation: {e}")
            return {
                'approved': False,
                'risk_score': 1.0,
                'warnings': [f"Risk validation error: {e}"],
                'adjustments': {},
                'reasoning': "Error in enhanced risk validation"
            }
    
    async def setup_enhanced_exit_management(self, position: Dict, current_price: float,
                                           exchange = None) -> Dict:
        """
        Setup enhanced exit management for position
        
        Args:
            position: Position data
            current_price: Current market price
            exchange: Exchange interface
            
        Returns:
            Enhanced exit management configuration
        """
        try:
            # Setup dynamic exit timing
            exit_timing = await dynamic_exit_manager.calculate_dynamic_exit_timing(
                position.get('symbol'), position.get('entry_price'),
                datetime.fromisoformat(position.get('entry_time', datetime.now().isoformat())),
                position.get('side'), exchange
            )
            
            # Setup trailing stop
            trailing_stop = await advanced_risk_manager.setup_trailing_stop(
                position, current_price, exchange
            )
            
            # Combine exit management strategies
            enhanced_exit = {
                'dynamic_timing': exit_timing,
                'trailing_stop': trailing_stop,
                'exit_strategy': 'enhanced',
                'setup_time': datetime.now()
            }
            
            logger.info(f"Enhanced exit management setup for {position.get('symbol')}")
            
            return enhanced_exit
            
        except Exception as e:
            logger.error(f"Error setting up enhanced exit management: {e}")
            return {}
    
    async def _run_multi_timeframe_analysis(self, signal: Dict, exchange) -> Dict:
        """Run multi-timeframe correlation analysis"""
        try:
            symbol = signal.get('symbol', 'ETHUSDT')
            vs_symbol = 'BTCUSDT'
            
            multi_tf_result = await multi_timeframe_analyzer.analyze_multi_timeframe_correlation(
                symbol, vs_symbol, exchange
            )
            
            return multi_tf_result
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe analysis: {e}")
            return {}
    
    async def _run_market_regime_analysis(self, symbols: List[str], exchange) -> Dict:
        """Run market regime detection"""
        try:
            regime_result = await market_regime_detector.detect_market_regime(symbols, exchange)
            return regime_result
            
        except Exception as e:
            logger.error(f"Error in market regime analysis: {e}")
            return {}
    
    async def _run_correlation_pair_analysis(self, symbols: List[str], exchange) -> Dict:
        """Run correlation pair expansion analysis"""
        try:
            correlation_result = await correlation_pair_expander.analyze_multi_pair_correlations(
                symbols, exchange
            )
            return correlation_result
            
        except Exception as e:
            logger.error(f"Error in correlation pair analysis: {e}")
            return {}
    
    async def _run_ml_signal_prediction(self, signal: Dict) -> Dict:
        """Run ML signal prediction"""
        try:
            ml_result = await ml_signal_predictor.predict_signal_strength(signal, {})
            return ml_result
            
        except Exception as e:
            logger.error(f"Error in ML signal prediction: {e}")
            return {}
    
    def _combine_signal_enhancements(self, base_signal: Dict, enhanced_corr_result: Dict, 
                                   multi_tf_result: Dict, regime_result: Dict, 
                                   correlation_result: Dict, ml_result: Dict) -> Dict:
        """Combine all signal enhancements into final enhanced signal"""
        try:
            enhanced_signal = base_signal.copy()
            
            # Base signal strength
            base_strength = base_signal.get('deviation', 0.15)
            
            # Multi-timeframe enhancement
            multi_tf_strength = 0.0
            if multi_tf_result and 'signal_strength' in multi_tf_result:
                multi_tf_strength = multi_tf_result['signal_strength']
                confluence_boost = multi_tf_result.get('confluence_score', 0.5) * 0.1
                multi_tf_strength += confluence_boost
            
            # ML enhancement
            ml_strength = ml_result.get('ml_predicted_strength', base_strength) if ml_result else base_strength
            ml_confidence = ml_result.get('confidence', 0.5) if ml_result else 0.5
            
            # Enhanced correlation analysis (NEW 10-pair system)
            enhanced_corr_boost = 0.0
            enhanced_corr_confidence = 0.0
            if enhanced_corr_result:
                strength_multiplier = enhanced_corr_result.get('correlation_strength_multiplier', 1.0)
                enhanced_corr_boost = (strength_multiplier - 1.0) * base_strength  # Convert multiplier to boost
                enhanced_corr_confidence = enhanced_corr_result.get('confidence_boost', 0.0)
            
            # Original correlation pair enhancement (reduced weight)
            correlation_boost = 0.0
            if correlation_result and correlation_result.get('ranked_opportunities'):
                top_opportunity = correlation_result['ranked_opportunities'][0]
                if top_opportunity.get('rank_score', 0) > 0.7:
                    correlation_boost = 0.03  # Reduced from 0.05 as enhanced system is primary
            
            # Calculate weighted final strength (updated with enhanced correlation)
            final_strength = (
                base_strength * 0.1 +  # Base weight reduced
                enhanced_corr_boost * self.enhancement_weights['enhanced_correlation'] +
                multi_tf_strength * self.enhancement_weights['multi_timeframe'] +
                ml_strength * self.enhancement_weights['ml_prediction'] * ml_confidence +
                (base_strength + correlation_boost) * self.enhancement_weights['correlation_pairs']
            )
            
            # Normalize final strength
            final_strength = min(1.0, max(0.0, final_strength))
            
            # Calculate combined confidence (updated with enhanced correlation)
            base_confidence = min(1.0, base_strength * 2)  # Simple confidence from strength
            multi_tf_confidence = multi_tf_result.get('confluence_score', 0.5) if multi_tf_result else 0.5
            
            combined_confidence = (
                base_confidence * 0.2 +  # Reduced base weight
                enhanced_corr_confidence * 0.35 +  # NEW: Enhanced correlation confidence
                multi_tf_confidence * 0.25 +
                ml_confidence * 0.15 +
                min(1.0, correlation_boost * 10) * 0.05  # Original correlation (reduced)
            )
            
            # Update enhanced signal
            enhanced_signal.update({
                'original_strength': base_strength,
                'enhanced_correlation_boost': enhanced_corr_boost,
                'multi_tf_strength': multi_tf_strength,
                'ml_strength': ml_strength,
                'correlation_boost': correlation_boost,
                'final_strength': final_strength,
                'confidence': combined_confidence,
                'enhancement_data': {
                    'enhanced_correlation': enhanced_corr_result,  # NEW: 10-pair correlation data
                    'multi_timeframe': multi_tf_result,
                    'ml_prediction': ml_result,
                    'correlation_analysis': correlation_result
                },
                'enhanced': True,
                'enhancement_timestamp': datetime.now()
            })
            
            return enhanced_signal
            
        except Exception as e:
            logger.error(f"Error combining signal enhancements: {e}")
            return base_signal
    
    def _apply_regime_adjustments(self, signal: Dict, regime_result: Dict) -> Dict:
        """Apply market regime adjustments to enhanced signal"""
        try:
            if not regime_result or 'recommendations' not in regime_result:
                return signal
            
            recommendations = regime_result['recommendations']
            
            # Apply leverage adjustment
            current_leverage = signal.get('suggested_leverage', config.DEFAULT_LEVERAGE)
            leverage_adjustment = recommendations.get('leverage_adjustment', 1.0)
            adjusted_leverage = int(current_leverage * leverage_adjustment)
            adjusted_leverage = max(config.MIN_LEVERAGE, min(config.MAX_LEVERAGE, adjusted_leverage))
            
            # Apply position size adjustment
            current_position_size = signal.get('suggested_position_size', config.RISK_PER_TRADE)
            position_adjustment = recommendations.get('position_size_adjustment', 1.0)
            adjusted_position_size = current_position_size * position_adjustment
            adjusted_position_size = max(0.005, min(0.05, adjusted_position_size))
            
            # Apply risk adjustment
            risk_adjustment = recommendations.get('risk_adjustment', 1.0)
            adjusted_confidence = signal.get('confidence', 0.5) * risk_adjustment
            
            # Update signal with regime adjustments
            signal.update({
                'suggested_leverage': adjusted_leverage,
                'suggested_position_size': adjusted_position_size,
                'confidence': min(1.0, adjusted_confidence),
                'regime_adjustments': {
                    'leverage_factor': leverage_adjustment,
                    'position_size_factor': position_adjustment,
                    'risk_factor': risk_adjustment,
                    'strategy_focus': recommendations.get('strategy_focus', 'balanced')
                },
                'market_regime': regime_result.get('overall_regime', {})
            })
            
            logger.info(f"Applied regime adjustments: leverage={adjusted_leverage}x, "
                       f"position_size={adjusted_position_size:.3f}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error applying regime adjustments: {e}")
            return signal
    
    async def update_optimization_performance(self, trade_result: Dict):
        """Update optimization performance tracking"""
        try:
            # Add performance record to advanced risk manager
            advanced_risk_manager.add_performance_record(trade_result)
            
            # Add training sample to ML predictor
            training_sample = {
                'signal_data': trade_result.get('signal_data', {}),
                'market_data': trade_result.get('market_data', {}),
                'actual_performance': {
                    'profit_pct': trade_result.get('pnl_pct', 0.0),
                    'duration_minutes': trade_result.get('duration_minutes', 120)
                }
            }
            ml_signal_predictor.add_training_sample(training_sample)
            
            logger.info(f"Updated optimization performance tracking for {trade_result.get('symbol')}")
            
        except Exception as e:
            logger.error(f"Error updating optimization performance: {e}")
    
    async def _run_enhanced_correlation_analysis(self, base_signal: Dict, exchange) -> Dict:
        """Run enhanced 10-pair correlation analysis"""
        try:
            if not exchange:
                return {}
                
            logger.info("Running enhanced 10-pair correlation analysis")
            
            # Get enhanced correlation engine
            enhanced_engine = await get_enhanced_correlation_engine(exchange)
            
            # Build correlation matrix
            correlation_matrix = await enhanced_engine.build_correlation_matrix()
            
            if not correlation_matrix:
                return {}
            
            # Generate enhanced correlation signals
            enhanced_signals = await enhanced_engine.generate_enhanced_signals(correlation_matrix)
            
            # Find signals matching our base signal symbol
            primary_symbol = base_signal.get('symbol', '')
            matching_signals = [
                s for s in enhanced_signals 
                if s.primary_pair == primary_symbol or s.reference_pair == primary_symbol
            ]
            
            if matching_signals:
                best_signal = matching_signals[0]  # Highest confidence
                
                return {
                    'correlation_strength_multiplier': best_signal.correlation_strength * 1.5,
                    'confidence_boost': best_signal.confidence_score * 0.3,
                    'cluster_alignment': best_signal.cluster_alignment,
                    'supporting_pairs': best_signal.supporting_pairs,
                    'signal_type': best_signal.signal_type,
                    'expected_move': best_signal.expected_move,
                    'risk_factor': best_signal.risk_factor,
                    'market_regime_factor': best_signal.market_regime_factor,
                    'total_opportunities': len(enhanced_signals),
                    'strong_correlations': correlation_matrix.divergence_opportunities[:3]
                }
            
            # If no direct match, use general correlation strength
            correlation_summary = await enhanced_engine.get_correlation_summary()
            
            return {
                'correlation_strength_multiplier': 1.2,  # General boost for 10-pair system
                'confidence_boost': 0.1,
                'total_pairs_analyzed': correlation_summary.get('total_pairs', 10),
                'divergence_opportunities': correlation_summary.get('divergence_opportunities', 0),
                'market_regime': 'multi_pair_enhanced'
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced correlation analysis: {e}")
            return {}
    
    def get_optimization_status(self) -> Dict:
        """Get current optimization system status"""
        try:
            return {
                'optimization_active': self.optimization_active,
                'enhancement_weights': self.enhancement_weights,
                'enhanced_correlation_status': 'active - 10 pair system',  # NEW
                'multi_timeframe_status': 'active',
                'dynamic_exit_status': 'active',
                'market_regime_status': 'active',
                'advanced_risk_status': 'active',
                'correlation_pairs_status': 'active - legacy support',
                'ml_prediction_status': ml_signal_predictor.get_model_status(),
                'performance_tracking': advanced_risk_manager.get_risk_metrics(),
                'total_trading_pairs': 10,  # Updated count
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting optimization status: {e}")
            return {'optimization_active': False, 'error': str(e)}
    
    def set_optimization_active(self, active: bool):
        """Enable or disable optimization system"""
        self.optimization_active = active
        logger.info(f"Optimization system {'enabled' if active else 'disabled'}")
    
    def update_enhancement_weights(self, new_weights: Dict):
        """Update enhancement weights"""
        try:
            for component, weight in new_weights.items():
                if component in self.enhancement_weights:
                    self.enhancement_weights[component] = max(0.0, min(1.0, weight))
            
            # Normalize weights
            total_weight = sum(self.enhancement_weights.values())
            if total_weight > 0:
                for component in self.enhancement_weights:
                    self.enhancement_weights[component] /= total_weight
            
            logger.info(f"Updated enhancement weights: {self.enhancement_weights}")
            
        except Exception as e:
            logger.error(f"Error updating enhancement weights: {e}")

# Global instance
optimization_integrator = OptimizationIntegrator()