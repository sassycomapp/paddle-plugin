#!/usr/bin/env python3
"""
Standalone Token Usage Monitoring Script

This script provides comprehensive monitoring capabilities for the token management system.
It can be run as a standalone service or as a periodic monitoring tool.
"""

import argparse
import logging
import sys
import time
import json
import signal
import schedule
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from simba.simba.database.postgres import PostgresDB
from src.token_monitoring import TokenMonitoringSystem
from src.token_alerting import TokenAlertingSystem, AlertingConfig, NotificationChannel
from src.token_analytics import TokenAnalytics, ReportFormat
from src.token_dashboard import TokenDashboard


class TokenMonitoringService:
    """
    Standalone monitoring service for token usage.
    
    Provides continuous monitoring, alerting, and reporting capabilities.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the monitoring service.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.db = PostgresDB()
        self.monitoring = TokenMonitoringSystem(self.db)
        self.alerting = TokenAlertingSystem(self.db)
        self.analytics = TokenAnalytics(self.db)
        self.dashboard = TokenDashboard(self.db)
        
        # Service state
        self.running = False
        self.schedule_job = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("TokenMonitoringService initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            'monitoring': {
                'check_interval': 60,  # seconds
                'alert_thresholds': {
                    'cpu_usage': 80,
                    'memory_usage': 85,
                    'error_rate': 5.0,
                    'response_time': 2.0,
                    'quota_usage': 90
                }
            },
            'alerting': {
                'enabled': True,
                'channels': [
                    {
                        'type': 'console',
                        'enabled': True
                    },
                    {
                        'type': 'email',
                        'enabled': False,
                        'config': {
                            'smtp_server': 'localhost',
                            'smtp_port': 587,
                            'username': '',
                            'password': '',
                            'recipients': []
                        }
                    }
                ]
            },
            'reporting': {
                'enabled': True,
                'schedule': 'daily',
                'format': 'json',
                'retention_days': 30
            },
            'logging': {
                'level': 'INFO',
                'file': 'token_monitoring.log',
                'max_size': '10MB',
                'backup_count': 5
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge with default config
                    for key, value in user_config.items():
                        if key in default_config:
                            default_config[key].update(value)
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
        
        return default_config
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def start(self):
        """Start the monitoring service."""
        if self.running:
            logger.warning("Service already running")
            return
        
        self.running = True
        logger.info("Starting TokenMonitoringService...")
        
        # Setup alerting configuration
        if self.config['alerting']['enabled']:
            alert_config = AlertingConfig(
                enabled=True,
                check_interval=self.config['monitoring']['check_interval'],
                thresholds=self.config['monitoring']['alert_thresholds']
            )
            self.alerting.configure(alert_config)
            
            # Setup notification channels
            for channel_config in self.config['alerting']['channels']:
                if channel_config['enabled']:
                    if channel_config['type'] == 'console':
                        channel = NotificationChannel.CONSOLE
                    elif channel_config['type'] == 'email':
                        channel = NotificationChannel.EMAIL
                        # Configure email settings
                        self.alerting.configure_email(
                            smtp_server=channel_config['config']['smtp_server'],
                            smtp_port=channel_config['config']['smtp_port'],
                            username=channel_config['config']['username'],
                            password=channel_config['config']['password'],
                            recipients=channel_config['config']['recipients']
                        )
                    else:
                        continue
                    
                    self.alerting.add_notification_channel(channel)
        
        # Setup reporting schedule
        if self.config['reporting']['enabled']:
            schedule_type = self.config['reporting']['schedule']
            if schedule_type == 'hourly':
                schedule.every().hour.do(self._generate_report)
            elif schedule_type == 'daily':
                schedule.every().day.at("09:00").do(self._generate_report)
            elif schedule_type == 'weekly':
                schedule.every().week.do(self._generate_report)
        
        # Start monitoring loop
        self._monitoring_loop()
    
    def stop(self):
        """Stop the monitoring service."""
        self.running = False
        logger.info("Stopping TokenMonitoringService...")
        
        if self.schedule_job:
            schedule.cancel_job(self.schedule_job)
        
        logger.info("TokenMonitoringService stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                logger.info("Starting monitoring cycle...")
                
                # Check system health
                health = self.monitoring.get_system_health()
                if health:
                    logger.info(f"System health - CPU: {health.cpu_usage:.1f}%, "
                              f"Memory: {health.memory_usage:.1f}%, "
                              f"Errors: {health.error_rate:.2f}%")
                
                # Check token usage
                usage_status = self.monitoring.get_token_usage_status()
                if usage_status:
                    logger.info(f"Token usage - Total: {usage_status.total_tokens:,}, "
                              f"Requests: {usage_status.total_requests:,}, "
                              f"Quota used: {usage_status.quota_used_percentage:.1f}%")
                
                # Check for anomalies
                anomalies = self.monitoring.detect_anomalies()
                if anomalies:
                    logger.warning(f"Detected {len(anomalies)} anomalies")
                    for anomaly in anomalies:
                        logger.warning(f"Anomaly: {anomaly.description}")
                
                # Send alerts if needed
                if self.config['alerting']['enabled']:
                    alerts = self.alerting.get_active_alerts()
                    if alerts:
                        logger.warning(f"Active alerts: {len(alerts)}")
                        for alert in alerts:
                            logger.warning(f"Alert: {alert.message}")
                
                # Wait for next cycle
                time.sleep(self.config['monitoring']['check_interval'])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Wait before retry
    
    def _generate_report(self):
        """Generate periodic report."""
        try:
            logger.info("Generating periodic report...")
            
            # Generate analytics report
            report = self.analytics.generate_usage_report(
                days=7,
                format=ReportFormat.JSON
            )
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = Path(f"reports/token_usage_report_{timestamp}.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Report saved to: {report_path}")
            
            # Clean up old reports
            self._cleanup_old_reports()
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
    
    def _cleanup_old_reports(self):
        """Clean up old reports based on retention policy."""
        try:
            retention_days = self.config['reporting']['retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            reports_dir = Path("reports")
            if reports_dir.exists():
                for report_file in reports_dir.glob("token_usage_report_*.json"):
                    if report_file.stat().st_mtime < cutoff_date.timestamp():
                        report_file.unlink()
                        logger.info(f"Deleted old report: {report_file}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old reports: {e}")
    
    def run_once(self):
        """Run monitoring once and exit."""
        logger.info("Running monitoring cycle once...")
        
        try:
            # Check system health
            health = self.monitoring.get_system_health()
            if health:
                print(f"System Health:")
                print(f"  CPU Usage: {health.cpu_usage:.1f}%")
                print(f"  Memory Usage: {health.memory_usage:.1f}%")
                print(f"  Error Rate: {health.error_rate:.2f}%")
                print(f"  Response Time: {health.average_response_time:.2f}s")
            
            # Check token usage
            usage_status = self.monitoring.get_token_usage_status()
            if usage_status:
                print(f"\nToken Usage:")
                print(f"  Total Tokens: {usage_status.total_tokens:,}")
                print(f"  Total Requests: {usage_status.total_requests:,}")
                print(f"  Average Tokens/Request: {usage_status.average_tokens_per_request:.1f}")
                print(f"  Quota Used: {usage_status.quota_used_percentage:.1f}%")
                print(f"  Quota Remaining: {usage_status.quota_remaining:,}")
            
            # Check for anomalies
            anomalies = self.monitoring.detect_anomalies()
            if anomalies:
                print(f"\nAnomalies Detected ({len(anomalies)}):")
                for anomaly in anomalies:
                    print(f"  - {anomaly.description}")
            
            # Check alerts
            alerts = self.alerting.get_active_alerts()
            if alerts:
                print(f"\nActive Alerts ({len(alerts)}):")
                for alert in alerts:
                    print(f"  [{alert.severity.value}] {alert.message}")
            
            print("\nMonitoring cycle completed successfully.")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            print(f"Error: {e}")
            sys.exit(1)


def setup_logging(config: Dict[str, Any]):
    """Setup logging configuration."""
    log_config = config.get('logging', {})
    
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_config.get('file', 'token_monitoring.log'))
        ]
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Token Usage Monitoring Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config.json --service
  %(prog)s --once
  %(prog)s --dashboard --real-time
  %(prog)s --report --days 7
        """
    )
    
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--service', action='store_true', help='Run as continuous service')
    parser.add_argument('--once', action='store_true', help='Run monitoring once and exit')
    parser.add_argument('--dashboard', action='store_true', help='Start interactive dashboard')
    parser.add_argument('--real-time', action='store_true', help='Real-time dashboard updates')
    parser.add_argument('--report', action='store_true', help='Generate usage report')
    parser.add_argument('--days', type=int, default=7, help='Days for report')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='Report format')
    parser.add_argument('--output', help='Output file for report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    config = TokenMonitoringService._load_config(args.config)
    if args.verbose:
        config['logging']['level'] = 'DEBUG'
    setup_logging(config)
    
    global logger
    logger = logging.getLogger(__name__)
    
    try:
        # Create monitoring service
        service = TokenMonitoringService(args.config)
        
        if args.dashboard:
            # Start dashboard
            print("Starting interactive dashboard...")
            print("Press Ctrl+C to stop")
            service.dashboard.start_real_time()
        
        elif args.report:
            # Generate report
            print("Generating usage report...")
            if args.format == 'json':
                report = service.analytics.generate_usage_report(days=args.days, format=ReportFormat.JSON)
                output = json.dumps(report, indent=2, default=str)
            else:
                output = service.dashboard.generate_report(days=args.days)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"Report saved to: {args.output}")
            else:
                print(output)
        
        elif args.once:
            # Run monitoring once
            service.run_once()
        
        elif args.service:
            # Run as service
            print("Starting token monitoring service...")
            print("Press Ctrl+C to stop")
            service.start()
            while service.running:
                time.sleep(1)
        
        else:
            # Default: show help
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()