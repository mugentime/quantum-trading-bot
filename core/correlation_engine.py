"""Advanced correlation analysis engine"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
from scipy import stats
from .config.settings import config

logger = logging.getLogger(__name__)

class CorrelationEngine:
    def __init__(self, window_size: int = None):
        """Initialize CorrelationEngine with configurable parameters"""
        self.window_size = window_size or config.CORRELATION_PERIOD
        self.correlation_history = {}
        self.last_correlations = None
        self.price_history = {}
        logger.info("CorrelationEngine initialized")
        
    def calculate(self, market_data: Dict) -> Dict:
        """Calculate correlation metrics from DataCollector format"""
        results = {
            'correlations': {},
            'breakdowns': [],
            'regime': 'neutral',
            'opportunities': [],
            'statistics': {}
        }
        
        try:
            if not market_data:
                return results
            
            # Update price history from DataCollector format
            self._update_price_history(market_data)
            
            # Need at least 2 symbols with sufficient data
            valid_symbols = [symbol for symbol, prices in self.price_history.items() 
                           if len(prices) >= self.window_size]
            
            if len(valid_symbols) < 2:
                logger.debug(f"Insufficient data: {len(valid_symbols)} symbols with {self.window_size}+ points")
                return results
            
            # Build correlation matrix
            corr_matrix, p_values = self._calculate_correlation_matrix(valid_symbols)
            
            if corr_matrix is not None:
                results['correlations']['matrix'] = corr_matrix.to_dict()
                results['statistics']['p_values'] = p_values.to_dict() if p_values is not None else {}
                
                # Detect opportunities and breakdowns
                results['opportunities'] = self._find_opportunities(corr_matrix, p_values, market_data)
                
                if self.last_correlations is not None:
                    results['breakdowns'] = self._detect_breakdowns(corr_matrix, self.last_correlations)
                
                self.last_correlations = corr_matrix
                
                # Determine market regime
                results['regime'] = self._determine_regime(corr_matrix)
                
                # Store correlation history
                self._store_correlation_history(corr_matrix)
                
                logger.debug(f"Calculated correlations for {len(valid_symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error in CorrelationEngine: {e}", exc_info=True)
            
        return results
        
    def _update_price_history(self, market_data: Dict):
        """Update price history from DataCollector market data"""
        for symbol, data in market_data.items():
            if data and 'last' in data and data['last'] is not None:
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                
                # Add new price point
                self.price_history[symbol].append(float(data['last']))
                
                # Keep only window_size + buffer for calculations
                max_history = self.window_size + 50
                if len(self.price_history[symbol]) > max_history:
                    self.price_history[symbol] = self.price_history[symbol][-max_history:]
    
    def _calculate_correlation_matrix(self, symbols: List[str]) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Calculate correlation matrix with statistical significance"""
        try:
            # Build price matrix using last window_size points
            price_matrix = {}
            min_length = float('inf')
            
            for symbol in symbols:
                prices = self.price_history[symbol][-self.window_size:]
                if len(prices) >= self.window_size:
                    price_matrix[symbol] = prices
                    min_length = min(min_length, len(prices))
            
            if len(price_matrix) < 2 or min_length < 10:
                return None, None
            
            # Ensure all series have same length
            for symbol in price_matrix:
                price_matrix[symbol] = price_matrix[symbol][-min_length:]
            
            # Create DataFrame and calculate returns
            df = pd.DataFrame(price_matrix)
            returns = df.pct_change().dropna()
            
            if len(returns) < 5:
                return None, None
            
            # Filter out symbols with constant prices (zero variance)
            valid_symbols_for_returns = []
            for symbol in returns.columns:
                if np.std(returns[symbol]) > 1e-8:  # Not constant
                    valid_symbols_for_returns.append(symbol)
                else:
                    logger.debug(f"Filtering out constant price symbol: {symbol}")
            
            if len(valid_symbols_for_returns) < 2:
                logger.warning("Less than 2 symbols with price movement")
                return None, None
            
            # Keep only symbols with movement
            returns = returns[valid_symbols_for_returns]
            symbols = valid_symbols_for_returns
            
            # Calculate correlation matrix
            corr_matrix = returns.corr()
            
            # Calculate p-values for statistical significance
            p_values = pd.DataFrame(np.ones(corr_matrix.shape), 
                                  index=corr_matrix.index, 
                                  columns=corr_matrix.columns)
            
            for i in range(len(symbols)):
                for j in range(i+1, len(symbols)):
                    symbol1, symbol2 = symbols[i], symbols[j]
                    if symbol1 in returns.columns and symbol2 in returns.columns:
                        try:
                            series1 = returns[symbol1].dropna()
                            series2 = returns[symbol2].dropna()
                            
                            # Check for constant arrays (zero variance)
                            if (len(series1) < 3 or len(series2) < 3 or 
                                np.std(series1) == 0 or np.std(series2) == 0):
                                logger.debug(f"Skipping constant/insufficient data: {symbol1}-{symbol2}")
                                p_values.loc[symbol1, symbol2] = 1.0  # No correlation
                                p_values.loc[symbol2, symbol1] = 1.0
                                corr_matrix.loc[symbol1, symbol2] = 0.0
                                corr_matrix.loc[symbol2, symbol1] = 0.0
                                continue
                            
                            corr, p_val = stats.pearsonr(series1, series2)
                            
                            # Handle NaN results
                            if np.isnan(corr) or np.isnan(p_val):
                                logger.debug(f"NaN correlation result: {symbol1}-{symbol2}")
                                corr, p_val = 0.0, 1.0
                            
                            p_values.loc[symbol1, symbol2] = p_val
                            p_values.loc[symbol2, symbol1] = p_val
                            
                        except Exception as e:
                            logger.warning(f"Correlation error {symbol1}-{symbol2}: {e}")
                            p_values.loc[symbol1, symbol2] = 1.0
                            p_values.loc[symbol2, symbol1] = 1.0
                            corr_matrix.loc[symbol1, symbol2] = 0.0
                            corr_matrix.loc[symbol2, symbol1] = 0.0
            
            return corr_matrix, p_values
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return None, None
    
    def _find_opportunities(self, corr_matrix: pd.DataFrame, p_values: pd.DataFrame, market_data: Dict) -> List[Dict]:
        """Find trading opportunities based on correlation analysis"""
        opportunities = []
        
        try:
            threshold_high = config.DEVIATION_THRESHOLD + 0.65  # ~0.8 for high correlation
            significance_level = 0.05  # 95% confidence
            
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    symbol1 = corr_matrix.columns[i]
                    symbol2 = corr_matrix.columns[j]
                    correlation = corr_matrix.iloc[i, j]
                    p_value = p_values.iloc[i, j] if p_values is not None else 1.0
                    
                    # High correlation opportunity
                    if (abs(correlation) > threshold_high and 
                        p_value < significance_level and 
                        symbol1 in market_data and symbol2 in market_data):
                        
                        # Calculate confidence based on correlation strength and significance
                        confidence = min(abs(correlation) * (1 - p_value), 0.95)
                        
                        # Boost confidence for AXSUSDT pairs (620% monthly target potential)
                        if 'AXSUSDT' in [symbol1, symbol2]:
                            confidence = min(confidence * 1.15, 0.95)  # 15% confidence boost
                        
                        opportunities.append({
                            'type': 'high_correlation' if correlation > 0 else 'negative_correlation',
                            'symbols': [symbol1, symbol2],
                            'correlation': float(correlation),
                            'p_value': float(p_value),
                            'confidence': float(confidence),
                            'significance': 'high' if p_value < 0.01 else 'moderate',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        logger.info(f"OPPORTUNITY: {symbol1}-{symbol2} corr: {correlation:.3f} (p={p_value:.4f})")
                        
        except Exception as e:
            logger.error(f"Error finding opportunities: {e}")
            
        return sorted(opportunities, key=lambda x: x['confidence'], reverse=True)[:5]
    
    def _detect_breakdowns(self, current: pd.DataFrame, previous: pd.DataFrame) -> List[Dict]:
        """Detect significant correlation changes"""
        breakdowns = []
        
        try:
            # Ensure matrices have same symbols
            common_symbols = list(set(current.columns) & set(previous.columns))
            if len(common_symbols) < 2:
                return breakdowns
            
            current_aligned = current.loc[common_symbols, common_symbols]
            previous_aligned = previous.loc[common_symbols, common_symbols]
            
            diff = current_aligned - previous_aligned
            breakdown_threshold = 0.25  # Significant correlation change
            
            for i in range(len(common_symbols)):
                for j in range(i+1, len(common_symbols)):
                    symbol1, symbol2 = common_symbols[i], common_symbols[j]
                    change = diff.iloc[i, j]
                    abs_change = abs(change)
                    
                    if abs_change > breakdown_threshold:
                        prev_corr = previous_aligned.iloc[i, j]
                        curr_corr = current_aligned.iloc[i, j]
                        
                        breakdown_type = 'strengthening' if change > 0 else 'weakening'
                        severity = 'high' if abs_change > 0.4 else 'moderate'
                        
                        breakdowns.append({
                            'pair': f"{symbol1}-{symbol2}",
                            'previous_corr': float(prev_corr),
                            'current_corr': float(curr_corr),
                            'change': float(change),
                            'abs_change': float(abs_change),
                            'type': breakdown_type,
                            'severity': severity,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        logger.info(f"BREAKDOWN: {symbol1}-{symbol2} {breakdown_type} "
                                  f"({prev_corr:.3f} -> {curr_corr:.3f})")
                        
        except Exception as e:
            logger.error(f"Error detecting breakdowns: {e}")
            
        return sorted(breakdowns, key=lambda x: x['abs_change'], reverse=True)
    
    def _determine_regime(self, corr_matrix: pd.DataFrame) -> str:
        """Determine market correlation regime"""
        try:
            # Get upper triangle correlations (excluding diagonal)
            upper_triangle = np.triu(corr_matrix.values, k=1)
            correlations = upper_triangle[upper_triangle != 0]
            
            if len(correlations) == 0:
                return 'insufficient_data'
            
            avg_corr = np.mean(np.abs(correlations))
            
            if avg_corr > 0.7:
                return 'high_correlation'
            elif avg_corr < 0.3:
                return 'low_correlation'
            else:
                return 'mixed_correlation'
                
        except Exception as e:
            logger.error(f"Error determining regime: {e}")
            return 'unknown'
    
    def _store_correlation_history(self, corr_matrix: pd.DataFrame):
        """Store correlation history for trend analysis"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Store average correlations by symbol
            for symbol in corr_matrix.columns:
                if symbol not in self.correlation_history:
                    self.correlation_history[symbol] = []
                
                # Calculate average correlation with other symbols
                other_corrs = [abs(corr_matrix.loc[symbol, other]) 
                             for other in corr_matrix.columns if other != symbol]
                avg_corr = np.mean(other_corrs) if other_corrs else 0.0
                
                self.correlation_history[symbol].append({
                    'timestamp': timestamp,
                    'avg_correlation': float(avg_corr)
                })
                
                # Keep last 100 records for efficiency
                if len(self.correlation_history[symbol]) > 100:
                    self.correlation_history[symbol] = self.correlation_history[symbol][-100:]
                    
        except Exception as e:
            logger.error(f"Error storing correlation history: {e}")
    
    def get_correlation_trend(self, symbol: str, periods: int = 10) -> Optional[str]:
        """Get correlation trend for a symbol"""
        try:
            if symbol not in self.correlation_history:
                return None
            
            history = self.correlation_history[symbol]
            if len(history) < periods:
                return None
            
            recent_corrs = [h['avg_correlation'] for h in history[-periods:]]
            
            # Simple trend analysis
            if len(recent_corrs) >= 2:
                trend_slope = (recent_corrs[-1] - recent_corrs[0]) / len(recent_corrs)
                
                if trend_slope > 0.02:
                    return 'increasing'
                elif trend_slope < -0.02:
                    return 'decreasing'
                else:
                    return 'stable'
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating correlation trend: {e}")
            return None
