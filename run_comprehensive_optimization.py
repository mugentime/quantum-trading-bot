#!/usr/bin/env python3
"""
Execute Comprehensive Optimization System
Main entry point for running the complete optimization workflow
"""

import asyncio
import sys
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_requirements():
    """Install required packages"""
    required_packages = [
        'ccxt',
        'pandas', 
        'numpy',
        'python-dotenv',
        'asyncio'
    ]
    
    print("📦 Installing required packages...")
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], 
                                capture_output=True)
            print(f"  ✅ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  {package} installation failed, might already be installed")

def check_environment():
    """Check system environment"""
    print("🔍 Checking system environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 7):
        print(f"❌ Python {python_version.major}.{python_version.minor} detected. Requires Python 3.7+")
        return False
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor} - OK")
    
    # Check required modules
    required_modules = ['ccxt', 'pandas', 'numpy']
    all_available = True
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} - Available")
        except ImportError:
            print(f"❌ {module} - Missing")
            all_available = False
    
    return all_available

async def main():
    """Main execution function"""
    print("=" * 80)
    print("COMPREHENSIVE OPTIMIZATION SYSTEM LAUNCHER")
    print("=" * 80)
    
    # Check environment
    if not check_environment():
        print("Installing missing dependencies...")
        install_requirements()
    
    # Import and run the comprehensive system
    try:
        from comprehensive_optimization_system import ComprehensiveOptimizationSystem
        
        print("\n🚀 Starting Comprehensive Optimization System...")
        system = ComprehensiveOptimizationSystem()
        
        # Execute the full system
        result = await system.run_comprehensive_system()
        
        if result:
            filename, report = result
            print(f"\n🎉 SUCCESS! Complete report saved to: {filename}")
            
            # Display key metrics
            if report and 'optimization_results' in report:
                print("\n📊 FINAL PERFORMANCE SUMMARY:")
                for symbol, results in report['optimization_results'].items():
                    print(f"{symbol}: {results['optimized_return_pct']:+.2f}% return")
                    
            return True
        else:
            print("❌ Optimization system failed to complete")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import optimization system: {e}")
        print("Ensure all files are in the same directory")
        return False
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        logger.error(f"System execution error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Comprehensive optimization completed successfully!")
        print("Check the generated report file for detailed results.")
    else:
        print("\n❌ Optimization failed. Check logs for details.")
        sys.exit(1)