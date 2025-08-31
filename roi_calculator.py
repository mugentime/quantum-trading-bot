#!/usr/bin/env python3
"""
ROI Calculator for Quantum Trading Bot
Calculates expected compound ROI based on backtesting and forward testing data
"""

import json
import math
from datetime import datetime, timedelta

class ROICalculator:
    def __init__(self):
        self.backtest_data = {}
        self.live_data = {}
        
    def load_backtest_results(self):
        """Load backtesting results"""
        try:
            # Load optimized backtest results  
            with open('optimized_backtest_results.json', 'r') as f:
                data = json.load(f)
                if 'SOL_30d' in data:
                    sol_data = data['SOL_30d']
                    self.backtest_data['sol'] = {
                        'return_pct': sol_data['total_return_pct'],
                        'trades': sol_data['total_trades'],
                        'win_rate': sol_data['win_rate'],
                        'avg_leverage': sol_data['avg_leverage_used'],
                        'sharpe': sol_data['sharpe_ratio'],
                        'max_drawdown': sol_data['max_drawdown'],
                        'period_days': sol_data['period_days']
                    }
            
            # Load comprehensive report data
            comprehensive_data = {
                'eth_return': 0.48,  # ETHUSDT +0.48% (30-day backtest)
                'overall_return': 0.11,  # Overall +0.11% (30-day backtest)  
                'win_rate': 45.11,  # 45.11% overall win rate
                'total_trades': 113,  # 113 total trades
                'sharpe': 0.1144,  # Overall Sharpe ratio
                'max_drawdown': 0.18  # Max drawdown
            }
            self.backtest_data['comprehensive'] = comprehensive_data
            
            return True
        except Exception as e:
            print(f"Error loading backtest data: {e}")
            return False
    
    def load_live_performance(self):
        """Load current live performance"""
        try:
            with open('live_performance_report_20250830_183409.json', 'r') as f:
                data = json.load(f)
                perf = data['performance_summary']
                self.live_data = {
                    'current_pnl': perf['total_pnl_usd'],
                    'start_balance': perf['start_balance'], 
                    'positions': perf['current_positions'],
                    'time_hours': 6,  # Approximately 6 hours running
                    'realized_pnl': perf.get('realized_pnl', 0),
                    'unrealized_pnl': perf['unrealized_pnl']
                }
            return True
        except Exception as e:
            print(f"Error loading live data: {e}")
            return False
    
    def calculate_base_daily_roi(self):
        """Calculate base daily ROI from different data sources"""
        results = {}
        
        # From SOL 30-day optimized backtest
        if 'sol' in self.backtest_data:
            sol = self.backtest_data['sol']
            monthly_return = sol['return_pct'] / 100  # 20.42% = 0.2042
            daily_return = ((1 + monthly_return) ** (1/30)) - 1
            results['sol_backtest'] = daily_return * 100
        
        # From comprehensive backtesting
        if 'comprehensive' in self.backtest_data:
            comp = self.backtest_data['comprehensive']
            # ETHUSDT performed best at +0.48% over 30 days
            eth_monthly = comp['eth_return'] / 100  # 0.48% = 0.0048
            eth_daily = ((1 + eth_monthly) ** (1/30)) - 1
            results['eth_backtest'] = eth_daily * 100
            
            # Overall performance
            overall_monthly = comp['overall_return'] / 100  # 0.11% = 0.0011  
            overall_daily = ((1 + overall_monthly) ** (1/30)) - 1
            results['overall_backtest'] = overall_daily * 100
        
        # From current live performance
        if self.live_data:
            live = self.live_data
            hourly_return = (live['current_pnl'] / live['start_balance']) / live['time_hours']
            daily_return = hourly_return * 24
            results['current_live'] = daily_return * 100
        
        return results
    
    def calculate_high_frequency_multiplier(self):
        """Calculate improvement factor from high-frequency scalping"""
        
        # High-frequency improvements:
        # 1. Faster signal detection (30-second intervals vs 5-minute)
        # 2. Lower deviation threshold (0.08 vs 0.15) = 87.5% more signals  
        # 3. Tighter stop/profit (1.2%/1.8% vs 2%/4%) = Better risk/reward
        # 4. Multiple concurrent positions (up to 5 vs 1-2)
        # 5. Focus on best performer (ETHUSDT) vs diversified
        
        signal_frequency_multiplier = 10  # 30-second vs 5-minute intervals
        threshold_multiplier = 1.875  # 87.5% more signals from lower threshold
        position_multiplier = 2.5  # Up to 5 positions vs 2 average
        focus_multiplier = 1.5  # Focus on ETHUSDT (best performer) vs diversified
        
        # Conservative estimate (not all multipliers stack linearly)
        base_improvement = 1.0
        base_improvement *= min(signal_frequency_multiplier, 3.0)  # Cap at 3x
        base_improvement *= min(threshold_multiplier, 1.5)  # Cap at 1.5x
        base_improvement *= min(position_multiplier, 2.0)  # Cap at 2x  
        base_improvement *= min(focus_multiplier, 1.3)  # Cap at 1.3x
        
        # Apply diminishing returns
        total_multiplier = math.sqrt(base_improvement)  # Square root for realism
        
        return min(total_multiplier, 5.0)  # Cap at 5x improvement maximum
    
    def calculate_compound_projections(self, daily_roi_pct, days=30):
        """Calculate compound growth projections"""
        daily_multiplier = 1 + (daily_roi_pct / 100)
        
        projections = {}
        for period in [7, 14, 21, 30]:
            if period <= days:
                compound_growth = (daily_multiplier ** period) - 1
                projections[f'{period}_days'] = compound_growth * 100
        
        return projections
    
    def generate_roi_forecast(self):
        """Generate comprehensive ROI forecast"""
        print("="*60)
        print("QUANTUM TRADING BOT - 30-DAY ROI FORECAST")  
        print("="*60)
        
        # Load data
        backtest_loaded = self.load_backtest_results()
        live_loaded = self.load_live_performance()
        
        if not (backtest_loaded and live_loaded):
            print("⚠️  Warning: Some data could not be loaded")
        
        # Calculate base daily ROI from different sources
        daily_rois = self.calculate_base_daily_roi()
        
        print("\nBASE DAILY ROI CALCULATIONS:")
        print("-" * 40)
        for source, roi in daily_rois.items():
            print(f"{source:20}: {roi:+.4f}% per day")
        
        # Calculate high-frequency scalping improvements
        hf_multiplier = self.calculate_high_frequency_multiplier()
        print(f"\nHIGH-FREQUENCY IMPROVEMENT FACTOR: {hf_multiplier:.2f}x")
        
        # Apply improvements to best performing scenarios
        improved_rois = {}
        
        # Use SOL backtest as base (strongest performance) + HF improvements
        if 'sol_backtest' in daily_rois:
            base_roi = daily_rois['sol_backtest']
            improved_rois['optimistic'] = base_roi * hf_multiplier
        
        # Use ETHUSDT backtest + HF improvements (more conservative)
        if 'eth_backtest' in daily_rois:
            base_roi = daily_rois['eth_backtest'] 
            improved_rois['realistic'] = base_roi * (hf_multiplier * 0.7)  # 70% of full improvement
        
        # Use current live performance + moderate improvements
        if 'current_live' in daily_rois:
            base_roi = daily_rois['current_live']
            improved_rois['conservative'] = base_roi * (hf_multiplier * 0.3)  # 30% of full improvement
        
        # Generate projections for each scenario
        print("\n30-DAY COMPOUND ROI PROJECTIONS:")
        print("-" * 50)
        
        scenarios = []
        
        for scenario, daily_roi in improved_rois.items():
            projections = self.calculate_compound_projections(daily_roi, 30)
            
            scenario_data = {
                'name': scenario.upper(),
                'daily_roi': daily_roi,
                'weekly': projections.get('7_days', 0),
                'biweekly': projections.get('14_days', 0), 
                'monthly': projections.get('30_days', 0)
            }
            scenarios.append(scenario_data)
            
            print(f"\n{scenario.upper()} SCENARIO:")
            print(f"  Daily ROI: {daily_roi:+.4f}%")
            print(f"  7-day:     {projections.get('7_days', 0):+.2f}%")
            print(f"  14-day:    {projections.get('14_days', 0):+.2f}%") 
            print(f"  30-day:    {projections.get('30_days', 0):+.2f}%")
        
        # Calculate expected range
        if scenarios:
            monthly_returns = [s['monthly'] for s in scenarios]
            min_return = min(monthly_returns)
            max_return = max(monthly_returns)
            avg_return = sum(monthly_returns) / len(monthly_returns)
            
            print("\n" + "="*50)
            print("EXPECTED 30-DAY ROI RANGE:")
            print("="*50)
            print(f"Conservative: {min_return:+.2f}%")
            print(f"Expected:     {avg_return:+.2f}%") 
            print(f"Optimistic:   {max_return:+.2f}%")
            
            # Calculate dollar projections based on current balance
            if self.live_data:
                balance = self.live_data['start_balance']
                print(f"\nDOLLAR PROJECTIONS (${balance:,.2f} balance):")
                print(f"Conservative: ${balance * (min_return/100):,.2f}")
                print(f"Expected:     ${balance * (avg_return/100):,.2f}")
                print(f"Optimistic:   ${balance * (max_return/100):,.2f}")
        
        print("\n" + "="*60)
        print("DISCLAIMER: Past performance does not guarantee future results")
        print("Projections based on backtesting + live performance + HF optimization")
        print("="*60)

if __name__ == "__main__":
    calculator = ROICalculator()
    calculator.generate_roi_forecast()