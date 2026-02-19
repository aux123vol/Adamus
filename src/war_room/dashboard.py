"""
War Room Dashboard

Flask-based web dashboard for Augustus's daily steering.

Features:
- Real-time metrics display
- Three panels: Internal Vitals, External Radar, Strategic Horizon
- Alert feed with severity coloring
- Mobile-responsive design

Access via: http://localhost:5000
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional
from flask import Flask, render_template_string, jsonify, request

from .metrics import MetricsCollector, InternalMetrics
from .alerts import AlertSystem, AlertSeverity

logger = logging.getLogger(__name__)


# HTML Template for War Room Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adamus War Room</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            min-height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem 2rem;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            font-size: 1.5rem;
            color: #00d4ff;
        }

        .header .status {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00ff00;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .container {
            padding: 1rem;
            max-width: 1600px;
            margin: 0 auto;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
        }

        .panel {
            background: #1a1a2e;
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid #333;
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #333;
        }

        .panel-title {
            font-size: 1rem;
            color: #00d4ff;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #222;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            color: #888;
        }

        .metric-value {
            font-weight: 600;
            font-family: 'Monaco', 'Menlo', monospace;
        }

        .metric-value.positive {
            color: #00ff00;
        }

        .metric-value.negative {
            color: #ff4444;
        }

        .metric-value.warning {
            color: #ffaa00;
        }

        .alert-feed {
            max-height: 300px;
            overflow-y: auto;
        }

        .alert {
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 4px;
            border-left: 4px solid;
        }

        .alert.critical {
            background: rgba(255, 68, 68, 0.1);
            border-left-color: #ff4444;
        }

        .alert.warning {
            background: rgba(255, 170, 0, 0.1);
            border-left-color: #ffaa00;
        }

        .alert.info {
            background: rgba(0, 212, 255, 0.1);
            border-left-color: #00d4ff;
        }

        .alert-title {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }

        .alert-message {
            font-size: 0.875rem;
            color: #888;
        }

        .alert-time {
            font-size: 0.75rem;
            color: #666;
            margin-top: 0.25rem;
        }

        .section-title {
            font-size: 1.25rem;
            color: #00d4ff;
            margin: 1.5rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #00d4ff;
        }

        .competitor-card {
            background: #222;
            padding: 0.75rem;
            border-radius: 4px;
            margin-bottom: 0.5rem;
        }

        .competitor-name {
            font-weight: 600;
            color: #fff;
        }

        .competitor-threat {
            display: inline-block;
            padding: 0.125rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            margin-left: 0.5rem;
        }

        .competitor-threat.high {
            background: #ff4444;
        }

        .competitor-threat.medium {
            background: #ffaa00;
            color: #000;
        }

        .competitor-threat.low {
            background: #00ff00;
            color: #000;
        }

        .refresh-btn {
            background: #00d4ff;
            color: #000;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
        }

        .refresh-btn:hover {
            background: #00b8e6;
        }

        .last-updated {
            color: #666;
            font-size: 0.875rem;
        }

        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 1rem;
            }

            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>⚔️ ADAMUS WAR ROOM</h1>
        <div class="status">
            <span class="last-updated" id="lastUpdated">Loading...</span>
            <div class="status-indicator"></div>
            <button class="refresh-btn" onclick="refreshMetrics()">Refresh</button>
        </div>
    </header>

    <div class="container">
        <!-- Alerts Section -->
        <h2 class="section-title">🚨 Active Alerts</h2>
        <div class="panel">
            <div class="alert-feed" id="alertFeed">
                <p style="color: #666; text-align: center;">No active alerts</p>
            </div>
        </div>

        <!-- Internal Vitals -->
        <h2 class="section-title">📊 Internal Vitals</h2>
        <div class="grid">
            <!-- Survival Metrics -->
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">💰 Survival</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Cash Balance</span>
                    <span class="metric-value" id="cashBalance">$0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Burn Rate</span>
                    <span class="metric-value" id="burnRate">$0/mo</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Runway</span>
                    <span class="metric-value" id="runway">0 months</span>
                </div>
            </div>

            <!-- PMF Metrics -->
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">📈 Product-Market Fit</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Users</span>
                    <span class="metric-value" id="totalUsers">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Paying Users</span>
                    <span class="metric-value positive" id="payingUsers">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">MRR</span>
                    <span class="metric-value positive" id="mrr">$0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Churn Rate</span>
                    <span class="metric-value" id="churnRate">0%</span>
                </div>
            </div>

            <!-- Adamus Health -->
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">🤖 Adamus Health</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Capabilities</span>
                    <span class="metric-value" id="capabilities">0/100</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Security Score</span>
                    <span class="metric-value" id="securityScore">0/10</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Documents Loaded</span>
                    <span class="metric-value positive" id="docsLoaded">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Budget Remaining</span>
                    <span class="metric-value" id="budgetRemaining">$0</span>
                </div>
            </div>
        </div>

        <!-- External Radar -->
        <h2 class="section-title">🎯 External Radar</h2>
        <div class="grid">
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">Competitors</span>
                </div>
                <div id="competitors">
                    <p style="color: #666;">Loading...</p>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">Market Signals</span>
                </div>
                <div id="marketSignals">
                    <p style="color: #666;">Loading...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function refreshMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to fetch metrics:', error);
            }
        }

        function updateDashboard(data) {
            const internal = data.internal;
            const external = data.external;

            // Update survival
            document.getElementById('cashBalance').textContent = '$' + internal.survival.cash_balance.toLocaleString();
            document.getElementById('burnRate').textContent = '$' + internal.survival.burn_rate.toLocaleString() + '/mo';

            const runway = document.getElementById('runway');
            runway.textContent = internal.survival.runway_months + ' months';
            runway.className = 'metric-value ' + (internal.survival.runway_months < 6 ? 'warning' : 'positive');

            // Update PMF
            document.getElementById('totalUsers').textContent = internal.pmf.total_users.toLocaleString();
            document.getElementById('payingUsers').textContent = internal.pmf.paying_users.toLocaleString();
            document.getElementById('mrr').textContent = '$' + internal.pmf.mrr.toLocaleString();

            const churn = document.getElementById('churnRate');
            churn.textContent = internal.pmf.churn_rate + '%';
            churn.className = 'metric-value ' + (internal.pmf.churn_rate > 10 ? 'negative' : '');

            // Update Adamus
            document.getElementById('capabilities').textContent =
                internal.adamus.capabilities_built + '/' + internal.adamus.capabilities_total;
            document.getElementById('securityScore').textContent =
                internal.adamus.security_score.toFixed(1) + '/10';
            document.getElementById('docsLoaded').textContent = internal.adamus.documents_loaded;
            document.getElementById('budgetRemaining').textContent = '$' + internal.adamus.budget_remaining.toFixed(2);

            // Update competitors
            const competitorsDiv = document.getElementById('competitors');
            competitorsDiv.innerHTML = external.competitors.map(c => `
                <div class="competitor-card">
                    <span class="competitor-name">${c.name}</span>
                    <span class="competitor-threat ${c.threat_level}">${c.threat_level}</span>
                    <div style="color: #888; font-size: 0.875rem; margin-top: 0.5rem;">
                        ${c.recent_features.join(', ')}
                    </div>
                </div>
            `).join('');

            // Update market signals
            const signalsDiv = document.getElementById('marketSignals');
            signalsDiv.innerHTML = external.market_signals.map(s => `
                <div style="padding: 0.5rem 0; border-bottom: 1px solid #333;">• ${s}</div>
            `).join('');

            // Update timestamp
            document.getElementById('lastUpdated').textContent = 'Updated: ' + new Date(data.collected_at).toLocaleTimeString();
        }

        async function fetchAlerts() {
            try {
                const response = await fetch('/api/alerts');
                const data = await response.json();
                updateAlerts(data.alerts);
            } catch (error) {
                console.error('Failed to fetch alerts:', error);
            }
        }

        function updateAlerts(alerts) {
            const feed = document.getElementById('alertFeed');

            if (alerts.length === 0) {
                feed.innerHTML = '<p style="color: #666; text-align: center;">✅ No active alerts</p>';
                return;
            }

            feed.innerHTML = alerts.map(a => `
                <div class="alert ${a.severity}">
                    <div class="alert-title">${a.title}</div>
                    <div class="alert-message">${a.message}</div>
                    <div class="alert-time">${new Date(a.timestamp).toLocaleString()}</div>
                </div>
            `).join('');
        }

        // Initial load
        refreshMetrics();
        fetchAlerts();

        // Auto-refresh every 30 seconds
        setInterval(() => {
            refreshMetrics();
            fetchAlerts();
        }, 30000);
    </script>
</body>
</html>
"""


def create_app(
    coordinator=None,
    memory_db=None
) -> Flask:
    """
    Create the War Room Flask application.

    Args:
        coordinator: AI Coordinator instance
        memory_db: Memory database instance

    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('WAR_ROOM_SECRET', 'dev-secret-key')

    # Initialize components
    metrics_collector = MetricsCollector(
        coordinator=coordinator,
        memory_db=memory_db
    )
    alert_system = AlertSystem()

    @app.route('/')
    def index():
        """Render War Room dashboard."""
        return render_template_string(DASHBOARD_HTML)

    @app.route('/api/metrics')
    def get_metrics():
        """API endpoint for metrics."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            metrics = loop.run_until_complete(metrics_collector.collect_all())

            # Check for alerts
            internal = InternalMetrics(
                timestamp=metrics['internal']['timestamp'],
                survival=type('Survival', (), metrics['internal']['survival'])(),
                pmf=type('PMF', (), metrics['internal']['pmf'])(),
                productivity=type('Productivity', (), metrics['internal']['productivity'])(),
                adamus=type('Adamus', (), metrics['internal']['adamus'])()
            )
            # Note: This is a simplified check - production would use proper dataclass

            return jsonify(metrics)
        finally:
            loop.close()

    @app.route('/api/alerts')
    def get_alerts():
        """API endpoint for alerts."""
        return jsonify(alert_system.get_alert_summary())

    @app.route('/api/health')
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "metrics_collector": "active",
                "alert_system": "active"
            }
        })

    return app


def run_dashboard(
    host: str = "0.0.0.0",
    port: int = 5000,
    coordinator=None,
    debug: bool = False
):
    """
    Run the War Room dashboard.

    Args:
        host: Host to bind to
        port: Port to run on
        coordinator: AI Coordinator instance
        debug: Enable debug mode
    """
    app = create_app(coordinator=coordinator)

    logger.info(f"Starting War Room dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_dashboard(debug=True)
