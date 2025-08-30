#!/usr/bin/env python3
"""
Live vs Backtest Comparison System
Compares real trading performance with backtesting predictions
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging
import os

from utils.logger import setup_logger

logger = setup_logger('comparison')

@dataclass
class ComparisonMetrics:
    """Comparison metrics between backtest and live results"""
    symbol: str
    backtest_return_pct: float
    live_return_pct: float
    return_difference_pct: float
    return_accuracy_score: float
    backtest_win_rate: float
    live_win_rate: float
    win_rate_difference: float
    backtest_sharpe: float
    live_sharpe: float
    sharpe_difference: float
    backtest_trades: int
    live_trades: int
    trade_frequency_ratio: float
    reliability_score: float
    overfitting_risk: str

@dataclass
class LiveTestingSession:
    """Live testing session data"""
    start_time: str
    duration_hours: float
    pairs_tested: List[str]
    total_trades: int
    total_return_pct: float
    trades: List[Dict]
    session_id: str

class LiveVsBacktestComparison:
    """Compare live testing results with backtesting predictions"""
    
    def __init__(self):
        self.comparison_threshold = 15.0  # 15% acceptable variance
        logger.info("Live vs Backtest comparison system initialized")
    
    def load_backtest_results(self, backtest_file: str) -> Optional[Dict]:
        """Load backtest results from JSON file"""
        try:
            with open(backtest_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded backtest results from {backtest_file}")
            return data
        except Exception as e:
            logger.error(f"Failed to load backtest results: {e}")
            return None
    
    def load_live_results(self, live_file: str = "testnet_progress_20250829.json") -> Optional[Dict]:
        """Load live testing results"""
        try:
            with open(live_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded live results from {live_file}")
            return data
        except Exception as e:
            logger.error(f"Failed to load live results: {e}")
            return None
    
    def extract_live_session(self, live_data: Dict, session_duration_hours: float = 24) -> LiveTestingSession:
        """Extract live testing session data"""
        try:
            start_time = live_data.get('start_time', datetime.now().isoformat())
            
            # Get trades from the session
            completed_trades = live_data.get('completed_trades', [])
            active_positions = live_data.get('active_positions', {})
            
            # Calculate session metrics
            session_start = datetime.fromisoformat(start_time)
            session_trades = []
            
            # Filter trades within session timeframe
            for trade in completed_trades:
                trade_time = datetime.fromisoformat(trade.get('exit_time', trade.get('entry_time', start_time)))
                if trade_time >= session_start:
                    session_trades.append(trade)
            
            # Add active positions as ongoing trades
            for symbol, position in active_positions.items():
                position_dict = dict(position)
                position_dict['status'] = 'active'
                session_trades.append(position_dict)
            
            # Calculate returns
            total_pnl = sum([trade.get('pnl_usd', 0) for trade in session_trades if 'pnl_usd' in trade])
            initial_balance = live_data.get('initial_balance', 10000)
            total_return_pct = (total_pnl / initial_balance) * 100
            
            # Get unique pairs
            pairs_tested = list(set([trade.get('symbol', 'UNKNOWN') for trade in session_trades]))
            
            session = LiveTestingSession(
                start_time=start_time,
                duration_hours=session_duration_hours,
                pairs_tested=pairs_tested,
                total_trades=len(session_trades),
                total_return_pct=total_return_pct,
                trades=session_trades,
                session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            logger.info(f"Extracted live session: {len(session_trades)} trades, {total_return_pct:.2f}% return")
            return session
            
        except Exception as e:
            logger.error(f"Failed to extract live session: {e}")
            return None
    
    def calculate_pair_comparison(self, symbol: str, backtest_data: Dict, live_session: LiveTestingSession) -> ComparisonMetrics:
        """Calculate comparison metrics for a specific pair"""
        try:
            # Get backtest metrics
            backtest_pair = backtest_data.get('detailed_results', {}).get(symbol, {})
            backtest_metrics = backtest_pair.get('performance_metrics', {})
            
            # Get live metrics for this pair
            live_trades = [t for t in live_session.trades if t.get('symbol') == symbol]
            
            if not live_trades:
                logger.warning(f"No live trades found for {symbol}")
                live_return_pct = 0
                live_win_rate = 0
                live_sharpe = 0
                live_trades_count = 0
            else:
                # Calculate live performance
                live_pnls = [t.get('pnl_pct', 0) for t in live_trades if 'pnl_pct' in t]
                live_return_pct = sum(live_pnls)
                live_win_rate = (len([p for p in live_pnls if p > 0]) / len(live_pnls)) * 100 if live_pnls else 0
                live_sharpe = (np.mean(live_pnls) / np.std(live_pnls)) if len(live_pnls) > 1 and np.std(live_pnls) > 0 else 0
                live_trades_count = len(live_trades)
            
            # Get backtest metrics
            backtest_return_pct = backtest_metrics.get('total_return_pct', 0)
            backtest_win_rate = backtest_metrics.get('win_rate_pct', 0)
            backtest_sharpe = backtest_metrics.get('sharpe_ratio', 0)
            backtest_trades_count = backtest_metrics.get('total_trades', 0)
            
            # Calculate differences
            return_difference = abs(live_return_pct - backtest_return_pct)
            win_rate_difference = abs(live_win_rate - backtest_win_rate)
            sharpe_difference = abs(live_sharpe - backtest_sharpe)
            
            # Calculate accuracy score (0-100, higher is better)
            if backtest_return_pct != 0:
                return_accuracy = max(0, 100 - (return_difference / abs(backtest_return_pct)) * 100)
            else:
                return_accuracy = 100 if live_return_pct == 0 else 0
            
            # Calculate trade frequency ratio
            if backtest_trades_count > 0:
                # Normalize for time period (backtest = 30 days, live = 1 day)
                expected_live_trades = backtest_trades_count / 30
                trade_frequency_ratio = live_trades_count / expected_live_trades if expected_live_trades > 0 else 0
            else:
                trade_frequency_ratio = 0
            
            # Calculate overall reliability score
            reliability_components = [
                return_accuracy,
                max(0, 100 - win_rate_difference * 2),  # Win rate accuracy
                max(0, 100 - sharpe_difference * 10),  # Sharpe accuracy (scaled)
                min(100, trade_frequency_ratio * 50)   # Trade frequency consistency
            ]
            reliability_score = np.mean(reliability_components)
            
            # Determine overfitting risk
            if return_difference > self.comparison_threshold:
                if live_return_pct < backtest_return_pct:
                    overfitting_risk = "HIGH - Live performance significantly lower"
                else:
                    overfitting_risk = "MEDIUM - Live performance exceeds backtest"
            elif return_difference > self.comparison_threshold / 2:
                overfitting_risk = "MEDIUM - Moderate variance from backtest"
            else:
                overfitting_risk = "LOW - Good alignment with backtest"
            
            comparison = ComparisonMetrics(
                symbol=symbol,
                backtest_return_pct=round(backtest_return_pct, 2),
                live_return_pct=round(live_return_pct, 2),
                return_difference_pct=round(return_difference, 2),
                return_accuracy_score=round(return_accuracy, 1),
                backtest_win_rate=round(backtest_win_rate, 1),
                live_win_rate=round(live_win_rate, 1),
                win_rate_difference=round(win_rate_difference, 1),
                backtest_sharpe=round(backtest_sharpe, 2),
                live_sharpe=round(live_sharpe, 2),
                sharpe_difference=round(sharpe_difference, 2),
                backtest_trades=backtest_trades_count,
                live_trades=live_trades_count,
                trade_frequency_ratio=round(trade_frequency_ratio, 2),
                reliability_score=round(reliability_score, 1),
                overfitting_risk=overfitting_risk
            )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to calculate comparison for {symbol}: {e}")
            return None
    
    def generate_comprehensive_comparison(self, backtest_file: str, live_file: str = None) -> Dict:
        """Generate comprehensive comparison report"""
        logger.info("Generating comprehensive comparison report")
        
        # Load data
        backtest_data = self.load_backtest_results(backtest_file)
        if not backtest_data:
            return {"error": "Failed to load backtest data"}
        
        live_data = self.load_live_results(live_file) if live_file else self.load_live_results()
        if not live_data:
            return {"error": "Failed to load live data"}
        
        # Extract live session
        live_session = self.extract_live_session(live_data)
        if not live_session:
            return {"error": "Failed to extract live session"}
        
        # Get all pairs from backtest
        backtest_pairs = list(backtest_data.get('detailed_results', {}).keys())
        
        # Calculate comparisons for each pair
        pair_comparisons = {}
        for symbol in backtest_pairs:
            comparison = self.calculate_pair_comparison(symbol, backtest_data, live_session)
            if comparison:
                pair_comparisons[symbol] = comparison
        
        # Calculate overall metrics
        if pair_comparisons:
            avg_accuracy = np.mean([c.return_accuracy_score for c in pair_comparisons.values()])
            avg_reliability = np.mean([c.reliability_score for c in pair_comparisons.values()])
            high_risk_pairs = len([c for c in pair_comparisons.values() if "HIGH" in c.overfitting_risk])
            
            # Rank pairs by reliability
            ranked_pairs = sorted(pair_comparisons.items(), key=lambda x: x[1].reliability_score, reverse=True)
            
        else:
            avg_accuracy = 0
            avg_reliability = 0
            high_risk_pairs = 0
            ranked_pairs = []
        
        # Generate report
        report = {
            "comparison_summary": {
                "backtest_file": backtest_file,
                "live_session_id": live_session.session_id,
                "live_session_duration_hours": live_session.duration_hours,
                "pairs_analyzed": len(pair_comparisons),
                "average_accuracy_score": round(avg_accuracy, 1),
                "average_reliability_score": round(avg_reliability, 1),
                "high_overfitting_risk_pairs": high_risk_pairs,
                "comparison_threshold_pct": self.comparison_threshold,
                "generated_at": datetime.now().isoformat()
            },
            "live_session_summary": asdict(live_session),
            "pair_reliability_ranking": [
                {
                    "rank": i + 1,
                    "symbol": symbol,
                    "reliability_score": comp.reliability_score,
                    "return_accuracy": comp.return_accuracy_score,
                    "overfitting_risk": comp.overfitting_risk,
                    "live_return_pct": comp.live_return_pct,
                    "backtest_return_pct": comp.backtest_return_pct
                }
                for i, (symbol, comp) in enumerate(ranked_pairs)
            ],
            "detailed_comparisons": {
                symbol: asdict(comparison)
                for symbol, comparison in pair_comparisons.items()
            },
            "recommendations": self.generate_recommendations(pair_comparisons, avg_reliability)
        }
        
        return report
    
    def generate_recommendations(self, comparisons: Dict, avg_reliability: float) -> List[str]:
        """Generate trading recommendations based on comparison analysis"""
        recommendations = []
        
        if avg_reliability >= 80:
            recommendations.append("EXCELLENT: High reliability across pairs. Strategy is well-calibrated for live trading.")
        elif avg_reliability >= 60:
            recommendations.append("GOOD: Moderate reliability. Consider focusing on top-performing pairs.")
        else:
            recommendations.append("WARNING: Low reliability detected. Strategy may need recalibration.")
        
        # Identify best and worst performers
        if comparisons:
            best_pair = max(comparisons.items(), key=lambda x: x[1].reliability_score)
            worst_pair = min(comparisons.items(), key=lambda x: x[1].reliability_score)
            
            recommendations.append(f"BEST PERFORMER: {best_pair[0]} with {best_pair[1].reliability_score:.1f}% reliability")
            recommendations.append(f"NEEDS ATTENTION: {worst_pair[0]} with {worst_pair[1].reliability_score:.1f}% reliability")
            
            # High-risk pairs
            high_risk = [symbol for symbol, comp in comparisons.items() if "HIGH" in comp.overfitting_risk]
            if high_risk:
                recommendations.append(f"HIGH OVERFITTING RISK: {', '.join(high_risk)} - Consider excluding from live trading")
            
            # Low-risk, high-performance pairs
            reliable_pairs = [symbol for symbol, comp in comparisons.items() if comp.reliability_score >= 75 and "LOW" in comp.overfitting_risk]
            if reliable_pairs:
                recommendations.append(f"RECOMMENDED FOR LIVE TRADING: {', '.join(reliable_pairs)}")
        
        return recommendations

def main():
    """Main function for testing"""
    comparison = LiveVsBacktestComparison()
    
    # Look for recent backtest files
    import glob
    backtest_files = glob.glob("simple_comprehensive_backtest_*.json")
    if not backtest_files:
        backtest_files = glob.glob("comprehensive_backtest_*.json")
    
    if not backtest_files:
        print("No backtest files found. Please run backtesting first.")
        return
    
    latest_backtest = max(backtest_files, key=os.path.getctime)
    print(f"Using latest backtest file: {latest_backtest}")
    
    # Generate comparison
    report = comparison.generate_comprehensive_comparison(latest_backtest)
    
    if "error" in report:
        print(f"ERROR: {report['error']}")
        return
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"backtest_vs_live_comparison_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Comparison report saved to: {report_file}")
    
    # Display summary
    summary = report['comparison_summary']
    print(f"\nCOMPARISON SUMMARY:")
    print(f"Average Accuracy: {summary['average_accuracy_score']:.1f}%")
    print(f"Average Reliability: {summary['average_reliability_score']:.1f}%")
    print(f"High Risk Pairs: {summary['high_overfitting_risk_pairs']}")
    
    print("\nRECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"- {rec}")

if __name__ == "__main__":
    main()