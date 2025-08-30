"""Performance tracking module"""
from typing import Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceTracker:
    def __init__(self):
        self.trades = []
        logger.info("PerformanceTracker inicializado")
        
    def record_trade(self, trade: Dict):
        """Record trade result"""
        self.trades.append(trade)
        
    def save_report(self):
        """Save performance report"""
        logger.info(f"Guardando reporte de {len(self.trades)} trades")
        
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            'total_trades': len(self.trades),
            'win_rate': 0.0,
            'pnl': 0.0
        }
