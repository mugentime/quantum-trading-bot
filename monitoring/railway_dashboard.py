#!/usr/bin/env python3
"""
Railway Trading Bot Interactive Dashboard
Real-time status dashboard with rich terminal UI
"""
import asyncio
import aiohttp
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import time

# Rich terminal UI imports
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.text import Text
    from rich.live import Live
    from rich.layout import Layout
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger_config import setup_logger

# Set up logging
logger = setup_logger("RailwayDashboard", level=logging.INFO)

class RailwayDashboard:
    """Interactive dashboard for Railway bot monitoring"""
    
    def __init__(self, railway_url: str = "https://railway-up-production-f151.up.railway.app"):
        """Initialize the Railway dashboard"""
        self.railway_url = railway_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.console = Console() if RICH_AVAILABLE else None
        
        # Dashboard state
        self.running = False
        self.last_update = None
        self.update_interval = 5  # seconds
        
        # Data storage
        self.health_data = {}
        self.trading_data = {}
        self.performance_data = {}
        self.system_data = {}
        
        # Performance history for charts
        self.performance_history = []
        self.max_history = 50
        
        if not RICH_AVAILABLE:
            logger.warning("Rich library not available. Install with: pip install rich")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5),
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def start_dashboard(self):
        """Start the interactive dashboard"""
        if not RICH_AVAILABLE:
            await self._start_simple_dashboard()
            return
        
        logger.info("🚀 Starting Railway Bot Dashboard...")
        self.running = True
        
        try:
            # Create layout
            layout = self._create_layout()
            
            # Start live dashboard
            with Live(layout, refresh_per_second=0.5, screen=True) as live:
                while self.running:
                    try:
                        # Update all data
                        await self._update_all_data()
                        
                        # Update layout with fresh data
                        layout = self._create_layout()
                        live.update(layout)
                        
                        # Wait for next update
                        await asyncio.sleep(self.update_interval)
                        
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        logger.error(f"Dashboard update error: {e}")
                        await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        finally:
            self.running = False
    
    async def _start_simple_dashboard(self):
        """Start simple text-based dashboard when Rich is not available"""
        logger.info("Starting simple text dashboard...")
        self.running = True
        
        try:
            while self.running:
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Update data
                await self._update_all_data()
                
                # Display simple dashboard
                self._display_simple_dashboard()
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            print("\nDashboard stopped by user")
        finally:
            self.running = False
    
    def _create_layout(self) -> Layout:
        """Create Rich layout for dashboard"""
        layout = Layout()
        
        # Main layout structure
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Split body into sections
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Split left side
        layout["left"].split_column(
            Layout(name="health", size=12),
            Layout(name="trading", size=12),
        )
        
        # Split right side
        layout["right"].split_column(
            Layout(name="performance", size=12),
            Layout(name="system", size=12),
        )
        
        # Update each section
        layout["header"].update(self._create_header())
        layout["health"].update(self._create_health_panel())
        layout["trading"].update(self._create_trading_panel())
        layout["performance"].update(self._create_performance_panel())
        layout["system"].update(self._create_system_panel())
        layout["footer"].update(self._create_footer())
        
        return layout
    
    def _create_header(self) -> Panel:
        """Create header panel"""
        title_text = Text("🚀 Railway Trading Bot Dashboard", style="bold blue")
        subtitle_text = Text(f"Monitoring: {self.railway_url}", style="dim")
        timestamp_text = Text(f"Last Update: {self.last_update or 'Never'}", style="dim")
        
        header_content = Text()
        header_content.append(title_text)
        header_content.append("\n")
        header_content.append(subtitle_text)
        header_content.append(" | ")
        header_content.append(timestamp_text)
        
        return Panel(header_content, box=box.ROUNDED)
    
    def _create_health_panel(self) -> Panel:
        """Create health status panel"""
        if not self.health_data:
            return Panel(Text("Loading health data...", style="yellow"), 
                        title="🏥 Health Status", box=box.ROUNDED)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Endpoint", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Response Time", justify="right")
        
        overall_status = self.health_data.get('overall_healthy', False)
        status_color = "green" if overall_status else "red"
        status_text = "✅ HEALTHY" if overall_status else "❌ UNHEALTHY"
        
        for name, data in self.health_data.get('endpoints', {}).items():
            success = data.get('success', False)
            status_icon = "✅" if success else "❌"
            response_time = data.get('response_time', 'N/A')
            
            table.add_row(
                name.replace('_', ' ').title(),
                status_icon,
                str(response_time)
            )
        
        title = f"🏥 Health Status - [{status_color}]{status_text}[/{status_color}]"
        return Panel(table, title=title, box=box.ROUNDED)
    
    def _create_trading_panel(self) -> Panel:
        """Create trading activity panel"""
        if not self.trading_data:
            return Panel(Text("Loading trading data...", style="yellow"),
                        title="📈 Trading Activity", box=box.ROUNDED)
        
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white", justify="right")
        
        # Extract trading metrics
        metrics = [
            ("Total Trades", self.trading_data.get('total_trades', 0)),
            ("Active Positions", self.trading_data.get('active_positions', 0)),
            ("Success Rate", f"{self.trading_data.get('success_rate', 0) * 100:.1f}%"),
            ("Total P&L", f"{self.trading_data.get('total_pnl', 0) * 100:.2f}%"),
            ("Daily Target", f"{self.trading_data.get('daily_target_progress', 0) * 100:.1f}%"),
            ("Win Streak", self.trading_data.get('win_streak', 0)),
            ("Last Trade", self.trading_data.get('last_trade_time', 'N/A'))
        ]
        
        for metric, value in metrics:
            # Color coding for values
            if metric == "Success Rate":
                rate = float(str(value).replace('%', ''))
                color = "green" if rate >= 60 else "yellow" if rate >= 40 else "red"
                value = f"[{color}]{value}[/{color}]"
            elif metric == "Total P&L":
                pnl = float(str(value).replace('%', ''))
                color = "green" if pnl >= 0 else "red"
                value = f"[{color}]{value}[/{color}]"
            
            table.add_row(metric, str(value))
        
        return Panel(table, title="📈 Trading Activity", box=box.ROUNDED)
    
    def _create_performance_panel(self) -> Panel:
        """Create performance metrics panel"""
        if not self.performance_data:
            return Panel(Text("Loading performance data...", style="yellow"),
                        title="⚡ Performance Metrics", box=box.ROUNDED)
        
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white", justify="right")
        
        # Extract performance metrics
        metrics = [
            ("Memory Usage", f"{self.performance_data.get('memory_usage_percent', 0):.1f}%"),
            ("CPU Usage", f"{self.performance_data.get('cpu_usage_percent', 0):.1f}%"),
            ("Avg Response Time", f"{self.performance_data.get('average_response_time', 0):.0f}ms"),
            ("Request Count", self.performance_data.get('total_requests', 0)),
            ("Error Rate", f"{self.performance_data.get('error_rate', 0):.1f}%"),
            ("Uptime", self.performance_data.get('uptime_hours', 0)),
            ("Restart Count", self.performance_data.get('restart_count', 0))
        ]
        
        for metric, value in metrics:
            # Color coding for critical values
            if metric == "Memory Usage":
                usage = float(str(value).replace('%', ''))
                color = "red" if usage >= 90 else "yellow" if usage >= 75 else "green"
                value = f"[{color}]{value}[/{color}]"
            elif metric == "Error Rate":
                rate = float(str(value).replace('%', ''))
                color = "red" if rate >= 5 else "yellow" if rate >= 2 else "green"
                value = f"[{color}]{value}[/{color}]"
            
            table.add_row(metric, str(value))
        
        return Panel(table, title="⚡ Performance Metrics", box=box.ROUNDED)
    
    def _create_system_panel(self) -> Panel:
        """Create system status panel"""
        if not self.system_data:
            return Panel(Text("Loading system data...", style="yellow"),
                        title="🖥️ System Status", box=box.ROUNDED)
        
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white", justify="right")
        
        # System components status
        components = [
            ("Bot Process", "🟢 Running" if self.system_data.get('bot_running') else "🔴 Stopped"),
            ("Database", "🟢 Connected" if self.system_data.get('db_connected') else "🔴 Disconnected"),
            ("Exchange API", "🟢 Connected" if self.system_data.get('exchange_connected') else "🔴 Disconnected"),
            ("Telegram Bot", "🟢 Active" if self.system_data.get('telegram_active') else "🔴 Inactive"),
            ("Risk Manager", "🟢 Normal" if not self.system_data.get('emergency_mode') else "🔴 Emergency"),
            ("Data Collector", "🟢 Active" if self.system_data.get('data_collector_active') else "🔴 Inactive"),
            ("Signal Generator", "🟢 Active" if self.system_data.get('signal_generator_active') else "🔴 Inactive")
        ]
        
        for component, status in components:
            table.add_row(component, status)
        
        return Panel(table, title="🖥️ System Status", box=box.ROUNDED)
    
    def _create_footer(self) -> Panel:
        """Create footer panel"""
        footer_text = Text()
        footer_text.append("Press ", style="dim")
        footer_text.append("Ctrl+C", style="bold red")
        footer_text.append(" to exit | Updates every ", style="dim")
        footer_text.append(f"{self.update_interval}s", style="bold cyan")
        footer_text.append(" | Railway Bot Monitor v1.0", style="dim")
        
        return Panel(footer_text, box=box.ROUNDED)
    
    def _display_simple_dashboard(self):
        """Display simple text-based dashboard"""
        print("=" * 80)
        print("🚀 RAILWAY TRADING BOT DASHBOARD")
        print(f"Monitoring: {self.railway_url}")
        print(f"Last Update: {self.last_update or 'Never'}")
        print("=" * 80)
        
        # Health Status
        print("\n🏥 HEALTH STATUS:")
        if self.health_data:
            overall = "HEALTHY ✅" if self.health_data.get('overall_healthy') else "UNHEALTHY ❌"
            print(f"  Overall: {overall}")
            for name, data in self.health_data.get('endpoints', {}).items():
                status = "✅" if data.get('success') else "❌"
                print(f"  {name.replace('_', ' ').title()}: {status}")
        else:
            print("  Loading...")
        
        # Trading Activity
        print("\n📈 TRADING ACTIVITY:")
        if self.trading_data:
            print(f"  Total Trades: {self.trading_data.get('total_trades', 0)}")
            print(f"  Active Positions: {self.trading_data.get('active_positions', 0)}")
            print(f"  Success Rate: {self.trading_data.get('success_rate', 0) * 100:.1f}%")
            print(f"  Total P&L: {self.trading_data.get('total_pnl', 0) * 100:.2f}%")
        else:
            print("  Loading...")
        
        # Performance
        print("\n⚡ PERFORMANCE:")
        if self.performance_data:
            print(f"  Memory Usage: {self.performance_data.get('memory_usage_percent', 0):.1f}%")
            print(f"  Avg Response Time: {self.performance_data.get('average_response_time', 0):.0f}ms")
            print(f"  Error Rate: {self.performance_data.get('error_rate', 0):.1f}%")
        else:
            print("  Loading...")
        
        print("\n" + "=" * 80)
        print("Press Ctrl+C to exit")
    
    async def _update_all_data(self):
        """Update all dashboard data"""
        try:
            # Gather all data concurrently
            tasks = [
                self._fetch_health_data(),
                self._fetch_trading_data(),
                self._fetch_performance_data(),
                self._fetch_system_data()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update data if successful
            for i, result in enumerate(results):
                if not isinstance(result, Exception) and result:
                    if i == 0:
                        self.health_data = result
                    elif i == 1:
                        self.trading_data = result
                    elif i == 2:
                        self.performance_data = result
                    elif i == 3:
                        self.system_data = result
            
            self.last_update = datetime.now().strftime("%H:%M:%S")
            
        except Exception as e:
            logger.error(f"Error updating dashboard data: {e}")
    
    async def _fetch_health_data(self) -> Optional[Dict]:
        """Fetch health status data"""
        try:
            endpoints = ['/health', '/health/detailed', '/ready', '/live']
            results = {}
            overall_healthy = True
            
            for endpoint in endpoints:
                url = f"{self.railway_url}{endpoint}"
                async with self.session.get(url) as response:
                    success = response.status == 200
                    name = endpoint.lstrip('/').replace('/', '_')
                    
                    results[name] = {
                        'success': success,
                        'status_code': response.status,
                        'response_time': f"{response.headers.get('X-Response-Time', 'N/A')}"
                    }
                    
                    if not success:
                        overall_healthy = False
            
            return {
                'overall_healthy': overall_healthy,
                'endpoints': results
            }
            
        except Exception as e:
            logger.debug(f"Error fetching health data: {e}")
            return None
    
    async def _fetch_trading_data(self) -> Optional[Dict]:
        """Fetch trading metrics data"""
        try:
            url = f"{self.railway_url}/metrics"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Add calculated fields
                    if 'trades' in data:
                        total_trades = len(data['trades'])
                        successful_trades = sum(1 for trade in data['trades'] if trade.get('profit', 0) > 0)
                        data['success_rate'] = successful_trades / total_trades if total_trades > 0 else 0
                    
                    return data
                return None
                
        except Exception as e:
            logger.debug(f"Error fetching trading data: {e}")
            return None
    
    async def _fetch_performance_data(self) -> Optional[Dict]:
        """Fetch performance metrics data"""
        try:
            url = f"{self.railway_url}/health/detailed"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
                
        except Exception as e:
            logger.debug(f"Error fetching performance data: {e}")
            return None
    
    async def _fetch_system_data(self) -> Optional[Dict]:
        """Fetch system status data"""
        try:
            url = f"{self.railway_url}/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
                
        except Exception as e:
            logger.debug(f"Error fetching system data: {e}")
            return None

async def main():
    """Main entry point for dashboard"""
    # Get Railway URL from environment or use default
    railway_url = os.getenv('RAILWAY_BOT_URL', 'https://railway-up-production-f151.up.railway.app')
    
    print(f"🚀 Starting Railway Bot Dashboard...")
    print(f"Target: {railway_url}")
    print("Press Ctrl+C to exit\n")
    
    try:
        async with RailwayDashboard(railway_url) as dashboard:
            await dashboard.start_dashboard()
            
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal dashboard error: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDashboard terminated")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)