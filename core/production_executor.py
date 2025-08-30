"""Production Executor API - Alias for enhanced backward compatibility"""

try:
    from core.executor import Executor
except ImportError:
    try:
        from .executor import Executor  
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.executor import Executor

# Export for backward compatibility
ProductionExecutor = Executor

# Also export main class
__all__ = ['ProductionExecutor', 'Executor']