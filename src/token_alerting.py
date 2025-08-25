"""
Token Alerting and Notification System

This module provides comprehensive alerting and notification capabilities for the token management system.
It supports configurable alert thresholds, multiple notification channels, alert escalation,
and automated response workflows.
"""

import logging
import json
import asyncio
import smtplib
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import yaml

from simba.simba.database.postgres import PostgresDB
from src.token_monitoring import TokenMonitoringSystem, TokenUsageStatus, SystemHealthMetrics, MonitoringAlert, AlertSeverity

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Notification types."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    PUSH = "push"
    TELEGRAM = "telegram"


class AlertCondition(Enum):
    """Alert conditions."""
    USAGE_THRESHOLD = "usage_threshold"
    QUOTA_EXCEEDED = "quota_exceeded"
    SYSTEM_HEALTH = "system_health"
    ANOMALY_DETECTED = "anomaly_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    COST_THRESHOLD = "cost_threshold"


@dataclass
class NotificationChannel:
    """Notification channel configuration."""
    channel_id: str
    channel_type: NotificationType
    name: str
    config: Dict[str, Any]
    enabled: bool = True
    priority: int = 1  # 1=highest, 5=lowest
    retry_count: int = 3
    retry_delay: int = 60  # seconds
    last_used: Optional[datetime] = None


@dataclass
class AlertRule:
    """Alert rule configuration."""
    rule_id: str
    name: str
    condition: AlertCondition
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    user_id_filter: Optional[str] = None
    api_endpoint_filter: Optional[str] = None
    time_window: Optional[int] = None  # minutes
    cooldown_period: int = 60  # minutes
    notification_channels: Optional[List[str]] = None
    escalation_rules: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = []
        if self.escalation_rules is None:
            self.escalation_rules = []


@dataclass
class Notification:
    """Notification message."""
    notification_id: str
    alert_id: str
    channel_type: NotificationType
    recipient: str
    subject: str
    message: str
    status: str = "pending"
    sent_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AlertingConfig:
    """Configuration for the alerting system."""
    enable_alerting: bool = True
    default_severity: AlertSeverity = AlertSeverity.MEDIUM
    max_alerts_per_user: int = 10
    alert_retention_days: int = 30
    enable_escalation: bool = True
    escalation_timeout: int = 300  # seconds
    enable_suppression: bool = True
    suppression_window: int = 300  # seconds
    enable_cost_alerts: bool = True
    cost_alert_threshold: float = 100.0  # dollars
    enable_system_health_alerts: bool = True
    health_alert_thresholds: Optional[Dict[str, float]] = None
    notification_batch_size: int = 10
    notification_batch_timeout: int = 30  # seconds
    
    def __post_init__(self):
        if self.health_alert_thresholds is None:
            self.health_alert_thresholds = {
                'cpu_usage': 80.0,
                'memory_usage': 85.0,
                'disk_usage': 90.0,
                'error_rate': 5.0,
                'response_time': 2.0  # seconds
            }


class TokenAlertingSystem:
    """
    Comprehensive token alerting and notification system.
    
    Provides configurable alerting, multiple notification channels,
    escalation rules, and automated response workflows.
    """
    
    def __init__(self, db: Optional[PostgresDB] = None, config: Optional[AlertingConfig] = None):
        """
        Initialize the alerting system.
        
        Args:
            db: Database instance for alert storage
            config: Alerting configuration
        """
        self.db = db or PostgresDB()
        self.config = config or AlertingConfig()
        
        # Alert storage
        self._alerts: Dict[str, MonitoringAlert] = {}
        self._alert_rules: Dict[str, AlertRule] = {}
        self._notification_channels: Dict[str, NotificationChannel] = {}
        self._notifications: Dict[str, Notification] = {}
        
        # Alert state tracking
        self._alert_suppressions: Dict[str, datetime] = {}
        self._alert_cooldowns: Dict[str, datetime] = {}
        self._escalation_states: Dict[str, Dict[str, Any]] = {}
        
        # Threading
        self._notification_thread = None
        self._stop_event = threading.Event()
        self._notification_queue = asyncio.Queue()
        
        # Performance metrics
        self.metrics = {
            'total_alerts': 0,
            'alerts_sent': 0,
            'alerts_failed': 0,
            'notifications_sent': 0,
            'notifications_failed': 0,
            'escalations_triggered': 0,
            'suppressions_applied': 0,
            'last_error': None,
            'error_timestamp': None
        }
        
        # Load default configuration
        self._load_default_configuration()
        
        # Start notification processor
        if self.config.enable_alerting:
            self._start_notification_processor()
        
        logger.info("TokenAlertingSystem initialized")
    
    def _load_default_configuration(self):
        """Load default alert rules and notification channels."""
        # Default alert rules
        default_rules = [
            AlertRule(
                rule_id="high_usage_warning",
                name="High Usage Warning",
                condition=AlertCondition.USAGE_THRESHOLD,
                threshold=75.0,  # 75%
                severity=AlertSeverity.MEDIUM,
                notification_channels=["email_default"]
            ),
            AlertRule(
                rule_id="critical_usage",
                name="Critical Usage",
                condition=AlertCondition.USAGE_THRESHOLD,
                threshold=90.0,  # 90%
                severity=AlertSeverity.HIGH,
                notification_channels=["email_default", "slack_critical"]
            ),
            AlertRule(
                rule_id="quota_exceeded",
                name="Quota Exceeded",
                condition=AlertCondition.QUOTA_EXCEEDED,
                threshold=100.0,  # 100%
                severity=AlertSeverity.CRITICAL,
                notification_channels=["email_default", "slack_critical", "sms_admin"]
            ),
            AlertRule(
                rule_id="system_health",
                name="System Health Alert",
                condition=AlertCondition.SYSTEM_HEALTH,
                threshold=80.0,  # 80%
                severity=AlertSeverity.HIGH,
                notification_channels=["email_default", "slack_system"]
            )
        ]
        
        # Default notification channels
        default_channels = [
            NotificationChannel(
                channel_id="email_default",
                channel_type=NotificationType.EMAIL,
                name="Default Email",
                config={
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'from_address': 'alerts@yourdomain.com',
                    'use_tls': True
                }
            ),
            NotificationChannel(
                channel_id="slack_critical",
                channel_type=NotificationType.SLACK,
                name="Critical Slack",
                config={
                    'webhook_url': '',
                    'channel': '#alerts',
                    'username': 'TokenBot'
                }
            ),
            NotificationChannel(
                channel_id="sms_admin",
                channel_type=NotificationType.SMS,
                name="Admin SMS",
                config={
                    'provider': 'twilio',
                    'account_sid': '',
                    'auth_token': '',
                    'from_number': '',
                    'to_numbers': []
                }
            )
        ]
        
        # Add default rules and channels
        for rule in default_rules:
            self.add_alert_rule(rule)
        
        for channel in default_channels:
            self.add_notification_channel(channel)
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self._alert_rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule."""
        if rule_id in self._alert_rules:
            del self._alert_rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add a notification channel."""
        self._notification_channels[channel.channel_id] = channel
        logger.info(f"Added notification channel: {channel.name}")
    
    def remove_notification_channel(self, channel_id: str):
        """Remove a notification channel."""
        if channel_id in self._notification_channels:
            del self._notification_channels[channel_id]
            logger.info(f"Removed notification channel: {channel_id}")
    
    def check_alert_conditions(self, status: TokenUsageStatus, health_metrics: Optional[SystemHealthMetrics] = None):
        """Check all alert conditions and generate alerts if needed."""
        alerts = []
        
        try:
            # Check usage-based alerts
            for rule in self._alert_rules.values():
                if not rule.enabled:
                    continue
                
                # Apply user filter
                if rule.user_id_filter and status.user_id != rule.user_id_filter:
                    continue
                
                # Check condition
                should_alert = False
                
                if rule.condition == AlertCondition.USAGE_THRESHOLD:
                    should_alert = status.usage_percentage >= rule.threshold
                
                elif rule.condition == AlertCondition.QUOTA_EXCEEDED:
                    should_alert = status.usage_percentage >= 100.0
                
                elif rule.condition == AlertCondition.SYSTEM_HEALTH and health_metrics:
                    should_alert = self._check_system_health_threshold(health_metrics, rule.threshold)
                
                if should_alert:
                    alert = self._create_alert_from_rule(rule, status, health_metrics)
                    alerts.append(alert)
            
            # Check cost alerts if enabled
            if self.config.enable_cost_alerts:
                cost_alert = self._check_cost_alerts(status)
                if cost_alert:
                    alerts.append(cost_alert)
            
            # Process alerts
            for alert in alerts:
                self.process_alert(alert)
            
            self.metrics['total_alerts'] += len(alerts)
            
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")
            self.metrics['last_error'] = str(e)
            self.metrics['error_timestamp'] = datetime.utcnow().isoformat()
        
        return alerts
    
    def _check_system_health_threshold(self, health_metrics: SystemHealthMetrics, threshold: float) -> bool:
        """Check if system health metrics exceed threshold."""
        # Check CPU usage
        if health_metrics.cpu_usage and health_metrics.cpu_usage >= threshold:
            return True
        
        # Check memory usage
        if health_metrics.memory_usage and health_metrics.memory_usage >= threshold:
            return True
        
        # Check error rate status
        if hasattr(health_metrics, 'error_rate_status') and 'error' in health_metrics.error_rate_status.lower():
            return True
        
        return False
    
    def _create_alert_from_rule(self, rule: AlertRule, status: TokenUsageStatus, 
                              health_metrics: Optional[SystemHealthMetrics] = None) -> MonitoringAlert:
        """Create an alert from a rule."""
        alert_id = f"{rule.rule_id}_{status.user_id}_{int(time.time())}"
        
        # Create alert message
        if rule.condition == AlertCondition.USAGE_THRESHOLD:
            message = f"User {status.user_id} has reached {status.usage_percentage:.1f}% token usage"
        elif rule.condition == AlertCondition.QUOTA_EXCEEDED:
            message = f"User {status.user_id} has exceeded their token quota"
        elif rule.condition == AlertCondition.SYSTEM_HEALTH:
            message = f"System health metrics exceeded threshold: {rule.threshold}%"
        else:
            message = f"Alert triggered for rule: {rule.name}"
        
        return MonitoringAlert(
            alert_id=alert_id,
            user_id=status.user_id,
            alert_type=rule.condition.value,
            severity=rule.severity,
            message=message,
            timestamp=datetime.utcnow(),
            metrics={
                'usage_percentage': status.usage_percentage,
                'current_usage': status.current_usage,
                'max_quota': status.max_quota,
                'remaining_tokens': status.remaining_tokens
            }
        )
    
    def _check_cost_alerts(self, status: TokenUsageStatus) -> Optional[MonitoringAlert]:
        """Check for cost-based alerts."""
        # This is a simplified implementation
        # In a real system, you would calculate actual costs based on token usage
        estimated_cost = status.current_usage * 0.000002  # $0.002 per 1K tokens
        
        if estimated_cost >= self.config.cost_alert_threshold:
            alert_id = f"cost_alert_{status.user_id}_{int(time.time())}"
            
            return MonitoringAlert(
                alert_id=alert_id,
                user_id=status.user_id,
                alert_type="cost_threshold",
                severity=AlertSeverity.HIGH,
                message=f"User {status.user_id} has reached ${estimated_cost:.2f} in token costs",
                timestamp=datetime.utcnow(),
                metrics={
                    'estimated_cost': estimated_cost,
                    'usage_percentage': status.usage_percentage,
                    'current_usage': status.current_usage
                }
            )
        
        return None
    
    def process_alert(self, alert: MonitoringAlert):
        """Process an alert and send notifications."""
        try:
            # Check if alert should be suppressed
            if self._should_suppress_alert(alert):
                self.metrics['suppressions_applied'] += 1
                logger.info(f"Alert suppressed: {alert.alert_id}")
                return
            
            # Check cooldown period
            if self._is_in_cooldown(alert):
                logger.info(f"Alert in cooldown: {alert.alert_id}")
                return
            
            # Store alert
            self._alerts[alert.alert_id] = alert
            
            # Send notifications
            self._send_alert_notifications(alert)
            
            # Check for escalation
            if self.config.enable_escalation:
                self._check_escalation(alert)
            
        except Exception as e:
            logger.error(f"Error processing alert {alert.alert_id}: {e}")
            self.metrics['last_error'] = str(e)
            self.metrics['error_timestamp'] = datetime.utcnow().isoformat()
    
    def _should_suppress_alert(self, alert: MonitoringAlert) -> bool:
        """Check if alert should be suppressed."""
        if not self.config.enable_suppression:
            return False
        
        # Check if similar alert was sent recently
        suppression_key = f"{alert.user_id}_{alert.alert_type}"
        
        if suppression_key in self._alert_suppressions:
            suppression_time = self._alert_suppressions[suppression_key]
            if datetime.utcnow() - suppression_time < timedelta(seconds=self.config.suppression_window):
                return True
        
        return False
    
    def _is_in_cooldown(self, alert: MonitoringAlert) -> bool:
        """Check if alert is in cooldown period."""
        alert_key = alert.alert_id
        
        if alert_key in self._alert_cooldowns:
            cooldown_time = self._alert_cooldowns[alert_key]
            if datetime.utcnow() - cooldown_time < timedelta(minutes=self.config.escalation_timeout):
                return True
        
        return False
    
    def _send_alert_notifications(self, alert: MonitoringAlert):
        """Send notifications for an alert."""
        try:
            # Get relevant notification channels
            channels_to_use = []
            
            for rule in self._alert_rules.values():
                if rule.rule_id == alert.alert_type.split('_')[0]:  # Match rule to alert type
                    if rule.notification_channels:
                        channels_to_use.extend(rule.notification_channels)
                    break
            
            # Send notifications
            for channel_id in channels_to_use:
                if channel_id in self._notification_channels:
                    channel = self._notification_channels[channel_id]
                    if channel.enabled:
                        notification = Notification(
                            notification_id=str(uuid.uuid4()),
                            alert_id=alert.alert_id,
                            channel_type=channel.channel_type,
                            recipient=self._get_recipient_for_channel(channel, alert),
                            subject=f"Token Alert: {alert.alert_type}",
                            message=self._format_alert_message(alert, channel),
                            metadata={'channel_id': channel_id}
                        )
                        
                        # Add to notification queue
                        asyncio.run_coroutine_threadsafe(
                            self._notification_queue.put(notification),
                            asyncio.get_event_loop()
                        )
            
            # Update suppression
            suppression_key = f"{alert.user_id}_{alert.alert_type}"
            self._alert_suppressions[suppression_key] = datetime.utcnow()
            
            # Set cooldown
            self._alert_cooldowns[alert.alert_id] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error sending notifications for alert {alert.alert_id}: {e}")
            self.metrics['alerts_failed'] += 1
    
    def _get_recipient_for_channel(self, channel: NotificationChannel, alert: MonitoringAlert) -> str:
        """Get recipient for a notification channel."""
        if channel.channel_type == NotificationType.EMAIL:
            return alert.user_id  # Use user ID as email (in real system, would map to actual email)
        elif channel.channel_type == NotificationType.SLACK:
            return channel.config.get('channel', '#alerts')
        elif channel.channel_type == NotificationType.SMS:
            return channel.config.get('to_numbers', [''])[0]  # First number
        else:
            return alert.user_id
    
    def _format_alert_message(self, alert: MonitoringAlert, channel: NotificationChannel) -> str:
        """Format alert message for a specific channel."""
        base_message = f"""
Alert Details:
- Alert ID: {alert.alert_id}
- Type: {alert.alert_type}
- Severity: {alert.severity.value}
- User: {alert.user_id}
- Message: {alert.message}
- Time: {alert.timestamp}

Metrics:
"""
        
        for key, value in alert.metrics.items():
            base_message += f"- {key}: {value}\n"
        
        # Format for different channels
        if channel.channel_type == NotificationType.SLACK:
            # Slack formatting
            return f"```\n{base_message}```"
        elif channel.channel_type == NotificationType.SMS:
            # SMS formatting (shorter)
            return f"ALERT: {alert.alert_type} - {alert.message} - User: {alert.user_id}"
        else:
            # Default email formatting
            return base_message
    
    def _check_escalation(self, alert: MonitoringAlert):
        """Check if alert should be escalated."""
        try:
            alert_key = alert.alert_id
            
            # Initialize escalation state
            if alert_key not in self._escalation_states:
                self._escalation_states[alert_key] = {
                    'triggered_at': datetime.utcnow(),
                    'escalation_level': 0,
                    'last_escalation': None
                }
            
            state = self._escalation_states[alert_key]
            
            # Check if time to escalate
            if (datetime.utcnow() - state['triggered_at']).total_seconds() >= self.config.escalation_timeout:
                self._escalate_alert(alert, state)
            
        except Exception as e:
            logger.error(f"Error checking escalation for alert {alert.alert_id}: {e}")
    
    def _escalate_alert(self, alert: MonitoringAlert, state: Dict[str, Any]):
        """Escalate an alert."""
        try:
            state['escalation_level'] += 1
            state['last_escalation'] = datetime.utcnow()
            
            # Create escalation notification
            escalation_message = f"""
ESCALATION ALERT: {alert.alert_type}

This alert has been escalated to level {state['escalation_level']}

Original Alert:
- Alert ID: {alert.alert_id}
- Type: {alert.alert_type}
- Severity: {alert.severity.value}
- User: {alert.user_id}
- Message: {alert.message}
- Time: {alert.timestamp}

Time to resolution: {(datetime.utcnow() - state['triggered_at']).total_seconds():.0f} seconds
"""
            
            # Send escalation notification
            escalation_notification = Notification(
                notification_id=str(uuid.uuid4()),
                alert_id=alert.alert_id,
                channel_type=NotificationType.EMAIL,
                recipient="admin@yourdomain.com",
                subject=f"ESCALATED: {alert.alert_type}",
                message=escalation_message,
                metadata={'escalation_level': state['escalation_level']}
            )
            
            asyncio.run_coroutine_threadsafe(
                self._notification_queue.put(escalation_notification),
                asyncio.get_event_loop()
            )
            
            self.metrics['escalations_triggered'] += 1
            logger.info(f"Escalated alert {alert.alert_id} to level {state['escalation_level']}")
            
        except Exception as e:
            logger.error(f"Error escalating alert {alert.alert_id}: {e}")
    
    def _start_notification_processor(self):
        """Start the notification processor thread."""
        if self._notification_thread and self._notification_thread.is_alive():
            return
        
        self._stop_event.clear()
        self._notification_thread = threading.Thread(target=self._notification_processor, daemon=True)
        self._notification_thread.start()
        logger.info("Notification processor started")
    
    def _notification_processor(self):
        """Process notifications from the queue."""
        while not self._stop_event.is_set():
            try:
                # Get notification from queue
                notification = asyncio.run_coroutine_threadsafe(
                    self._notification_queue.get(),
                    asyncio.get_event_loop()
                ).result(timeout=1.0)
                
                # Process notification
                self._send_notification(notification)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in notification processor: {e}")
    
    def _send_notification(self, notification: Notification):
        """Send a notification via the appropriate channel."""
        try:
            channel_id = notification.metadata.get('channel_id') if notification.metadata else None
            if not channel_id or channel_id not in self._notification_channels:
                logger.error(f"Unknown channel ID: {channel_id}")
                return
            
            channel = self._notification_channels[channel_id]
            
            # Send based on channel type
            if channel.channel_type == NotificationType.EMAIL:
                self._send_email_notification(notification, channel)
            elif channel.channel_type == NotificationType.SLACK:
                self._send_slack_notification(notification, channel)
            elif channel.channel_type == NotificationType.SMS:
                self._send_sms_notification(notification, channel)
            else:
                logger.error(f"Unsupported notification type: {channel.channel_type}")
                return
            
            # Update notification status
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            self._notifications[notification.notification_id] = notification
            
            self.metrics['notifications_sent'] += 1
            logger.info(f"Notification sent: {notification.notification_id}")
            
        except Exception as e:
            logger.error(f"Error sending notification {notification.notification_id}: {e}")
            notification.status = "failed"
            notification.error_message = str(e)
            notification.retry_count += 1
            self._notifications[notification.notification_id] = notification
            
            self.metrics['notifications_failed'] += 1
            self.metrics['last_error'] = str(e)
            self.metrics['error_timestamp'] = datetime.utcnow().isoformat()
    
    def _send_email_notification(self, notification: Notification, channel: NotificationChannel):
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg['From'] = channel.config['from_address']
            msg['To'] = notification.recipient
            msg['Subject'] = notification.subject
            
            msg.attach(MIMEText(notification.message, 'plain'))
            
            # Send email
            with smtplib.SMTP(channel.config['smtp_server'], channel.config['smtp_port']) as server:
                if channel.config.get('use_tls', True):
                    server.starttls()
                
                if channel.config.get('username') and channel.config.get('password'):
                    server.login(channel.config['username'], channel.config['password'])
                
                server.send_message(msg)
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            raise
    
    def _send_slack_notification(self, notification: Notification, channel: NotificationChannel):
        """Send Slack notification."""
        try:
            payload = {
                'channel': channel.config['channel'],
                'username': channel.config.get('username', 'TokenBot'),
                'text': notification.message,
                'mrkdwn': True
            }
            
            response = requests.post(
                channel.config['webhook_url'],
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            raise
    
    def _send_sms_notification(self, notification: Notification, channel: NotificationChannel):
        """Send SMS notification."""
        try:
            # This is a simplified implementation
            # In a real system, you would use Twilio or similar SMS provider
            
            provider = channel.config.get('provider', 'twilio')
            if provider == 'twilio':
                # Twilio implementation would go here
                logger.info(f"SMS notification would be sent to {notification.recipient}")
            else:
                logger.warning(f"SMS provider {provider} not implemented")
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            raise
    
    def get_active_alerts(self, user_id: Optional[str] = None) -> List[MonitoringAlert]:
        """Get active alerts."""
        alerts = list(self._alerts.values())
        
        if user_id:
            alerts = [alert for alert in alerts if alert.user_id == user_id and not alert.resolved]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_history(self, user_id: Optional[str] = None, days: int = 7) -> List[MonitoringAlert]:
        """Get alert history."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        alerts = list(self._alerts.values())
        
        if user_id:
            alerts = [alert for alert in alerts if alert.user_id == user_id]
        
        return [alert for alert in alerts if alert.timestamp >= cutoff_date]
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge an alert."""
        if alert_id in self._alerts:
            alert = self._alerts[alert_id]
            alert.acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str, resolved_by: str = "system", notes: str = "") -> bool:
        """Resolve an alert."""
        if alert_id in self._alerts:
            alert = self._alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            logger.info(f"Alert {alert_id} resolved by {resolved_by}")
            return True
        return False
    
    def get_alerting_metrics(self) -> Dict[str, Any]:
        """Get alerting system metrics."""
        return {
            'total_alerts': len(self._alerts),
            'active_alerts': len([a for a in self._alerts.values() if not a.resolved]),
            'acknowledged_alerts': len([a for a in self._alerts.values() if a.acknowledged]),
            'resolved_alerts': len([a for a in self._alerts.values() if a.resolved]),
            'total_notifications': len(self._notifications),
            'notifications_sent': self.metrics['notifications_sent'],
            'notifications_failed': self.metrics['notifications_failed'],
            'escalations_triggered': self.metrics['escalations_triggered'],
            'suppressions_applied': self.metrics['suppressions_applied'],
            'last_error': self.metrics['last_error'],
            'error_timestamp': self.metrics['error_timestamp']
        }
    
    def cleanup_old_data(self):
        """Clean up old alerting data."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.config.alert_retention_days)
            
            # Clean up old alerts
            alerts_to_remove = [
                alert_id for alert_id, alert in self._alerts.items()
                if alert.timestamp < cutoff_date and alert.resolved
            ]
            
            for alert_id in alerts_to_remove:
                del self._alerts[alert_id]
            
            # Clean up old notifications
            notifications_to_remove = [
                notif_id for notif_id, notif in self._notifications.items()
                if notif.sent_at and notif.sent_at < cutoff_date
            ]
            
            for notif_id in notifications_to_remove:
                del self._notifications[notif_id]
            
            logger.info(f"Cleaned up {len(alerts_to_remove)} old alerts and {len(notifications_to_remove)} notifications")
            
        except Exception as e:
            logger.error(f"Error cleaning up old alerting data: {e}")
    
    def shutdown(self):
        """Shutdown the alerting system."""
        logger.info("Shutting down TokenAlertingSystem")
        
        # Stop notification processor
        self._stop_event.set()
        
        if self._notification_thread and self._notification_thread.is_alive():
            self._notification_thread.join(timeout=5.0)
        
        # Clean up old data
        self.cleanup_old_data()
        
        logger.info("TokenAlertingSystem shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Convenience functions
def get_alerting_system(db: Optional[PostgresDB] = None) -> TokenAlertingSystem:
    """Get a global alerting system instance."""
    return TokenAlertingSystem(db)


def configure_alerting_from_file(config_path: str) -> AlertingConfig:
    """Configure alerting system from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return AlertingConfig(**config_data)
    except Exception as e:
        logger.error(f"Error loading alerting config from {config_path}: {e}")
        return AlertingConfig()