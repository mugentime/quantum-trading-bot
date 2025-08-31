#!/usr/bin/env python3
"""
Direct correlation signal verification script
Tests the correlation engine locally with the same fix deployed to Railway
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime
from core.data_collector import DataCollector
from core.correlation_engine import CorrelationEngine
from core.config.settings import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CorrelationTest - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_correlation_signals():
    """Test correlation engine for signal generation"""
    
    logger.info("Testing correlation engine after ConstantInputWarning fix")
    logger.info("Checking for AXSUSDT correlation opportunities...")
    
    # Initialize components
    data_collector = DataCollector(['ETHUSDT', 'AXSUSDT', 'BTCUSDT', 'SOLUSDT', 'LINKUSDT'])
    correlation_engine = CorrelationEngine()
    
    try:
        # Start data collection
        await data_collector.start()
        
        # Wait for initial data
        logger.info("Collecting initial market data...")
        await asyncio.sleep(10)
        
        # Test correlation calculation multiple times
        for i in range(5):
            logger.info(f"Test iteration {i+1}/5")
            
            # Get latest market data
            market_data = await data_collector.get_latest_data()
            logger.info(f"Market data symbols: {list(market_data.keys())}")
            
            # Calculate correlations with the fixed engine
            results = correlation_engine.calculate(market_data)
            
            # Check for signals
            opportunities = results.get('opportunities', [])
            correlations = results.get('correlations', {})
            regime = results.get('regime', 'unknown')
            
            logger.info(f"Market regime: {regime}")
            logger.info(f"Generated {len(opportunities)} correlation opportunities")
            
            if opportunities:
                logger.info("🎯 CORRELATION SIGNALS DETECTED!")
                for opp in opportunities:
                    symbols = opp.get('symbols', [])
                    correlation = opp.get('correlation', 0)
                    confidence = opp.get('confidence', 0)
                    
                    # Check for AXSUSDT specifically
                    axs_involved = 'AXSUSDT' in symbols
                    if axs_involved:
                        logger.info(f"🚀 AXSUSDT OPPORTUNITY: {symbols} - corr: {correlation:.3f}, confidence: {confidence:.3f}")
                    else:
                        logger.info(f"📊 Signal: {symbols} - corr: {correlation:.3f}, confidence: {confidence:.3f}")
            else:
                logger.warning("⚠️  No correlation signals generated")
            
            # Check correlation matrix
            if correlations and 'matrix' in correlations:
                matrix = correlations['matrix']
                logger.info(f"Correlation matrix has {len(matrix)} symbols")
                
                # Log AXSUSDT correlations specifically
                if 'AXSUSDT' in matrix:
                    axs_corrs = matrix['AXSUSDT']
                    logger.info(f"AXSUSDT correlations: {axs_corrs}")
            
            await asyncio.sleep(5)
        
        logger.info("✅ Correlation engine test completed")
        
        if len(opportunities) > 0:
            logger.info("🎉 SUCCESS: Correlation signals are being generated!")
            logger.info("The ConstantInputWarning fix appears to be working correctly")
        else:
            logger.warning("❌ WARNING: No correlation signals generated")
            logger.warning("The correlation engine may still have issues")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    
    finally:
        await data_collector.stop()

if __name__ == "__main__":
    asyncio.run(test_correlation_signals())