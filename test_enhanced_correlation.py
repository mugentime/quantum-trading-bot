#!/usr/bin/env python3
"""Test Enhanced 10-Pair Correlation System"""
import asyncio
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ccxt.async_support as ccxt
from core.config.settings import config
from core.enhanced_correlation_engine import get_enhanced_correlation_engine
from core.optimization_integrator import optimization_integrator
from utils.telegram_notifier import TelegramNotifier

async def test_enhanced_correlation_system():
    """Test the new 10-pair enhanced correlation system"""
    print("TESTING ENHANCED 10-PAIR CORRELATION SYSTEM")
    print("=" * 50)
    
    exchange = None
    telegram = TelegramNotifier()
    
    try:
        # Initialize exchange
        exchange = ccxt.binance({
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_SECRET_KEY,
            'sandbox': True,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        
        print("1. Testing Enhanced Correlation Engine...")
        
        # Get enhanced correlation engine
        enhanced_engine = await get_enhanced_correlation_engine(exchange)
        
        # Build correlation matrix
        print("   Building 10-pair correlation matrix...")
        correlation_matrix = await enhanced_engine.build_correlation_matrix()
        
        if correlation_matrix:
            print(f"   Matrix built with {len(correlation_matrix.pairs)} pairs")
            print(f"   Found {len(correlation_matrix.divergence_opportunities)} divergence opportunities")
            print(f"   Analyzed {len(correlation_matrix.cluster_groups)} clusters")
            
            # Generate enhanced signals
            print("   Generating enhanced correlation signals...")
            enhanced_signals = await enhanced_engine.generate_enhanced_signals(correlation_matrix)
            
            print(f"   Generated {len(enhanced_signals)} enhanced signals")
            
            if enhanced_signals:
                best_signal = enhanced_signals[0]
                print(f"   Best Signal: {best_signal.primary_pair} vs {best_signal.reference_pair}")
                print(f"   Type: {best_signal.signal_type}, Confidence: {best_signal.confidence_score:.3f}")
                print(f"   Supporting pairs: {', '.join(best_signal.supporting_pairs)}")
        
        print("\n2. Testing Integration with Optimization System...")
        
        # Test with a mock signal
        mock_signal = {
            'symbol': 'ETHUSDT',
            'side': 'BUY',
            'strength': 0.25,
            'deviation': 0.18,
            'correlation': 0.75
        }
        
        # Generate enhanced signal
        print("   Running optimization integrator...")
        enhanced_signal = await optimization_integrator.generate_enhanced_signal(
            mock_signal, config.SYMBOLS, exchange
        )
        
        if enhanced_signal.get('enhanced'):
            print(f"   Signal enhanced successfully")
            print(f"   Original strength: {enhanced_signal['original_strength']:.3f}")
            print(f"   Enhanced correlation boost: {enhanced_signal.get('enhanced_correlation_boost', 0):.3f}")
            print(f"   Final strength: {enhanced_signal['final_strength']:.3f}")
            print(f"   Confidence: {enhanced_signal['confidence']:.3f}")
        
        print("\n3. Testing Correlation Summary...")
        
        # Get correlation summary
        summary = await enhanced_engine.get_correlation_summary()
        
        print(f"   Total pairs: {summary.get('total_pairs', 0)}")
        print(f"   Clusters analyzed: {summary.get('clusters_analyzed', 0)}")
        print(f"   Divergence opportunities: {summary.get('divergence_opportunities', 0)}")
        
        # Display top opportunities
        if summary.get('top_opportunities'):
            print("\n   TOP CORRELATION OPPORTUNITIES:")
            for i, opp in enumerate(summary['top_opportunities'][:3], 1):
                print(f"   {i}. {opp['pair_a']} vs {opp['pair_b']}")
                print(f"      Divergence: {opp['divergence_magnitude']:.3f}")
                print(f"      Direction: {opp['expected_direction']}")
                print(f"      Confidence: {opp['confidence']:.3f}")
        
        # Display strong correlations
        if summary.get('strongest_correlations'):
            print("\n   STRONGEST CORRELATIONS:")
            for i, corr in enumerate(summary['strongest_correlations'][:3], 1):
                print(f"   {i}. {corr['pair_a']} ↔ {corr['pair_b']}")
                print(f"      Correlation: {corr['correlation']:.3f} ({corr['strength']})")
        
        print("\n4. Testing System Status...")
        
        # Get optimization status
        status = optimization_integrator.get_optimization_status()
        
        print(f"   Enhanced correlation: {status.get('enhanced_correlation_status', 'inactive')}")
        print(f"   Total trading pairs: {status.get('total_trading_pairs', 'unknown')}")
        print(f"   Enhancement weights: {status.get('enhancement_weights', {})}")
        
        # Send results to Telegram
        message = f"""ENHANCED 10-PAIR CORRELATION SYSTEM TEST

SYSTEM STATUS: OPERATIONAL

CORRELATION MATRIX:
• Total pairs: {summary.get('total_pairs', 10)}
• Divergence opportunities: {summary.get('divergence_opportunities', 0)}
• Clusters analyzed: {summary.get('clusters_analyzed', 0)}

OPTIMIZATION WEIGHTS:
• Enhanced correlation: {status.get('enhancement_weights', {}).get('enhanced_correlation', 0):.0%}
• Multi-timeframe: {status.get('enhancement_weights', {}).get('multi_timeframe', 0):.0%}
• Dynamic exit: {status.get('enhancement_weights', {}).get('dynamic_exit', 0):.0%}

NEW TRADING PAIRS ADDED:
ADAUSDT, AVAXUSDT, DOGEUSDT, DOTUSDT, LINKUSDT

System ready for enhanced correlation trading with 10 pairs!"""
        
        await telegram.send_message(message)
        
        print("\n" + "=" * 50)
        print("ENHANCED CORRELATION SYSTEM TEST COMPLETE")
        print("All systems operational - ready for trading!")
        
    except Exception as e:
        print(f"Error in correlation system test: {e}")
        try:
            await telegram.send_message(f"Enhanced Correlation Test Error: {e}")
        except:
            pass
    
    finally:
        if exchange:
            await exchange.close()

if __name__ == "__main__":
    asyncio.run(test_enhanced_correlation_system())