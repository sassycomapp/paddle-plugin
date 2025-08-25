"""
Comprehensive Test Suite for Token Monitoring and Reporting System

This test suite provides comprehensive coverage for the token monitoring,
alerting, analytics, and dashboard components.
"""

import unittest
import unittest.mock as mock
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simba.simba.database.postgres import PostgresDB
from src.token_monitoring import TokenMonitoringSystem, TokenUsageStatus, SystemHealthMetrics, Anomaly
from src.token_alerting import TokenAlertingSystem, Alert, AlertSeverity, AlertingConfig
from src.token_analytics import TokenAnalytics, ReportFormat, UsageTrend, CostAnalysis
from src.token_dashboard import TokenDashboard, TokenCLI, UsageStatusWidget, SystemHealthWidget
from src.token_management.token_counter import TokenCounter, TokenizationModel


class TestTokenMonitoringSystem(unittest.TestCase):
    """Test cases for TokenMonitoringSystem."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.monitoring = TokenMonitoringSystem(self.mock_db)
        
        # Mock database responses
        self.mock_usage_data = [
            {
                'user_id': 'user1',
                'session_id': 'session1',
                'tokens_used': 100,
                'api_endpoint': 'chat/completions',
                'priority_level': 'Medium',
                'timestamp': datetime.utcnow()
            },
            {
                'user_id': 'user1',
                'session_id': 'session2',
                'tokens_used': 150,
                'api_endpoint': 'chat/completions',
                'priority_level': 'High',
                'timestamp': datetime.utcnow() - timedelta(hours=1)
            }
        ]
    
    def test_init(self):
        """Test TokenMonitoringSystem initialization."""
        self.assertEqual(self.monitoring.db, self.mock_db)
        self.assertIsInstance(self.monitoring.config, dict)
        self.assertIsInstance(self.monitoring.metrics, dict)
    
    def test_get_token_usage_status_success(self):
        """Test successful token usage status retrieval."""
        self.mock_db.get_user_token_usage.return_value = self.mock_usage_data
        
        status = self.monitoring.get_token_usage_status('user1')
        
        self.assertIsNotNone(status)
        self.assertEqual(status.user_id, 'user1')
        self.assertEqual(status.total_tokens, 250)
        self.assertEqual(status.total_requests, 2)
        self.assertEqual(status.average_tokens_per_request, 125.0)
    
    def test_get_token_usage_status_no_data(self):
        """Test token usage status with no data."""
        self.mock_db.get_user_token_usage.return_value = []
        
        status = self.monitoring.get_token_usage_status('user1')
        
        self.assertIsNotNone(status)
        self.assertEqual(status.total_tokens, 0)
        self.assertEqual(status.total_requests, 0)
        self.assertEqual(status.average_tokens_per_request, 0.0)
    
    def test_get_token_usage_status_all_users(self):
        """Test token usage status for all users."""
        self.mock_db.get_user_token_usage.return_value = self.mock_usage_data
        
        status = self.monitoring.get_token_usage_status()
        
        self.assertIsNotNone(status)
        self.assertIsNone(status.user_id)
        self.assertEqual(status.total_tokens, 250)
    
    def test_get_system_health_success(self):
        """Test successful system health retrieval."""
        mock_health = {
            'cpu_usage': 45.5,
            'memory_usage': 60.2,
            'disk_usage': 75.0,
            'error_rate': 1.5,
            'average_response_time': 0.8,
            'active_users': 10,
            'total_requests': 1000
        }
        
        self.mock_db.get_system_health.return_value = mock_health
        
        health = self.monitoring.get_system_health()
        
        self.assertIsNotNone(health)
        self.assertEqual(health.cpu_usage, 45.5)
        self.assertEqual(health.memory_usage, 60.2)
        self.assertEqual(health.error_rate, 1.5)
    
    def test_get_system_health_no_data(self):
        """Test system health with no data."""
        self.mock_db.get_system_health.return_value = None
        
        health = self.monitoring.get_system_health()
        
        self.assertIsNone(health)
    
    def test_detect_anomalies_success(self):
        """Test successful anomaly detection."""
        self.mock_db.get_user_token_usage.return_value = self.mock_usage_data
        
        anomalies = self.monitoring.detect_anomalies()
        
        self.assertIsInstance(anomalies, list)
        # Should detect anomalies based on high usage
        self.assertTrue(len(anomalies) > 0)
    
    def test_detect_anomalies_no_data(self):
        """Test anomaly detection with no data."""
        self.mock_db.get_user_token_usage.return_value = []
        
        anomalies = self.monitoring.detect_anomalies()
        
        self.assertEqual(len(anomalies), 0)
    
    def test_send_alerts_success(self):
        """Test successful alert sending."""
        alert_config = AlertingConfig(
            enabled=True,
            check_interval=60,
            thresholds={'cpu_usage': 80}
        )
        
        self.monitoring.configure(alert_config)
        
        # Mock successful alert sending
        self.mock_db.send_alert.return_value = True
        
        result = self.monitoring.send_alerts('user1', 'High CPU usage', AlertSeverity.HIGH)
        
        self.assertTrue(result)
        self.mock_db.send_alert.assert_called_once()
    
    def test_send_alerts_disabled(self):
        """Test alert sending when disabled."""
        alert_config = AlertingConfig(
            enabled=False,
            check_interval=60,
            thresholds={'cpu_usage': 80}
        )
        
        self.monitoring.configure(alert_config)
        
        result = self.monitoring.send_alerts('user1', 'High CPU usage', AlertSeverity.HIGH)
        
        self.assertFalse(result)
    
    def test_export_metrics_success(self):
        """Test successful metrics export."""
        self.mock_db.get_system_health.return_value = {
            'cpu_usage': 45.5,
            'memory_usage': 60.2
        }
        
        metrics = self.monitoring.export_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('timestamp', metrics)
        self.assertIn('system_metrics', metrics)
        self.assertIn('monitoring_metrics', metrics)
    
    def test_get_performance_metrics(self):
        """Test performance metrics retrieval."""
        metrics = self.monitoring.get_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_checks', metrics)
        self.assertIn('successful_checks', metrics)
        self.assertIn('failed_checks', metrics)
    
    def test_configure(self):
        """Test monitoring configuration."""
        config = AlertingConfig(
            enabled=True,
            check_interval=120,
            thresholds={'cpu_usage': 90}
        )
        
        self.monitoring.configure(config)
        
        self.assertTrue(self.monitoring.config['alerting']['enabled'])
        self.assertEqual(self.monitoring.config['alerting']['check_interval'], 120)
        self.assertEqual(self.monitoring.config['alerting']['thresholds']['cpu_usage'], 90)


class TestTokenAlertingSystem(unittest.TestCase):
    """Test cases for TokenAlertingSystem."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.alerting = TokenAlertingSystem(self.mock_db)
        
        # Mock alert data
        self.mock_alert = Alert(
            alert_id='alert1',
            user_id='user1',
            message='High token usage detected',
            severity=AlertSeverity.HIGH,
            timestamp=datetime.utcnow(),
            resolved=False
        )
    
    def test_init(self):
        """Test TokenAlertingSystem initialization."""
        self.assertEqual(self.alerting.db, self.mock_db)
        self.assertIsInstance(self.alerting.config, AlertingConfig)
        self.assertIsInstance(self.alerting.metrics, dict)
    
    def test_configure_success(self):
        """Test successful alerting configuration."""
        config = AlertingConfig(
            enabled=True,
            check_interval=60,
            thresholds={'cpu_usage': 80}
        )
        
        self.alerting.configure(config)
        
        self.assertTrue(self.alerting.config.enabled)
        self.assertEqual(self.alerting.config.check_interval, 60)
        self.assertEqual(self.alerting.config.thresholds['cpu_usage'], 80)
    
    def test_add_alert_success(self):
        """Test successful alert addition."""
        self.mock_db.add_alert.return_value = True
        
        result = self.alerting.add_alert(
            user_id='user1',
            message='Test alert',
            severity=AlertSeverity.HIGH
        )
        
        self.assertTrue(result)
        self.mock_db.add_alert.assert_called_once()
    
    def test_add_alert_failure(self):
        """Test alert addition failure."""
        self.mock_db.add_alert.return_value = False
        
        result = self.alerting.add_alert(
            user_id='user1',
            message='Test alert',
            severity=AlertSeverity.HIGH
        )
        
        self.assertFalse(result)
    
    def test_get_active_alerts_success(self):
        """Test successful active alerts retrieval."""
        self.mock_db.get_active_alerts.return_value = [self.mock_alert]
        
        alerts = self.alerting.get_active_alerts('user1')
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_id, 'alert1')
        self.assertEqual(alerts[0].user_id, 'user1')
    
    def test_get_active_alerts_no_data(self):
        """Test active alerts retrieval with no data."""
        self.mock_db.get_active_alerts.return_value = []
        
        alerts = self.alerting.get_active_alerts('user1')
        
        self.assertEqual(len(alerts), 0)
    
    def test_get_alert_history_success(self):
        """Test successful alert history retrieval."""
        self.mock_db.get_alert_history.return_value = [self.mock_alert]
        
        alerts = self.alerting.get_alert_history('user1', days=7)
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_id, 'alert1')
    
    def test_acknowledge_alert_success(self):
        """Test successful alert acknowledgment."""
        self.mock_db.acknowledge_alert.return_value = True
        
        result = self.alerting.acknowledge_alert('alert1')
        
        self.assertTrue(result)
        self.mock_db.acknowledge_alert.assert_called_once_with('alert1')
    
    def test_acknowledge_alert_not_found(self):
        """Test alert acknowledgment when alert not found."""
        self.mock_db.acknowledge_alert.return_value = False
        
        result = self.alerting.acknowledge_alert('alert1')
        
        self.assertFalse(result)
    
    def test_resolve_alert_success(self):
        """Test successful alert resolution."""
        self.mock_db.resolve_alert.return_value = True
        
        result = self.alerting.resolve_alert('alert1')
        
        self.assertTrue(result)
        self.mock_db.resolve_alert.assert_called_once_with('alert1')
    
    def test_resolve_alert_not_found(self):
        """Test alert resolution when alert not found."""
        self.mock_db.resolve_alert.return_value = False
        
        result = self.alerting.resolve_alert('alert1')
        
        self.assertFalse(result)
    
    def test_get_alerting_metrics(self):
        """Test alerting metrics retrieval."""
        metrics = self.alerting.get_alerting_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_alerts', metrics)
        self.assertIn('active_alerts', metrics)
        self.assertIn('resolved_alerts', metrics)
        self.assertIn('last_error', metrics)


class TestTokenAnalytics(unittest.TestCase):
    """Test cases for TokenAnalytics."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.analytics = TokenAnalytics(self.mock_db)
        
        # Mock usage data
        self.mock_usage_data = [
            {
                'user_id': 'user1',
                'session_id': 'session1',
                'tokens_used': 100,
                'api_endpoint': 'chat/completions',
                'priority_level': 'Medium',
                'timestamp': datetime.utcnow()
            },
            {
                'user_id': 'user1',
                'session_id': 'session2',
                'tokens_used': 150,
                'api_endpoint': 'chat/completions',
                'priority_level': 'High',
                'timestamp': datetime.utcnow() - timedelta(hours=1)
            }
        ]
    
    def test_init(self):
        """Test TokenAnalytics initialization."""
        self.assertEqual(self.analytics.db, self.mock_db)
        self.assertIsInstance(self.analytics.config, dict)
        self.assertIsInstance(self.analytics.metrics, dict)
    
    def test_generate_usage_report_success(self):
        """Test successful usage report generation."""
        self.mock_db.get_user_token_usage.return_value = self.mock_usage_data
        
        report = self.analytics.generate_usage_report('user1', days=7)
        
        self.assertIsNotNone(report)
        self.assertEqual(report.user_id, 'user1')
        self.assertEqual(report.total_tokens, 250)
        self.assertEqual(report.total_requests, 2)
        self.assertEqual(report.average_tokens_per_request, 125.0)
    
    def test_generate_usage_report_no_data(self):
        """Test usage report generation with no data."""
        self.mock_db.get_user_token_usage.return_value = []
        
        report = self.analytics.generate_usage_report('user1', days=7)
        
        self.assertIsNotNone(report)
        self.assertEqual(report.total_tokens, 0)
        self.assertEqual(report.total_requests, 0)
        self.assertEqual(report.average_tokens_per_request, 0.0)
    
    def test_export_metrics_success(self):
        """Test successful metrics export."""
        self.mock_db.get_system_health.return_value = {
            'cpu_usage': 45.5,
            'memory_usage': 60.2
        }
        
        metrics = self.analytics.export_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('timestamp', metrics)
        self.assertIn('system_metrics', metrics)
        self.assertIn('analytics_metrics', metrics)
    
    def test_get_analytics_metrics(self):
        """Test analytics metrics retrieval."""
        metrics = self.analytics.get_analytics_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_reports_generated', metrics)
        self.assertIn('forecast_accuracy', metrics)
        self.assertIn('recommendations_generated', metrics)


class TestTokenDashboard(unittest.TestCase):
    """Test cases for TokenDashboard."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.dashboard = TokenDashboard(self.mock_db)
        
        # Mock monitoring system
        self.mock_monitoring = MagicMock()
        self.dashboard.monitoring = self.mock_monitoring
        
        # Mock alerting system
        self.mock_alerting = MagicMock()
        self.dashboard.alerting = self.mock_alerting
    
    def test_init(self):
        """Test TokenDashboard initialization."""
        self.assertEqual(self.dashboard.db, self.mock_db)
        self.assertIsInstance(self.dashboard.config, dict)
        self.assertEqual(len(self.dashboard.widgets), 0)
    
    def test_add_widget_success(self):
        """Test successful widget addition."""
        widget = UsageStatusWidget(self.mock_monitoring)
        
        self.dashboard.add_widget(widget)
        
        self.assertEqual(len(self.dashboard.widgets), 1)
        self.assertEqual(self.dashboard.widgets[0], widget)
    
    def test_add_widget_max_limit(self):
        """Test widget addition at max limit."""
        # Add max widgets
        for i in range(self.dashboard.config['max_widgets']):
            widget = UsageStatusWidget(self.mock_monitoring)
            self.dashboard.add_widget(widget)
        
        # Try to add one more
        widget = UsageStatusWidget(self.mock_monitoring)
        self.dashboard.add_widget(widget)
        
        self.assertEqual(len(self.dashboard.widgets), self.dashboard.config['max_widgets'])
    
    def test_remove_widget_success(self):
        """Test successful widget removal."""
        widget = UsageStatusWidget(self.mock_monitoring)
        self.dashboard.add_widget(widget)
        
        self.dashboard.remove_widget('Token Usage Status')
        
        self.assertEqual(len(self.dashboard.widgets), 0)
    
    def test_remove_widget_not_found(self):
        """Test widget removal when widget not found."""
        widget = UsageStatusWidget(self.mock_monitoring)
        self.dashboard.add_widget(widget)
        
        self.dashboard.remove_widget('Non-existent Widget')
        
        self.assertEqual(len(self.dashboard.widgets), 1)
    
    def test_clear_widgets(self):
        """Test widget clearing."""
        widget1 = UsageStatusWidget(self.mock_monitoring)
        widget2 = SystemHealthWidget(self.mock_monitoring)
        
        self.dashboard.add_widget(widget1)
        self.dashboard.add_widget(widget2)
        
        self.dashboard.clear_widgets()
        
        self.assertEqual(len(self.dashboard.widgets), 0)
    
    def test_setup_default_widgets(self):
        """Test default widget setup."""
        self.dashboard.setup_default_widgets('user1')
        
        self.assertEqual(len(self.dashboard.widgets), 3)
        widget_titles = [w.title for w in self.dashboard.widgets]
        self.assertIn('Token Usage Status', widget_titles)
        self.assertIn('System Health', widget_titles)
        self.assertIn('Active Alerts', widget_titles)
    
    def test_render_dashboard_no_widgets(self):
        """Test dashboard rendering with no widgets."""
        output = self.dashboard.render_dashboard()
        
        self.assertEqual(output, 'No widgets configured')
    
    def test_render_dashboard_with_widgets(self):
        """Test dashboard rendering with widgets."""
        widget = UsageStatusWidget(self.mock_monitoring)
        self.dashboard.add_widget(widget)
        
        output = self.dashboard.render_dashboard()
        
        self.assertIsInstance(output, str)
        self.assertIn('Token Usage Status', output)


class TestTokenCLI(unittest.TestCase):
    """Test cases for TokenCLI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.cli = TokenCLI(self.mock_db)
        
        # Mock monitoring system
        self.mock_monitoring = MagicMock()
        self.cli.monitoring = self.mock_monitoring
        
        # Mock alerting system
        self.mock_alerting = MagicMock()
        self.cli.alerting = self.mock_alerting
        
        # Mock analytics system
        self.mock_analytics = MagicMock()
        self.cli.analytics = self.mock_analytics
    
    def test_init(self):
        """Test TokenCLI initialization."""
        self.assertEqual(self.cli.db, self.mock_db)
        self.assertIsInstance(self.cli.monitoring, MagicMock)
        self.assertIsInstance(self.cli.alerting, MagicMock)
        self.assertIsInstance(self.cli.analytics, MagicMock)
    
    def test_setup_parser(self):
        """Test argument parser setup."""
        parser = self.cli.setup_parser()
        
        self.assertIsNotNone(parser)
        self.assertIn('status', parser._subparsers._actions[1].choices)
        self.assertIn('dashboard', parser._subparsers._actions[1].choices)
        self.assertIn('report', parser._subparsers._actions[1].choices)
        self.assertIn('alerts', parser._subparsers._actions[1].choices)
        self.assertIn('analytics', parser._subparsers._actions[1].choices)
        self.assertIn('system', parser._subparsers._actions[1].choices)
    
    def test_handle_status_success(self):
        """Test successful status command handling."""
        mock_status = MagicMock()
        mock_status.user_id = 'user1'
        mock_status.total_tokens = 1000
        mock_status.total_requests = 10
        mock_status.average_tokens_per_request = 100.0
        mock_status.quota_used_percentage = 75.0
        
        self.mock_monitoring.get_token_usage_status.return_value = mock_status
        
        # Capture stdout
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.cli.handle_status(type('Args', (), {'user': 'user1', 'json': False})())
        
        output = f.getvalue()
        
        self.assertIn('TOKEN USAGE STATUS', output)
        self.assertIn('user1', output)
        self.assertIn('1000', output)
    
    def test_handle_status_json(self):
        """Test status command with JSON output."""
        mock_status = MagicMock()
        mock_status.user_id = 'user1'
        mock_status.total_tokens = 1000
        mock_status.total_requests = 10
        mock_status.average_tokens_per_request = 100.0
        mock_status.quota_used_percentage = 75.0
        
        self.mock_monitoring.get_token_usage_status.return_value = mock_status
        
        # Capture stdout
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.cli.handle_status(type('Args', (), {'user': 'user1', 'json': True})())
        
        output = f.getvalue()
        
        self.assertIn('"user_id": "user1"', output)
        self.assertIn('"total_tokens": 1000', output)
    
    def test_handle_alerts_list_success(self):
        """Test successful alerts list command handling."""
        mock_alert = MagicMock()
        mock_alert.severity.value = 'HIGH'
        mock_alert.message = 'Test alert'
        mock_alert.user_id = 'user1'
        mock_alert.timestamp = datetime.utcnow()
        mock_alert.alert_id = 'alert1'
        
        self.mock_alerting.get_active_alerts.return_value = [mock_alert]
        
        # Capture stdout
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.cli.handle_alerts(type('Args', (), {'list': True, 'user': 'user1'})())
        
        output = f.getvalue()
        
        self.assertIn('ACTIVE ALERTS', output)
        self.assertIn('HIGH', output)
        self.assertIn('Test alert', output)
    
    def test_handle_alerts_list_no_data(self):
        """Test alerts list command with no data."""
        self.mock_alerting.get_active_alerts.return_value = []
        
        # Capture stdout
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.cli.handle_alerts(type('Args', (), {'list': True, 'user': 'user1'})())
        
        output = f.getvalue()
        
        self.assertEqual(output.strip(), 'No active alerts')
    
    def test_handle_analytics_forecast_success(self):
        """Test successful analytics forecast command handling."""
        mock_report = MagicMock()
        mock_report.forecast_data = MagicMock()
        mock_report.forecast_data.predicted_usage = 1000
        mock_report.forecast_data.confidence_interval = (800, 1200)
        mock_report.forecast_data.accuracy_score = 0.85
        mock_report.forecast_data.factors = ['Increasing usage trend']
        
        self.mock_analytics.generate_usage_report.return_value = mock_report
        
        # Capture stdout
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.cli.handle_analytics(type('Args', (), {'forecast': True, 'user': 'user1', 'days': 7})())
        
        output = f.getvalue()
        
        self.assertIn('USAGE FORECAST', output)
        self.assertIn('1000', output)
        self.assertIn('0.85', output)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete monitoring system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        
        # Create system components
        self.monitoring = TokenMonitoringSystem(self.mock_db)
        self.alerting = TokenAlertingSystem(self.mock_db)
        self.analytics = TokenAnalytics(self.mock_db)
        self.dashboard = TokenDashboard(self.mock_db)
        self.cli = TokenCLI(self.mock_db)
    
    def test_end_to_end_monitoring_workflow(self):
        """Test complete monitoring workflow."""
        # Mock database responses
        mock_usage_data = [
            {
                'user_id': 'user1',
                'session_id': 'session1',
                'tokens_used': 100,
                'api_endpoint': 'chat/completions',
                'priority_level': 'Medium',
                'timestamp': datetime.utcnow()
            }
        ]
        
        self.mock_db.get_user_token_usage.return_value = mock_usage_data
        self.mock_db.get_system_health.return_value = {
            'cpu_usage': 45.5,
            'memory_usage': 60.2,
            'error_rate': 1.5
        }
        
        # Test monitoring
        usage_status = self.monitoring.get_token_usage_status('user1')
        self.assertIsNotNone(usage_status)
        self.assertEqual(usage_status.total_tokens, 100)
        
        # Test alerting
        alert_config = AlertingConfig(
            enabled=True,
            check_interval=60,
            thresholds={'cpu_usage': 80}
        )
        self.alerting.configure(alert_config)
        
        # Test analytics
        report = self.analytics.generate_usage_report('user1', days=7)
        self.assertIsNotNone(report)
        self.assertEqual(report.total_tokens, 100)
        
        # Test dashboard
        self.dashboard.setup_default_widgets('user1')
        self.assertEqual(len(self.dashboard.widgets), 3)
        
        # Test CLI
        args = type('Args', (), {
            'command': 'status',
            'user': 'user1',
            'json': False
        })()
        
        # Capture stdout
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.cli.handle_status(args)
        
        output = f.getvalue()
        self.assertIn('TOKEN USAGE STATUS', output)
    
    def test_error_handling(self):
        """Test error handling across components."""
        # Mock database to raise exceptions
        self.mock_db.get_user_token_usage.side_effect = Exception("Database error")
        self.mock_db.get_system_health.side_effect = Exception("Database error")
        
        # Test monitoring error handling
        usage_status = self.monitoring.get_token_usage_status('user1')
        self.assertIsNotNone(usage_status)
        self.assertEqual(usage_status.total_tokens, 0)
        
        # Test analytics error handling
        report = self.analytics.generate_usage_report('user1', days=7)
        self.assertIsNotNone(report)
        self.assertEqual(report.total_tokens, 0)
        
        # Test alerting error handling
        alert_config = AlertingConfig(
            enabled=True,
            check_interval=60,
            thresholds={'cpu_usage': 80}
        )
        self.alerting.configure(alert_config)
        
        # Test CLI error handling
        args = type('Args', (), {
            'command': 'status',
            'user': 'user1',
            'json': False
        })()
        
        # Should not raise exception
        self.cli.handle_status(args)


class TestPerformance(unittest.TestCase):
    """Performance tests for the monitoring system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.monitoring = TokenMonitoringSystem(self.mock_db)
        self.alerting = TokenAlertingSystem(self.mock_db)
        self.analytics = TokenAnalytics(self.mock_db)
    
    def test_monitoring_performance(self):
        """Test monitoring system performance."""
        import time
        
        # Mock large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                'user_id': f'user{i}',
                'session_id': f'session{i}',
                'tokens_used': 100 + i,
                'api_endpoint': 'chat/completions',
                'priority_level': 'Medium',
                'timestamp': datetime.utcnow() - timedelta(hours=i)
            })
        
        self.mock_db.get_user_token_usage.return_value = large_dataset
        
        # Measure performance
        start_time = time.time()
        usage_status = self.monitoring.get_token_usage_status()
        end_time = time.time()
        
        # Should process 1000 records in reasonable time
        self.assertLess(end_time - start_time, 1.0)
        self.assertEqual(usage_status.total_tokens, sum(record['tokens_used'] for record in large_dataset))
    
    def test_alerting_performance(self):
        """Test alerting system performance."""
        import time
        
        # Configure alerting
        alert_config = AlertingConfig(
            enabled=True,
            check_interval=60,
            thresholds={'cpu_usage': 80}
        )
        self.alerting.configure(alert_config)
        
        # Measure performance
        start_time = time.time()
        result = self.alerting.add_alert('user1', 'Test alert', AlertSeverity.HIGH)
        end_time = time.time()
        
        # Should add alert quickly
        self.assertLess(end_time - start_time, 0.1)
        self.assertTrue(result)
    
    def test_analytics_performance(self):
        """Test analytics system performance."""
        import time
        
        # Mock large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                'user_id': f'user{i % 10}',  # 10 unique users
                'session_id': f'session{i}',
                'tokens_used': 100 + i,
                'api_endpoint': 'chat/completions',
                'priority_level': 'Medium',
                'timestamp': datetime.utcnow() - timedelta(hours=i)
            })
        
        self.mock_db.get_user_token_usage.return_value = large_dataset
        
        # Measure performance
        start_time = time.time()
        report = self.analytics.generate_usage_report(days=7)
        end_time = time.time()
        
        # Should generate report in reasonable time
        self.assertLess(end_time - start_time, 2.0)
        self.assertEqual(report.total_tokens, sum(record['tokens_used'] for record in large_dataset))


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)