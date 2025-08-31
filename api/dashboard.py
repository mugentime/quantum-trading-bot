#!/usr/bin/env python3
"""
Web Dashboard for Quantum Trading Bot
Provides real-time monitoring interface
"""

from flask import Flask, render_template_string, jsonify
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# HTML Template for Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Quantum Trading Bot Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0e27;
            color: #fff;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .subtitle { opacity: 0.9; font-size: 1.1em; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #1a1f3a;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #2a3f5f;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 6px;
        }
        .metric-label { opacity: 0.7; }
        .metric-value { 
            font-weight: bold;
            font-size: 1.1em;
        }
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        .neutral { color: #6b7280; }
        .warning { color: #f59e0b; }
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        .status-active { background: #10b981; }
        .status-inactive { background: #ef4444; }
        .status-warning { background: #f59e0b; }
        .table-container {
            background: #1a1f3a;
            border-radius: 12px;
            padding: 20px;
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #2a3f5f;
        }
        th {
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            font-weight: bold;
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }
        .refresh-btn:hover {
            background: #764ba2;
            transform: translateY(-2px);
        }
        .alert {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
            color: #ef4444;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .chart-container {
            height: 300px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ Quantum Trading Bot</h1>
        <div class="subtitle">Real-Time Trading Dashboard</div>
    </div>

    <div id="alerts"></div>

    <div class="grid">
        <div class="card">
            <h3>System Status</h3>
            <div class="metric">
                <span class="metric-label">Trading Mode</span>
                <span class="metric-value" id="trading-mode">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Bot Status</span>
                <span id="bot-status">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Uptime</span>
                <span class="metric-value" id="uptime">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Last Update</span>
                <span class="metric-value" id="last-update">-</span>
            </div>
        </div>

        <div class="card">
            <h3>Account Info</h3>
            <div class="metric">
                <span class="metric-label">Balance (USDT)</span>
                <span class="metric-value" id="balance">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Active Positions</span>
                <span class="metric-value" id="positions">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Open Orders</span>
                <span class="metric-value" id="orders">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Margin Used</span>
                <span class="metric-value" id="margin">-</span>
            </div>
        </div>

        <div class="card">
            <h3>Performance</h3>
            <div class="metric">
                <span class="metric-label">P&L Today</span>
                <span class="metric-value" id="pnl-today">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Total Trades</span>
                <span class="metric-value" id="total-trades">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Win Rate</span>
                <span class="metric-value" id="win-rate">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Target (14% Daily)</span>
                <span class="metric-value" id="target-progress">-</span>
            </div>
        </div>

        <div class="card">
            <h3>Risk Metrics</h3>
            <div class="metric">
                <span class="metric-label">Current Leverage</span>
                <span class="metric-value" id="leverage">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Max Drawdown</span>
                <span class="metric-value" id="drawdown">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Risk Score</span>
                <span class="metric-value" id="risk-score">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Circuit Breaker</span>
                <span id="circuit-breaker">-</span>
            </div>
        </div>
    </div>

    <div class="table-container">
        <h3 style="margin-bottom: 20px; color: #667eea;">Active Signals & Trades</h3>
        <table id="trades-table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Price</th>
                    <th>Quantity</th>
                    <th>Status</th>
                    <th>P&L</th>
                </tr>
            </thead>
            <tbody id="trades-body">
                <tr><td colspan="7" style="text-align: center; opacity: 0.5;">No active trades</td></tr>
            </tbody>
        </table>
    </div>

    <div style="margin-top: 30px; text-align: center;">
        <button class="refresh-btn" onclick="refreshData()">Refresh Data</button>
    </div>

    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/dashboard-data');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error fetching data:', error);
                showAlert('Failed to fetch data from server');
            }
        }

        function updateDashboard(data) {
            // Update system status
            document.getElementById('trading-mode').textContent = data.trading_mode || 'Unknown';
            document.getElementById('trading-mode').className = 
                data.trading_mode === 'PRODUCTION' ? 'metric-value positive' : 'metric-value warning';
            
            const statusBadge = document.getElementById('bot-status');
            statusBadge.innerHTML = `<span class="status-badge ${data.bot_active ? 'status-active' : 'status-inactive'}">${data.bot_active ? 'ACTIVE' : 'INACTIVE'}</span>`;
            
            document.getElementById('uptime').textContent = formatUptime(data.uptime_seconds);
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            
            // Update account info
            document.getElementById('balance').textContent = '$' + (data.balance || 0).toFixed(2);
            document.getElementById('positions').textContent = data.active_positions || 0;
            document.getElementById('orders').textContent = data.open_orders || 0;
            document.getElementById('margin').textContent = (data.margin_used || 0).toFixed(1) + '%';
            
            // Update performance
            const pnl = data.pnl_today || 0;
            const pnlElement = document.getElementById('pnl-today');
            pnlElement.textContent = '$' + pnl.toFixed(2);
            pnlElement.className = pnl >= 0 ? 'metric-value positive' : 'metric-value negative';
            
            document.getElementById('total-trades').textContent = data.total_trades || 0;
            document.getElementById('win-rate').textContent = (data.win_rate || 0).toFixed(1) + '%';
            
            const targetProgress = ((pnl / (data.balance * 0.14)) * 100).toFixed(1);
            const targetElement = document.getElementById('target-progress');
            targetElement.textContent = targetProgress + '%';
            targetElement.className = targetProgress >= 100 ? 'metric-value positive' : 'metric-value neutral';
            
            // Update risk metrics
            document.getElementById('leverage').textContent = (data.current_leverage || 0) + 'x';
            document.getElementById('drawdown').textContent = (data.max_drawdown || 0).toFixed(1) + '%';
            
            const riskScore = data.risk_score || 0;
            const riskElement = document.getElementById('risk-score');
            riskElement.textContent = riskScore.toFixed(2) + '/10';
            riskElement.className = riskScore > 7 ? 'metric-value negative' : 'metric-value positive';
            
            const circuitElement = document.getElementById('circuit-breaker');
            circuitElement.innerHTML = `<span class="status-badge ${data.circuit_breaker_active ? 'status-warning' : 'status-active'}">${data.circuit_breaker_active ? 'TRIGGERED' : 'NORMAL'}</span>`;
            
            // Update trades table
            updateTradesTable(data.recent_trades || []);
            
            // Show alerts if needed
            if (data.alerts && data.alerts.length > 0) {
                showAlerts(data.alerts);
            }
        }

        function updateTradesTable(trades) {
            const tbody = document.getElementById('trades-body');
            if (trades.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; opacity: 0.5;">No active trades</td></tr>';
                return;
            }
            
            tbody.innerHTML = trades.map(trade => `
                <tr>
                    <td>${new Date(trade.timestamp).toLocaleTimeString()}</td>
                    <td>${trade.symbol}</td>
                    <td class="${trade.side === 'BUY' ? 'positive' : 'negative'}">${trade.side}</td>
                    <td>$${trade.price.toFixed(2)}</td>
                    <td>${trade.quantity.toFixed(4)}</td>
                    <td><span class="status-badge status-${trade.status.toLowerCase()}">${trade.status}</span></td>
                    <td class="${trade.pnl >= 0 ? 'positive' : 'negative'}">$${trade.pnl.toFixed(2)}</td>
                </tr>
            `).join('');
        }

        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }

        function showAlert(message) {
            const alertDiv = document.getElementById('alerts');
            alertDiv.innerHTML = `<div class="alert">${message}</div>`;
            setTimeout(() => alertDiv.innerHTML = '', 5000);
        }

        function showAlerts(alerts) {
            const alertDiv = document.getElementById('alerts');
            alertDiv.innerHTML = alerts.map(alert => 
                `<div class="alert">${alert}</div>`
            ).join('');
        }

        // Auto-refresh every 5 seconds
        setInterval(refreshData, 5000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Serve the dashboard HTML"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/dashboard-data')
def dashboard_data():
    """Provide real-time data for dashboard"""
    try:
        # Import here to avoid circular imports
        from core.config.settings import config
        
        # Gather system data
        data = {
            'trading_mode': 'TESTNET' if config.BINANCE_TESTNET else 'PRODUCTION',
            'bot_active': True,  # This should come from actual bot status
            'uptime_seconds': 0,
            'balance': 0,
            'active_positions': 0,
            'open_orders': 0,
            'margin_used': 0,
            'pnl_today': 0,
            'total_trades': 0,
            'win_rate': 0,
            'current_leverage': config.DEFAULT_LEVERAGE,
            'max_drawdown': 0,
            'risk_score': 0,
            'circuit_breaker_active': False,
            'recent_trades': [],
            'alerts': []
        }
        
        # Try to get actual data from health checker if available
        try:
            from api.health import health_checker
            system_metrics = health_checker.get_system_metrics()
            trading_metrics = health_checker.get_trading_metrics()
            
            data.update({
                'uptime_seconds': health_checker.get_uptime(),
                'active_positions': trading_metrics.get('active_positions', 0),
                'total_trades': trading_metrics.get('total_trades', 0),
                'win_rate': trading_metrics.get('win_rate', 0),
                'pnl_today': trading_metrics.get('pnl_today', 0)
            })
        except:
            pass
        
        # Add warning alerts if in testnet mode
        if config.BINANCE_TESTNET:
            data['alerts'].append('WARNING: Bot is in TESTNET mode - no real trading!')
        
        if data['total_trades'] == 0 and data['uptime_seconds'] > 600:
            data['alerts'].append('WARNING: No trades executed - check configuration!')
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_dashboard(port: int = 8081):
    """Start the dashboard server"""
    print(f"Starting dashboard on port {port}")
    print(f"Access dashboard at: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    port = int(os.getenv("DASHBOARD_PORT", 8081))
    start_dashboard(port)