"""
Token Management Dashboard and CLI Interface

This module provides comprehensive CLI and dashboard interfaces for the token management system.
It supports real-time monitoring, interactive dashboards, and command-line tools for token management.
"""

import logging
import json
import argparse
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import asdict
import asyncio
import threading
from pathlib import Path

from simba.simba.database.postgres import PostgresDB
from src.token_monitoring import TokenMonitoringSystem, TokenUsageStatus, SystemHealthMetrics
from src.token_alerting import TokenAlertingSystem, AlertingConfig
from src.token_analytics import TokenAnalytics, ReportFormat

logger = logging.getLogger(__name__)


class DashboardWidget:
    """Base class for dashboard widgets."""
    
    def __init__(self, title: str, width: int = 80, height: int = 10):
        self.title = title
        self.width = width
        self.height = height
    
    def get_border(self) -> str:
        """Get widget border."""
        return "+" + "-" * (self.width - 2) + "+"
    
    def render_header(self) -> str:
        """Render widget header."""
        padding = (self.width - len(self.title) - 2) // 2
        header = "|" + " " * padding + self.title + " " * (self.width - len(self.title) - 2 - padding) + "|"
        return header
    
    def render_content(self) -> str:
        """Render the widget content."""
        raise NotImplementedError
    
    def render(self) -> str:
        """Render the complete widget."""
        content = self.render_content()
        lines = content.split('\n')
        
        # Pad content to widget height
        while len(lines) < self.height:
            lines.append("")
        
        # Truncate content to widget width
        lines = [line[:self.width] for line in lines]
        
        result = [self.get_border()]
        result.append(self.render_header())
        result.append(self.get_border())
        
        for line in lines[:self.height-2]:
            result.append("|" + line.ljust(self.width - 2) + "|")
        
        result.append(self.get_border())
        return '\n'.join(result)


class UsageStatusWidget(DashboardWidget):
    """Widget for displaying token usage status."""
    
    def __init__(self, monitoring_system: TokenMonitoringSystem, user_id: Optional[str] = None):
        super().__init__("Token Usage Status", 80, 8)
        self.monitoring_system = monitoring_system
        self.user_id = user_id
    
    def render_content(self) -> str:
        """Render usage status content."""
        try:
            status = self.monitoring_system.get_token_usage_status(self.user_id or "default")
            if not status:
                return "No usage data available"
            
            lines = [
                f"User: {status.user_id or 'All Users'}",
                f"Period: {status.period_start.strftime('%Y-%m-%d')} to {status.period_end.strftime('%Y-%m-%d')}",
                f"Total Tokens: {getattr(status, 'total_tokens', 0):,}",
                f"Requests: {getattr(status, 'total_requests', 0):,}",
                f"Average/Request: {getattr(status, 'average_tokens_per_request', 0):.1f}",
                f"Quota Used: {getattr(status, 'quota_used_percentage', 0):.1f}%"
            ]
            
            quota_used = getattr(status, 'quota_used_percentage', 0)
            if quota_used > 90:
                lines.append("⚠️  CRITICAL: Quota almost exhausted!")
            elif quota_used > 75:
                lines.append("⚠️  WARNING: Quota usage high")
            else:
                lines.append("✅ Quota usage normal")
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error rendering usage status: {e}")
            return "Error loading usage status"


class SystemHealthWidget(DashboardWidget):
    """Widget for displaying system health metrics."""
    
    def __init__(self, monitoring_system: TokenMonitoringSystem):
        super().__init__("System Health", 80, 10)
        self.monitoring_system = monitoring_system
    
    def render_content(self) -> str:
        """Render system health content."""
        try:
            health = self.monitoring_system.get_system_health()
            if not health:
                return "Health data unavailable"
            
            lines = [
                f"CPU Usage: {health.cpu_usage:.1f}%",
                f"Memory Usage: {health.memory_usage:.1f}%",
                f"Disk Usage: {getattr(health, 'disk_usage', 0):.1f}%",
                f"Error Rate: {getattr(health, 'error_rate', 0):.2f}%",
                f"Response Time: {getattr(health, 'average_response_time', 0):.2f}s",
                f"Active Users: {getattr(health, 'active_users', 0)}",
                f"Total Requests: {getattr(health, 'total_requests', 0):,}"
            ]
            
            # Health status
            cpu_usage = getattr(health, 'cpu_usage', 0)
            memory_usage = getattr(health, 'memory_usage', 0)
            error_rate = getattr(health, 'error_rate', 0)
            
            if cpu_usage > 80 or memory_usage > 85:
                lines.append("⚠️  WARNING: High resource usage")
            elif error_rate > 5:
                lines.append("⚠️  WARNING: High error rate")
            else:
                lines.append("✅ System healthy")
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error rendering system health: {e}")
            return "Error loading system health"


class AlertsWidget(DashboardWidget):
    """Widget for displaying active alerts."""
    
    def __init__(self, alerting_system: TokenAlertingSystem):
        super().__init__("Active Alerts", 80, 12)
        self.alerting_system = alerting_system
    
    def render_content(self) -> str:
        """Render alerts content."""
        try:
            alerts = self.alerting_system.get_active_alerts()
            
            if not alerts:
                return "No active alerts"
            
            lines = []
            for alert in alerts[:5]:  # Show top 5 alerts
                time_ago = (datetime.utcnow() - alert.timestamp).seconds // 60
                lines.append(f"[{alert.severity.value}] {alert.message}")
                lines.append(f"   User: {alert.user_id}, Time: {time_ago}m ago")
                lines.append("")
            
            if len(alerts) > 5:
                lines.append(f"... and {len(alerts) - 5} more alerts")
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error rendering alerts: {e}")
            return "Error loading alerts"


class TokenDashboard:
    """
    Interactive dashboard for token management monitoring.
    
    Provides real-time dashboards with widgets for monitoring
    token usage, system health, and alerts.
    """
    
    def __init__(self, db: Optional[PostgresDB] = None):
        """
        Initialize the dashboard.
        
        Args:
            db: Database instance
        """
        self.db = db or PostgresDB()
        self.monitoring = TokenMonitoringSystem(db)
        self.alerting = TokenAlertingSystem(db)
        self.analytics = TokenAnalytics(db)
        
        # Dashboard configuration
        self.config = {
            'refresh_interval': 30,  # seconds
            'max_widgets': 10,
            'enable_real_time': True,
            'log_level': 'INFO'
        }
        
        # Dashboard widgets
        self.widgets = []
        self.running = False
        self.refresh_thread = None
        
        logger.info("TokenDashboard initialized")
    
    def add_widget(self, widget: DashboardWidget):
        """Add a widget to the dashboard."""
        if len(self.widgets) < self.config['max_widgets']:
            self.widgets.append(widget)
            logger.info(f"Added widget: {widget.title}")
        else:
            logger.warning(f"Maximum widgets ({self.config['max_widgets']}) reached")
    
    def remove_widget(self, title: str):
        """Remove a widget by title."""
        self.widgets = [w for w in self.widgets if w.title != title]
        logger.info(f"Removed widget: {title}")
    
    def clear_widgets(self):
        """Clear all widgets."""
        self.widgets.clear()
        logger.info("Cleared all widgets")
    
    def setup_default_widgets(self, user_id: Optional[str] = None):
        """Setup default dashboard widgets."""
        self.clear_widgets()
        
        # Add default widgets
        self.add_widget(UsageStatusWidget(self.monitoring, user_id))
        self.add_widget(SystemHealthWidget(self.monitoring))
        self.add_widget(AlertsWidget(self.alerting))
        
        logger.info("Setup default dashboard widgets")
    
    def render_dashboard(self) -> str:
        """Render the complete dashboard."""
        if not self.widgets:
            return "No widgets configured"
        
        # Render each widget
        widget_outputs = []
        for widget in self.widgets:
            try:
                widget_outputs.append(widget.render())
            except Exception as e:
                logger.error(f"Error rendering widget {widget.title}: {e}")
                widget_outputs.append(f"Error in {widget.title}")
        
        # Combine widget outputs
        return '\n\n'.join(widget_outputs)
    
    def start_real_time(self, user_id: Optional[str] = None):
        """Start real-time dashboard updates."""
        if self.running:
            logger.warning("Dashboard already running")
            return
        
        self.running = True
        self.setup_default_widgets(user_id)
        
        def refresh_loop():
            while self.running:
                try:
                    # Clear screen and render dashboard
                    print("\033[2J\033[H")  # Clear screen and move cursor to top
                    print(self.render_dashboard())
                    print(f"\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print("Press Ctrl+C to stop...")
                    
                    time.sleep(self.config['refresh_interval'])
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Error in refresh loop: {e}")
                    time.sleep(5)  # Wait before retry
        
        self.refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self.refresh_thread.start()
        
        logger.info("Real-time dashboard started")
    
    def stop_real_time(self):
        """Stop real-time dashboard updates."""
        self.running = False
        if self.refresh_thread:
            self.refresh_thread.join(timeout=5.0)
        
        logger.info("Real-time dashboard stopped")
    
    def generate_report(self, user_id: Optional[str] = None, days: int = 7) -> str:
        """Generate a comprehensive report."""
        try:
            # Generate analytics report
            report = self.analytics.generate_usage_report(user_id, days)
            
            # Format report as text
            lines = []
            lines.append("=" * 80)
            lines.append(report.title)
            lines.append("=" * 80)
            lines.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Period: {report.time_period['start'].strftime('%Y-%m-%d')} to {report.time_period['end'].strftime('%Y-%m-%d')}")
            lines.append("")
            
            # Summary
            lines.append("SUMMARY")
            lines.append("-" * 40)
            for key, value in report.summary.items():
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
            lines.append("")
            
            # Usage trends
            if report.usage_trends:
                lines.append("USAGE TRENDS")
                lines.append("-" * 40)
                for trend in report.usage_trends[:3]:  # Show top 3 trends
                    lines.append(f"Period: {trend.period_start.strftime('%Y-%m-%d')} to {trend.period_end.strftime('%Y-%m-%d')}")
                    lines.append(f"  Total Tokens: {trend.total_tokens:,}")
                    lines.append(f"  Average/Request: {trend.average_tokens_per_request:.1f}")
                    lines.append(f"  Trend: {trend.trend_direction.value}")
                    lines.append(f"  Growth Rate: {trend.growth_rate:.1f}%")
                    lines.append("")
            
            # Cost analysis
            if report.cost_analysis:
                lines.append("COST ANALYSIS")
                lines.append("-" * 40)
                cost = report.cost_analysis
                lines.append(f"Total Cost: ${cost.total_cost:.4f}")
                lines.append(f"Cost per Token: ${cost.cost_per_token:.6f}")
                lines.append(f"Cost per User: ${cost.cost_per_user:.4f}")
                lines.append(f"Budget Utilization: {cost.budget_utilization:.1%}")
                lines.append("")
                
                # Cost breakdown
                lines.append("Cost Breakdown by Endpoint:")
                for endpoint, cost in cost.cost_breakdown.items():
                    lines.append(f"  {endpoint}: ${cost:.4f}")
                lines.append("")
            
            # Recommendations
            if report.recommendations:
                lines.append("RECOMMENDATIONS")
                lines.append("-" * 40)
                for rec in report.recommendations[:5]:  # Show top 5 recommendations
                    lines.append(f"[{rec.priority.upper()}] {rec.description}")
                    if rec.estimated_savings:
                        lines.append(f"  Estimated Savings: ${rec.estimated_savings:.4f}")
                    lines.append("")
            
            lines.append("=" * 80)
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}"


class TokenCLI:
    """
    Command-line interface for token management.
    
    Provides comprehensive CLI commands for monitoring, alerting,
    and managing token usage.
    """
    
    def __init__(self, db: Optional[PostgresDB] = None):
        """
        Initialize the CLI.
        
        Args:
            db: Database instance
        """
        self.db = db or PostgresDB()
        self.monitoring = TokenMonitoringSystem(db)
        self.alerting = TokenAlertingSystem(db)
        self.analytics = TokenAnalytics(db)
        self.dashboard = TokenDashboard(db)
        
        logger.info("TokenCLI initialized")
    
    def setup_parser(self) -> argparse.ArgumentParser:
        """Setup argument parser."""
        parser = argparse.ArgumentParser(
            description="Token Management CLI - Monitor and manage token usage",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s status --user user123
  %(prog)s dashboard --user user123 --real-time
  %(prog)s report --days 7 --format json
  %(prog)s alerts --list --active
  %(prog)s analytics --forecast --days 30
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show token usage status')
        status_parser.add_argument('--user', help='Specific user ID')
        status_parser.add_argument('--json', action='store_true', help='Output as JSON')
        
        # Dashboard command
        dashboard_parser = subparsers.add_parser('dashboard', help='Start interactive dashboard')
        dashboard_parser.add_argument('--user', help='Specific user ID')
        dashboard_parser.add_argument('--real-time', action='store_true', help='Real-time updates')
        dashboard_parser.add_argument('--refresh', type=int, default=30, help='Refresh interval in seconds')
        
        # Report command
        report_parser = subparsers.add_parser('report', help='Generate usage report')
        report_parser.add_argument('--user', help='Specific user ID')
        report_parser.add_argument('--days', type=int, default=7, help='Number of days to include')
        report_parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
        report_parser.add_argument('--output', help='Output file path')
        
        # Alerts command
        alerts_parser = subparsers.add_parser('alerts', help='Manage alerts')
        alerts_parser.add_argument('--list', action='store_true', help='List active alerts')
        alerts_parser.add_argument('--history', action='store_true', help='Show alert history')
        alerts_parser.add_argument('--days', type=int, default=7, help='Days of history to show')
        alerts_parser.add_argument('--user', help='Filter by user ID')
        alerts_parser.add_argument('--acknowledge', help='Acknowledge specific alert ID')
        alerts_parser.add_argument('--resolve', help='Resolve specific alert ID')
        
        # Analytics command
        analytics_parser = subparsers.add_parser('analytics', help='Analytics and forecasting')
        analytics_parser.add_argument('--forecast', action='store_true', help='Show usage forecast')
        analytics_parser.add_argument('--trends', action='store_true', help='Show usage trends')
        analytics_parser.add_argument('--costs', action='store_true', help='Show cost analysis')
        analytics_parser.add_argument('--recommendations', action='store_true', help='Show recommendations')
        analytics_parser.add_argument('--user', help='Specific user ID')
        analytics_parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
        
        # System command
        system_parser = subparsers.add_parser('system', help='System information')
        system_parser.add_argument('--health', action='store_true', help='Show system health')
        system_parser.add_argument('--metrics', action='store_true', help='Show performance metrics')
        system_parser.add_argument('--config', action='store_true', help='Show configuration')
        
        return parser
    
    def run(self, args: Optional[List[str]] = None):
        """Run the CLI with given arguments."""
        parser = self.setup_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return
        
        try:
            if parsed_args.command == 'status':
                self.handle_status(parsed_args)
            elif parsed_args.command == 'dashboard':
                self.handle_dashboard(parsed_args)
            elif parsed_args.command == 'report':
                self.handle_report(parsed_args)
            elif parsed_args.command == 'alerts':
                self.handle_alerts(parsed_args)
            elif parsed_args.command == 'analytics':
                self.handle_analytics(parsed_args)
            elif parsed_args.command == 'system':
                self.handle_system(parsed_args)
            else:
                logger.error(f"Unknown command: {parsed_args.command}")
                
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            print(f"Error: {e}")
    
    def handle_status(self, args):
        """Handle status command."""
        try:
            status = self.monitoring.get_token_usage_status(args.user)
            
            if args.json:
                print(json.dumps(asdict(status), indent=2, default=str))
            else:
                print("=" * 60)
                print("TOKEN USAGE STATUS")
                print("=" * 60)
                print(f"User: {status.user_id or 'All Users'}")
                print(f"Period: {status.period_start.strftime('%Y-%m-%d')} to {status.period_end.strftime('%Y-%m-%d')}")
                print(f"Total Tokens: {getattr(status, 'total_tokens', 0):,}")
                print(f"Total Requests: {getattr(status, 'total_requests', 0):,}")
                print(f"Average Tokens/Request: {getattr(status, 'average_tokens_per_request', 0):.1f}")
                print(f"Quota Used: {getattr(status, 'quota_used_percentage', 0):.1f}%")
                print(f"Quota Remaining: {getattr(status, 'quota_remaining', 0):,} tokens")
                print(f"Top Endpoints: {', '.join(getattr(status, 'top_endpoints', [])[:3])}")
                
                quota_used = getattr(status, 'quota_used_percentage', 0)
                if quota_used > 90:
                    print("⚠️  CRITICAL: Quota almost exhausted!")
                elif quota_used > 75:
                    print("⚠️  WARNING: Quota usage high")
                else:
                    print("✅ Quota usage normal")
                
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            print(f"Error: {e}")
    
    def handle_dashboard(self, args):
        """Handle dashboard command."""
        try:
            self.dashboard.config['refresh_interval'] = args.refresh
            
            if args.real_time:
                print("Starting real-time dashboard...")
                print("Press Ctrl+C to stop")
                self.dashboard.start_real_time(args.user)
            else:
                # Single dashboard render
                self.dashboard.setup_default_widgets(args.user)
                print(self.dashboard.render_dashboard())
                
        except KeyboardInterrupt:
            print("\nDashboard stopped")
        except Exception as e:
            logger.error(f"Error running dashboard: {e}")
            print(f"Error: {e}")
    
    def handle_report(self, args):
        """Handle report command."""
        try:
            if args.format == 'json':
                report = self.analytics.generate_usage_report(args.user, args.days)
                output = json.dumps(asdict(report), indent=2, default=str)
            else:
                output = self.dashboard.generate_report(args.user, args.days)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"Report saved to: {args.output}")
            else:
                print(output)
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            print(f"Error: {e}")
    
    def handle_alerts(self, args):
        """Handle alerts command."""
        try:
            if args.list:
                alerts = self.alerting.get_active_alerts(args.user)
                if not alerts:
                    print("No active alerts")
                else:
                    print("=" * 60)
                    print("ACTIVE ALERTS")
                    print("=" * 60)
                    for alert in alerts:
                        print(f"[{alert.severity.value}] {alert.message}")
                        print(f"  User: {alert.user_id}")
                        print(f"  Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"  ID: {alert.alert_id}")
                        print()
            
            elif args.history:
                alerts = self.alerting.get_alert_history(args.user, args.days)
                if not alerts:
                    print("No alert history")
                else:
                    print("=" * 60)
                    print("ALERT HISTORY")
                    print("=" * 60)
                    for alert in alerts:
                        status = "RESOLVED" if alert.resolved else "ACTIVE"
                        print(f"[{alert.severity.value}] {alert.message} ({status})")
                        print(f"  User: {alert.user_id}")
                        print(f"  Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                        print()
            
            elif args.acknowledge:
                success = self.alerting.acknowledge_alert(args.acknowledge)
                if success:
                    print(f"Alert {args.acknowledge} acknowledged")
                else:
                    print(f"Alert {args.acknowledge} not found")
            
            elif args.resolve:
                success = self.alerting.resolve_alert(args.resolve)
                if success:
                    print(f"Alert {args.resolve} resolved")
                else:
                    print(f"Alert {args.resolve} not found")
            
            else:
                print("Use --list, --history, --acknowledge, or --resolve")
                
        except Exception as e:
            logger.error(f"Error handling alerts: {e}")
            print(f"Error: {e}")
    
    def handle_analytics(self, args):
        """Handle analytics command."""
        try:
            if args.forecast:
                report = self.analytics.generate_usage_report(args.user, args.days)
                if report.forecast_data:
                    print("=" * 60)
                    print("USAGE FORECAST")
                    print("=" * 60)
                    print(f"Predicted Usage: {report.forecast_data.predicted_usage:,} tokens")
                    print(f"Confidence Interval: {report.forecast_data.confidence_interval}")
                    print(f"Accuracy Score: {report.forecast_data.accuracy_score:.2f}")
                    print(f"Factors: {', '.join(report.forecast_data.factors)}")
                else:
                    print("No forecast data available")
            
            elif args.trends:
                report = self.analytics.generate_usage_report(args.user, args.days)
                if report.usage_trends:
                    print("=" * 60)
                    print("USAGE TRENDS")
                    print("=" * 60)
                    for trend in report.usage_trends:
                        print(f"Period: {trend.period_start.strftime('%Y-%m-%d')} to {trend.period_end.strftime('%Y-%m-%d')}")
                        print(f"  Total Tokens: {trend.total_tokens:,}")
                        print(f"  Average/Request: {trend.average_tokens_per_request:.1f}")
                        print(f"  Trend: {trend.trend_direction.value}")
                        print(f"  Growth Rate: {trend.growth_rate:.1f}%")
                        print()
                else:
                    print("No trend data available")
            
            elif args.costs:
                report = self.analytics.generate_usage_report(args.user, args.days)
                if report.cost_analysis:
                    print("=" * 60)
                    print("COST ANALYSIS")
                    print("=" * 60)
                    cost = report.cost_analysis
                    print(f"Total Cost: ${cost.total_cost:.4f}")
                    print(f"Cost per Token: ${cost.cost_per_token:.6f}")
                    print(f"Cost per User: ${cost.cost_per_user:.4f}")
                    print(f"Budget Utilization: {cost.budget_utilization:.1%}")
                    print(f"Cost Trend: {cost.cost_trend.value}")
                    print(f"Projected Cost: ${cost.projected_cost:.4f}")
                    
                    print("\nCost Breakdown by Endpoint:")
                    for endpoint, cost in cost.cost_breakdown.items():
                        print(f"  {endpoint}: ${cost:.4f}")
                else:
                    print("No cost data available")
            
            elif args.recommendations:
                report = self.analytics.generate_usage_report(args.user, args.days)
                if report.recommendations:
                    print("=" * 60)
                    print("RECOMMENDATIONS")
                    print("=" * 60)
                    for rec in report.recommendations:
                        print(f"[{rec.priority.upper()}] {rec.description}")
                        print(f"  Type: {rec.type}")
                        print(f"  Impact: {rec.impact}")
                        if rec.estimated_savings:
                            print(f"  Estimated Savings: ${rec.estimated_savings:.4f}")
                        print(f"  Implementation Effort: {rec.implementation_effort}")
                        print()
                else:
                    print("No recommendations available")
            
            else:
                print("Use --forecast, --trends, --costs, or --recommendations")
                
        except Exception as e:
            logger.error(f"Error handling analytics: {e}")
            print(f"Error: {e}")
    
    def handle_system(self, args):
        """Handle system command."""
        try:
            if args.health:
                health = self.monitoring.get_system_health()
                if health:
                    print("=" * 60)
                    print("SYSTEM HEALTH")
                    print("=" * 60)
                    print(f"CPU Usage: {health.cpu_usage:.1f}%")
                    print(f"Memory Usage: {health.memory_usage:.1f}%")
                    print(f"Disk Usage: {getattr(health, 'disk_usage', 0):.1f}%")
                    print(f"Error Rate: {getattr(health, 'error_rate', 0):.2f}%")
                    print(f"Response Time: {getattr(health, 'average_response_time', 0):.2f}s")
                    print(f"Active Users: {getattr(health, 'active_users', 0)}")
                    print(f"Total Requests: {getattr(health, 'total_requests', 0):,}")
                    
                    cpu_usage = getattr(health, 'cpu_usage', 0)
                    memory_usage = getattr(health, 'memory_usage', 0)
                    error_rate = getattr(health, 'error_rate', 0)
                    
                    if cpu_usage > 80 or memory_usage > 85:
                        print("⚠️  WARNING: High resource usage")
                    elif error_rate > 5:
                        print("⚠️  WARNING: High error rate")
                    else:
                        print("✅ System healthy")
                else:
                    print("No health data available")
            
            elif args.metrics:
                metrics = self.monitoring.get_performance_metrics()
                print("=" * 60)
                print("PERFORMANCE METRICS")
                print("=" * 60)
                for key, value in metrics.items():
                    print(f"{key.replace('_', ' ').title()}: {value}")
            
            elif args.config:
                config = {
                    'monitoring_config': self.monitoring.config,
                    'alerting_config': self.alerting.config.__dict__,
                    'analytics_config': self.analytics.config,
                    'dashboard_config': self.dashboard.config
                }
                print(json.dumps(config, indent=2))
            
            else:
                print("Use --health, --metrics, or --config")
                
        except Exception as e:
            logger.error(f"Error handling system: {e}")
            print(f"Error: {e}")


# Convenience functions
def get_cli_system(db: Optional[PostgresDB] = None) -> TokenCLI:
    """Get a global CLI system instance."""
    return TokenCLI(db)


def run_cli(args: Optional[List[str]] = None, db: Optional[PostgresDB] = None):
    """Run the CLI with optional arguments."""
    cli = TokenCLI(db)
    cli.run(args)


if __name__ == "__main__":
    run_cli()