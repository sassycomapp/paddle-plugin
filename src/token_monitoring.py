"""
Token Monitoring and Reporting System

This module provides comprehensive monitoring and reporting capabilities for the token management system.
It includes real-time status monitoring, anomaly detection, usage analytics, and system health monitoring.
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time
from contextlib import contextmanager
import statistics

from simba.simba.database.postgres import PostgresDB
from src.token_usage_logger import TokenUsageLogger, LoggingConfig
from src.token_management.rate_limiter import RateLimiter, RateLimitConfig
from src.token_management.token_counter import TokenCounter

logger = logging.getLogger(__name__)


class MonitoringStatus(Enum):
    """Monitoring system status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TokenUsageStatus:
    """Current token usage status for a user."""
    user_id: str
    current_usage: int
    max_quota: int
    remaining_tokens: int
    usage_percentage: float
    period_start: datetime
    period_end: datetime
    status: MonitoringStatus
    last_updated: datetime
    api_endpoint: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class SystemHealthMetrics:
    """System health metrics."""
    timestamp: datetime
    total_requests_24h: int
    requests_last_hour: int
    avg_tokens_per_request: float
    max_tokens_single_request: int
    active_users_24h: int
    active_endpoints: int
    system_load: str
    quota_status: str
    error_rate_status: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    database_connections: Optional[int] = None


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection."""
    user_id: str
    anomaly_type: str
    severity: AlertSeverity
    description: str
    detected_at: datetime
    metrics: Dict[str, Any]
    confidence_score: float
    suggested_action: str


@dataclass
class MonitoringAlert:
    """Monitoring alert."""
    alert_id: str
    user_id: str
    alert_type: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    metrics: Dict[str, Any]
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    escalation_count: int = 0


@dataclass
class MonitoringConfig:
    """Configuration for the monitoring system."""
    enable_real_time_monitoring: bool = True
    monitoring_interval: int = 60  # seconds
    anomaly_detection_enabled: bool = True
    alerting_enabled: bool = True
    alert_threshold_high_usage: float = 0.8  # 80%
    alert_threshold_critical_usage: float = 0.95  # 95%
    anomaly_detection_window: int = 24  # hours
    anomaly_threshold_multiplier: float = 3.0
    max_alerts_per_user: int = 10
    enable_system_health_monitoring: bool = True
    enable_cost_analysis: bool = True
    data_retention_days: int = 90
    performance_monitoring: bool = True


class TokenMonitoringSystem:
    """
    Comprehensive token monitoring and reporting system.
    
    Provides real-time monitoring, anomaly detection, alerting, and reporting
    capabilities for the token management system.
    """
    
    def __init__(self, db: Optional[PostgresDB] = None, config: Optional[MonitoringConfig] = None):
        """
        Initialize the token monitoring system.
        
        Args:
            db: Database instance for monitoring queries
            config: Monitoring configuration
        """
        self.db = db or PostgresDB()
        self.config = config or MonitoringConfig()
        
        # Core components
        self.token_counter = TokenCounter(self.db)
        self.rate_limiter = RateLimiter(self.db)
        self.usage_logger = TokenUsageLogger(self.db, LoggingConfig())
        
        # Monitoring state
        self._monitoring_active = False
        self._monitoring_thread = None
        self._stop_event = threading.Event()
        self._alerts: Dict[str, MonitoringAlert] = {}
        self._metrics_history: List[SystemHealthMetrics] = []
        
        # Performance metrics
        self.performance_metrics = {
            'total_checks': 0,
            'anomalies_detected': 0,
            'alerts_generated': 0,
            'system_health_checks': 0,
            'average_check_time': 0.0,
            'last_error': None,
            'error_timestamp': None
        }
        
        # Alert handlers
        self._alert_handlers: List[Callable] = []
        
        logger.info("TokenMonitoringSystem initialized")
    
    def start_monitoring(self):
        """Start the monitoring system."""
        if self._monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self._monitoring_active = True
        self._stop_event.clear()
        
        # Start monitoring thread
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        
        logger.info("Token monitoring system started")
    
    def stop_monitoring(self):
        """Stop the monitoring system."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        self._stop_event.set()
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5.0)
        
        logger.info("Token monitoring system stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                start_time = time.time()
                
                # Perform monitoring tasks
                if self.config.enable_real_time_monitoring:
                    self._check_token_usage_status()
                
                if self.config.anomaly_detection_enabled:
                    anomalies = self.detect_anomalies()
                    for anomaly in anomalies:
                        self._handle_anomaly(anomaly)
                
                if self.config.enable_system_health_monitoring:
                    health_metrics = self.get_system_health()
                    self._update_metrics_history(health_metrics)
                
                # Update performance metrics
                check_time = time.time() - start_time
                self._update_performance_metric('average_check_time', check_time)
                self.performance_metrics['total_checks'] += 1
                
                # Sleep until next check
                time.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.performance_metrics['last_error'] = str(e)
                self.performance_metrics['error_timestamp'] = datetime.utcnow().isoformat()
                time.sleep(self.config.monitoring_interval)
    
    def get_token_usage_status(self, user_id: str, api_endpoint: Optional[str] = None) -> TokenUsageStatus:
        """
        Get current token usage status for a user.
        
        Args:
            user_id: User identifier
            api_endpoint: Specific API endpoint to check (optional)
            
        Returns:
            TokenUsageStatus with current usage information
        """
        try:
            # Get user's token limit
            token_limit = self.db.get_user_token_limit(user_id)
            if not token_limit:
                return TokenUsageStatus(
                    user_id=user_id,
                    current_usage=0,
                    max_quota=0,
                    remaining_tokens=0,
                    usage_percentage=0.0,
                    period_start=datetime.utcnow(),
                    period_end=datetime.utcnow() + timedelta(days=1),
                    status=MonitoringStatus.UNKNOWN,
                    last_updated=datetime.utcnow()
                )
            
            # Get current usage
            current_usage = token_limit['tokens_used_in_period']
            max_quota = token_limit['max_tokens_per_period']
            remaining_tokens = max_quota - current_usage
            usage_percentage = (current_usage / max_quota) * 100 if max_quota > 0 else 0.0
            
            # Determine status
            if usage_percentage >= 100:
                status = MonitoringStatus.CRITICAL
            elif usage_percentage >= self.config.alert_threshold_critical_usage:
                status = MonitoringStatus.CRITICAL
            elif usage_percentage >= self.config.alert_threshold_high_usage:
                status = MonitoringStatus.WARNING
            else:
                status = MonitoringStatus.HEALTHY
            
            # Calculate period times
            period_start = token_limit['period_start']
            period_days = float(token_limit['period_interval'].split()[0])
            period_end = period_start + timedelta(days=period_days)
            
            return TokenUsageStatus(
                user_id=user_id,
                current_usage=current_usage,
                max_quota=max_quota,
                remaining_tokens=remaining_tokens,
                usage_percentage=usage_percentage,
                period_start=period_start,
                period_end=period_end,
                status=status,
                last_updated=datetime.utcnow(),
                api_endpoint=api_endpoint
            )
            
        except Exception as e:
            logger.error(f"Error getting token usage status for user {user_id}: {e}")
            return TokenUsageStatus(
                user_id=user_id,
                current_usage=0,
                max_quota=0,
                remaining_tokens=0,
                usage_percentage=0.0,
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow() + timedelta(days=1),
                status=MonitoringStatus.ERROR,
                last_updated=datetime.utcnow()
            )
    
    def _check_token_usage_status(self):
        """Check token usage status for all users."""
        try:
            # Get all users with limits
            users_with_limits = self.db.get_token_usage_summary()
            
            for user_id in users_with_limits:
                status = self.get_token_usage_status(user_id)
                
                # Check if we need to generate alerts
                if status.status in [MonitoringStatus.WARNING, MonitoringStatus.CRITICAL]:
                    alert = MonitoringAlert(
                        alert_id=f"usage_{user_id}_{int(time.time())}",
                        user_id=user_id,
                        alert_type="high_usage",
                        severity=AlertSeverity.HIGH if status.status == MonitoringStatus.CRITICAL else AlertSeverity.MEDIUM,
                        message=f"User {user_id} has {status.usage_percentage:.1f}% token usage",
                        timestamp=datetime.utcnow(),
                        metrics={
                            'current_usage': status.current_usage,
                            'max_quota': status.max_quota,
                            'usage_percentage': status.usage_percentage,
                            'remaining_tokens': status.remaining_tokens
                        }
                    )
                    self._add_alert(alert)
                
                # Check for quota violations
                if status.usage_percentage >= 100:
                    alert = MonitoringAlert(
                        alert_id=f"violation_{user_id}_{int(time.time())}",
                        user_id=user_id,
                        alert_type="quota_violation",
                        severity=AlertSeverity.CRITICAL,
                        message=f"User {user_id} has exceeded token quota",
                        timestamp=datetime.utcnow(),
                        metrics={
                            'current_usage': status.current_usage,
                            'max_quota': status.max_quota,
                            'usage_percentage': status.usage_percentage,
                            'remaining_tokens': status.remaining_tokens
                        }
                    )
                    self._add_alert(alert)
        
        except Exception as e:
            logger.error(f"Error checking token usage status: {e}")
    
    def detect_anomalies(self) -> List[AnomalyDetectionResult]:
        """
        Detect anomalous token consumption patterns.
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        try:
            # Get usage data for anomaly detection window
            start_date = datetime.utcnow() - timedelta(hours=self.config.anomaly_detection_window)
            usage_data = self.db.get_token_usage_history(start_date=start_date)
            
            if not usage_data:
                return anomalies
            
            # Group by user for individual analysis
            user_usage = {}
            for record in usage_data:
                user_id = record['user_id']
                if user_id not in user_usage:
                    user_usage[user_id] = []
                user_usage[user_id].append(record['tokens_used'])
            
            # Analyze each user's usage patterns
            for user_id, usage_values in user_usage.items():
                if len(usage_values) < 5:  # Need sufficient data points
                    continue
                
                # Calculate statistics
                mean_usage = statistics.mean(usage_values)
                median_usage = statistics.median(usage_values)
                std_usage = statistics.stdev(usage_values) if len(usage_values) > 1 else 0
                
                # Detect anomalies using statistical methods
                for i, usage in enumerate(usage_values):
                    # Z-score method
                    if std_usage > 0:
                        z_score = abs(usage - mean_usage) / std_usage
                        if z_score > self.config.anomaly_threshold_multiplier:
                            anomaly = AnomalyDetectionResult(
                                user_id=user_id,
                                anomaly_type="statistical_outlier",
                                severity=AlertSeverity.HIGH if z_score > 5 else AlertSeverity.MEDIUM,
                                description=f"Unusual token consumption detected: {usage} tokens (Z-score: {z_score:.2f})",
                                detected_at=datetime.utcnow(),
                                metrics={
                                    'usage_value': usage,
                                    'mean_usage': mean_usage,
                                    'median_usage': median_usage,
                                    'std_usage': std_usage,
                                    'z_score': z_score,
                                    'request_index': i
                                },
                                confidence_score=min(1.0, z_score / 5.0),
                                suggested_action="Review user's usage pattern and consider adjusting limits"
                            )
                            anomalies.append(anomaly)
                
                # Detect trend anomalies
                if len(usage_values) >= 10:
                    # Simple trend detection
                    recent_usage = usage_values[-5:]  # Last 5 requests
                    earlier_usage = usage_values[-10:-5] if len(usage_values) >= 10 else usage_values[:-5]
                    
                    if recent_usage and earlier_usage:
                        recent_avg = statistics.mean(recent_usage)
                        earlier_avg = statistics.mean(earlier_usage)
                        
                        # Significant increase detection
                        if recent_avg > earlier_avg * 2:  # 2x increase
                            anomaly = AnomalyDetectionResult(
                                user_id=user_id,
                                anomaly_type="usage_spike",
                                severity=AlertSeverity.MEDIUM,
                                description=f"Significant usage spike detected: {recent_avg:.1f} vs {earlier_avg:.1f} tokens",
                                detected_at=datetime.utcnow(),
                                metrics={
                                    'recent_avg': recent_avg,
                                    'earlier_avg': earlier_avg,
                                    'increase_factor': recent_avg / earlier_avg,
                                    'recent_values': recent_usage,
                                    'earlier_values': earlier_usage
                                },
                                confidence_score=min(1.0, (recent_avg / earlier_avg - 1) / 2),
                                suggested_action="Investigate the cause of usage spike and consider temporary limits"
                            )
                            anomalies.append(anomaly)
            
            self.performance_metrics['anomalies_detected'] += len(anomalies)
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
        
        return anomalies
    
    def _handle_anomaly(self, anomaly: AnomalyDetectionResult):
        """Handle a detected anomaly."""
        try:
            # Create alert for the anomaly
            alert = MonitoringAlert(
                alert_id=f"anomaly_{anomaly.user_id}_{int(time.time())}",
                user_id=anomaly.user_id,
                alert_type="anomaly_detection",
                severity=anomaly.severity,
                message=anomaly.description,
                timestamp=datetime.utcnow(),
                metrics=anomaly.metrics
            )
            
            self._add_alert(alert)
            self.performance_metrics['alerts_generated'] += 1
            
            logger.info(f"Detected anomaly for user {anomaly.user_id}: {anomaly.description}")
            
        except Exception as e:
            logger.error(f"Error handling anomaly: {e}")
    
    def get_system_health(self) -> SystemHealthMetrics:
        """
        Get current system health metrics.
        
        Returns:
            SystemHealthMetrics with current system status
        """
        try:
            self.performance_metrics['system_health_checks'] += 1
            
            # Get basic metrics from database
            start_date = datetime.utcnow() - timedelta(hours=24)
            usage_data = self.db.get_token_usage_history(start_date=start_date)
            
            if not usage_data:
                return SystemHealthMetrics(
                    timestamp=datetime.utcnow(),
                    total_requests_24h=0,
                    requests_last_hour=0,
                    avg_tokens_per_request=0.0,
                    max_tokens_single_request=0,
                    active_users_24h=0,
                    active_endpoints=0,
                    system_load="low",
                    quota_status="normal",
                    error_rate_status="normal"
                )
            
            # Calculate metrics
            total_requests = len(usage_data)
            total_tokens = sum(record['tokens_used'] for record in usage_data)
            avg_tokens_per_request = total_tokens / total_requests if total_requests > 0 else 0.0
            max_tokens_single_request = max(record['tokens_used'] for record in usage_data)
            
            # Get recent requests (last hour)
            recent_start = datetime.utcnow() - timedelta(hours=1)
            recent_requests = [
                record for record in usage_data 
                if record['timestamp'] >= recent_start
            ]
            requests_last_hour = len(recent_requests)
            
            # Get unique users and endpoints
            unique_users = set(record['user_id'] for record in usage_data)
            unique_endpoints = set(record['api_endpoint'] for record in usage_data)
            
            # Determine system load
            if requests_last_hour > 1000:
                system_load = "high"
            elif requests_last_hour > 500:
                system_load = "medium"
            else:
                system_load = "low"
            
            # Check quota status
            high_usage_users = 0
            critical_usage_users = 0
            for user_id in unique_users:
                status = self.get_token_usage_status(user_id)
                if status.usage_percentage > 95:
                    critical_usage_users += 1
                elif status.usage_percentage > 80:
                    high_usage_users += 1
            
            if critical_usage_users > 5:
                quota_status = "critical"
            elif critical_usage_users > 2:
                quota_status = "high"
            elif high_usage_users > 10:
                quota_status = "medium"
            else:
                quota_status = "normal"
            
            # Determine error rate status (simplified)
            high_priority_requests = sum(1 for record in usage_data if record['priority_level'] == 'High')
            error_rate = high_priority_requests / total_requests if total_requests > 0 else 0.0
            
            if error_rate > 0.1:
                error_rate_status = "high"
            elif error_rate > 0.05:
                error_rate_status = "medium"
            else:
                error_rate_status = "normal"
            
            # Get system metrics (simplified implementation)
            cpu_usage = self._get_cpu_usage()
            memory_usage = self._get_memory_usage()
            database_connections = self._get_database_connections()
            
            return SystemHealthMetrics(
                timestamp=datetime.utcnow(),
                total_requests_24h=total_requests,
                requests_last_hour=requests_last_hour,
                avg_tokens_per_request=avg_tokens_per_request,
                max_tokens_single_request=max_tokens_single_request,
                active_users_24h=len(unique_users),
                active_endpoints=len(unique_endpoints),
                system_load=system_load,
                quota_status=quota_status,
                error_rate_status=error_rate_status,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                database_connections=database_connections
            )
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return SystemHealthMetrics(
                timestamp=datetime.utcnow(),
                total_requests_24h=0,
                requests_last_hour=0,
                avg_tokens_per_request=0.0,
                max_tokens_single_request=0,
                active_users_24h=0,
                active_endpoints=0,
                system_load="error",
                quota_status="error",
                error_rate_status="error"
            )
    
    def _update_metrics_history(self, metrics: SystemHealthMetrics):
        """Update metrics history for trend analysis."""
        self._metrics_history.append(metrics)
        
        # Keep only recent data (last 24 hours of metrics, collected every minute)
        max_history = 24 * 60  # 24 hours * 60 minutes
        if len(self._metrics_history) > max_history:
            self._metrics_history = self._metrics_history[-max_history:]
    
    def _add_alert(self, alert: MonitoringAlert):
        """Add an alert to the system."""
        # Check if user has too many alerts
        user_alerts = [a for a in self._alerts.values() if a.user_id == alert.user_id and not a.resolved]
        if len(user_alerts) >= self.config.max_alerts_per_user:
            # Resolve oldest alert
            oldest_alert = min(user_alerts, key=lambda a: a.timestamp)
            oldest_alert.resolved = True
            oldest_alert.resolved_at = datetime.utcnow()
        
        self._alerts[alert.alert_id] = alert
        
        # Notify alert handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        logger.info(f"Alert generated: {alert.alert_type} for user {alert.user_id}")
    
    def get_alerts(self, user_id: Optional[str] = None, 
                  severity: Optional[AlertSeverity] = None,
                  resolved: Optional[bool] = None) -> List[MonitoringAlert]:
        """
        Get alerts with optional filtering.
        
        Args:
            user_id: Filter by user ID (optional)
            severity: Filter by severity level (optional)
            resolved: Filter by resolved status (optional)
            
        Returns:
            List of matching alerts
        """
        alerts = list(self._alerts.values())
        
        if user_id:
            alerts = [a for a in alerts if a.user_id == user_id]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        
        return alerts
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self._alerts:
            self._alerts[alert_id].acknowledged = True
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id in self._alerts:
            self._alerts[alert_id].resolved = True
            self._alerts[alert_id].resolved_at = datetime.utcnow()
            return True
        return False
    
    def add_alert_handler(self, handler: Callable):
        """Add an alert handler function."""
        self._alert_handlers.append(handler)
    
    def generate_usage_report(self, user_id: Optional[str] = None,
                             days: int = 7,
                             format: str = "json") -> Dict[str, Any]:
        """
        Generate comprehensive usage report.
        
        Args:
            user_id: Specific user to report on (optional)
            days: Number of days to include in report
            format: Report format ('json', 'summary')
            
        Returns:
            Dictionary with usage report data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get usage data
            usage_data = self.db.get_token_usage_history(user_id=user_id, start_date=start_date)
            
            if not usage_data:
                return {
                    'report_generated_at': datetime.utcnow().isoformat(),
                    'period_days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': datetime.utcnow().isoformat(),
                    'total_tokens': 0,
                    'total_requests': 0,
                    'unique_users': 0 if not user_id else 1,
                    'unique_endpoints': 0,
                    'average_tokens_per_request': 0,
                    'peak_usage': 0,
                    'user_breakdown': {} if user_id else {},
                    'endpoint_breakdown': {},
                    'trend_analysis': {},
                    'cost_analysis': {},
                    'format': format
                }
            
            # Calculate basic metrics
            total_tokens = sum(record['tokens_used'] for record in usage_data)
            total_requests = len(usage_data)
            unique_users = set(record['user_id'] for record in usage_data) if not user_id else {user_id}
            unique_endpoints = set(record['api_endpoint'] for record in usage_data)
            average_tokens_per_request = total_tokens / total_requests if total_requests > 0 else 0
            peak_usage = max(record['tokens_used'] for record in usage_data)
            
            # User breakdown
            user_breakdown = {}
            if not user_id:
                for user in unique_users:
                    user_data = [r for r in usage_data if r['user_id'] == user]
                    user_tokens = sum(r['tokens_used'] for r in user_data)
                    user_breakdown[user] = {
                        'total_tokens': user_tokens,
                        'total_requests': len(user_data),
                        'average_tokens_per_request': user_tokens / len(user_data) if user_data else 0,
                        'percentage_of_total': (user_tokens / total_tokens) * 100 if total_tokens > 0 else 0
                    }
            else:
                user_data = [r for r in usage_data if r['user_id'] == user_id]
                user_breakdown[user_id] = {
                    'total_tokens': total_tokens,
                    'total_requests': total_requests,
                    'average_tokens_per_request': average_tokens_per_request,
                    'percentage_of_total': 100.0
                }
            
            # Endpoint breakdown
            endpoint_breakdown = {}
            for endpoint in unique_endpoints:
                endpoint_data = [r for r in usage_data if r['api_endpoint'] == endpoint]
                endpoint_tokens = sum(r['tokens_used'] for r in endpoint_data)
                endpoint_breakdown[endpoint] = {
                    'total_tokens': endpoint_tokens,
                    'total_requests': len(endpoint_data),
                    'average_tokens_per_request': endpoint_tokens / len(endpoint_data) if endpoint_data else 0,
                    'percentage_of_total': (endpoint_tokens / total_tokens) * 100 if total_tokens > 0 else 0
                }
            
            # Trend analysis
            trend_analysis = self._analyze_usage_trends(usage_data)
            
            # Cost analysis (simplified)
            cost_analysis = self._analyze_costs(usage_data)
            
            # Format output
            if format == "summary":
                return {
                    'report_generated_at': datetime.utcnow().isoformat(),
                    'period_days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': datetime.utcnow().isoformat(),
                    'total_tokens': total_tokens,
                    'total_requests': total_requests,
                    'unique_users': len(unique_users),
                    'unique_endpoints': len(unique_endpoints),
                    'average_tokens_per_request': average_tokens_per_request,
                    'peak_usage': peak_usage,
                    'top_users': sorted(user_breakdown.items(), key=lambda x: x[1]['total_tokens'], reverse=True)[:5],
                    'top_endpoints': sorted(endpoint_breakdown.items(), key=lambda x: x[1]['total_tokens'], reverse=True)[:5],
                    'trend_summary': trend_analysis.get('summary', {}),
                    'cost_summary': cost_analysis.get('summary', {}),
                    'format': format
                }
            else:
                return {
                    'report_generated_at': datetime.utcnow().isoformat(),
                    'period_days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': datetime.utcnow().isoformat(),
                    'total_tokens': total_tokens,
                    'total_requests': total_requests,
                    'unique_users': len(unique_users),
                    'unique_endpoints': len(unique_endpoints),
                    'average_tokens_per_request': average_tokens_per_request,
                    'peak_usage': peak_usage,
                    'user_breakdown': user_breakdown,
                    'endpoint_breakdown': endpoint_breakdown,
                    'trend_analysis': trend_analysis,
                    'cost_analysis': cost_analysis,
                    'format': format
                }
        
        except Exception as e:
            logger.error(f"Error generating usage report: {e}")
            return {
                'error': str(e),
                'report_generated_at': datetime.utcnow().isoformat()
            }
    
    def _analyze_usage_trends(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze usage trends in the data."""
        try:
            if not usage_data:
                return {}
            
            # Group by day
            daily_usage = {}
            for record in usage_data:
                day = record['timestamp'].strftime('%Y-%m-%d')
                if day not in daily_usage:
                    daily_usage[day] = {'tokens': 0, 'requests': 0}
                daily_usage[day]['tokens'] += record['tokens_used']
                daily_usage[day]['requests'] += 1
            
            # Calculate trends
            days = sorted(daily_usage.keys())
            if len(days) < 2:
                return {'summary': {'trend': 'insufficient_data'}}
            
            # Calculate daily growth
            daily_tokens = [daily_usage[day]['tokens'] for day in days]
            growth_rates = []
            for i in range(1, len(daily_tokens)):
                if daily_tokens[i-1] > 0:
                    growth_rate = (daily_tokens[i] - daily_tokens[i-1]) / daily_tokens[i-1]
                    growth_rates.append(growth_rate)
            
            avg_growth = statistics.mean(growth_rates) if growth_rates else 0
            trend_direction = "increasing" if avg_growth > 0.1 else "decreasing" if avg_growth < -0.1 else "stable"
            
            # Peak usage day
            peak_day = max(daily_usage.keys(), key=lambda day: daily_usage[day]['tokens'])
            
            return {
                'summary': {
                    'trend': trend_direction,
                    'average_daily_growth': avg_growth,
                    'peak_day': peak_day,
                    'peak_tokens': daily_usage[peak_day]['tokens']
                },
                'daily_breakdown': daily_usage,
                'growth_rates': growth_rates
            }
        
        except Exception as e:
            logger.error(f"Error analyzing usage trends: {e}")
            return {'error': str(e)}
    
    def _analyze_costs(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze costs associated with token usage."""
        try:
            # Simplified cost calculation (adjust based on your pricing model)
            # Assuming $0.002 per 1K tokens for input, $0.008 per 1K tokens for output
            input_cost_per_1k = 0.002
            output_cost_per_1k = 0.008
            
            total_tokens = sum(record['tokens_used'] for record in usage_data)
            
            # Estimate input/output split (simplified: assume 70% input, 30% output)
            input_tokens = total_tokens * 0.7
            output_tokens = total_tokens * 0.3
            
            input_cost = (input_tokens / 1000) * input_cost_per_1k
            output_cost = (output_tokens / 1000) * output_cost_per_1k
            total_cost = input_cost + output_cost
            
            # Daily cost breakdown
            daily_costs = {}
            for record in usage_data:
                day = record['timestamp'].strftime('%Y-%m-%d')
                if day not in daily_costs:
                    daily_costs[day] = 0
                daily_costs[day] += ((record['tokens_used'] / 1000) * input_cost_per_1k * 0.7 + 
                                   (record['tokens_used'] / 1000) * output_cost_per_1k * 0.3)
            
            return {
                'summary': {
                    'total_tokens': total_tokens,
                    'estimated_input_tokens': input_tokens,
                    'estimated_output_tokens': output_tokens,
                    'input_cost': input_cost,
                    'output_cost': output_cost,
                    'total_cost': total_cost,
                    'cost_per_token': total_cost / total_tokens if total_tokens > 0 else 0
                },
                'daily_breakdown': daily_costs,
                'pricing_model': {
                    'input_cost_per_1k': input_cost_per_1k,
                    'output_cost_per_1k': output_cost_per_1k,
                    'input_output_ratio': '70/30'
                }
            }
        
        except Exception as e:
            logger.error(f"Error analyzing costs: {e}")
            return {'error': str(e)}
    
    def export_metrics(self, format: str = "json", 
                      include_system_metrics: bool = True,
                      include_alerts: bool = True) -> Union[str, bytes]:
        """
        Export metrics for external monitoring systems.
        
        Args:
            format: Export format ('json', 'csv')
            include_system_metrics: Include system health metrics
            include_alerts: Include alert data
            
        Returns:
            Exported data as string or bytes
        """
        try:
            export_data = {
                'export_timestamp': datetime.utcnow().isoformat(),
                'format': format,
                'monitoring_config': asdict(self.config),
                'performance_metrics': self.performance_metrics.copy()
            }
            
            # Add system metrics
            if include_system_metrics:
                current_health = self.get_system_health()
                export_data['system_health'] = asdict(current_health)
                export_data['metrics_history'] = [asdict(m) for m in self._metrics_history[-60:]]  # Last hour
            
            # Add alerts
            if include_alerts:
                export_data['alerts'] = [asdict(alert) for alert in self._alerts.values()]
            
            if format.lower() == "json":
                return json.dumps(export_data, indent=2, ensure_ascii=False)
            
            elif format.lower() == "csv":
                import csv
                import io
                
                # Convert to CSV format (simplified)
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(['Metric', 'Value', 'Timestamp'])
                
                # Write performance metrics
                for key, value in self.performance_metrics.items():
                    writer.writerow([f'performance.{key}', value, datetime.utcnow().isoformat()])
                
                # Write system health
                if include_system_metrics:
                    health = self.get_system_health()
                    for key, value in asdict(health).items():
                        if key != 'timestamp':
                            writer.writerow([f'system_health.{key}', value, health.timestamp.isoformat()])
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            raise
    
    def _get_cpu_usage(self) -> Optional[float]:
        """Get current CPU usage (simplified implementation)."""
        try:
            # This is a simplified implementation
            # In a real system, you would use psutil or similar
            import random
            return random.uniform(10, 90)  # Mock CPU usage
        except:
            return None
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage (simplified implementation)."""
        try:
            # This is a simplified implementation
            # In a real system, you would use psutil or similar
            import random
            return random.uniform(30, 80)  # Mock memory usage
        except:
            return None
    
    def _get_database_connections(self) -> Optional[int]:
        """Get current database connection count (simplified implementation)."""
        try:
            # This is a simplified implementation
            # In a real system, you would query the database directly
            import random
            return random.randint(10, 50)  # Mock connection count
        except:
            return None
    
    def _update_performance_metric(self, metric_name: str, value: float):
        """Update performance metric with exponential moving average."""
        if metric_name in self.performance_metrics:
            current_avg = self.performance_metrics[metric_name]
            alpha = 0.1  # Smoothing factor
            self.performance_metrics[metric_name] = alpha * value + (1 - alpha) * current_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the monitoring system."""
        return self.performance_metrics.copy()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the monitoring system."""
        try:
            # Check database connection
            db_health = self.db.health_check()
            
            # Check monitoring status
            monitoring_active = self._monitoring_active
            monitoring_thread_alive = self._monitoring_thread and self._monitoring_thread.is_alive()
            
            # Check alert system
            alert_count = len(self._alerts)
            unresolved_alerts = len([a for a in self._alerts.values() if not a.resolved])
            
            # Get current system health
            system_health = self.get_system_health()
            
            overall_health = (
                db_health and
                monitoring_active and
                monitoring_thread_alive
            )
            
            return {
                'healthy': overall_health,
                'database_healthy': db_health,
                'monitoring_active': monitoring_active,
                'monitoring_thread_alive': monitoring_thread_alive,
                'alert_count': alert_count,
                'unresolved_alerts': unresolved_alerts,
                'system_load': system_health.system_load,
                'quota_status': system_health.quota_status,
                'last_error': self.performance_metrics['last_error'],
                'error_timestamp': self.performance_metrics['error_timestamp'],
                'config': {
                    'enable_real_time_monitoring': self.config.enable_real_time_monitoring,
                    'monitoring_interval': self.config.monitoring_interval,
                    'anomaly_detection_enabled': self.config.anomaly_detection_enabled,
                    'alerting_enabled': self.config.alerting_enabled
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'database_healthy': False,
                'monitoring_active': False,
                'monitoring_thread_alive': False,
                'alert_count': 0,
                'unresolved_alerts': 0
            }
    
    def cleanup_old_data(self):
        """Clean up old monitoring data based on retention policies."""
        try:
            # Clean up old alerts
            cutoff_date = datetime.utcnow() - timedelta(days=self.config.data_retention_days)
            alerts_to_remove = [
                alert_id for alert_id, alert in self._alerts.items()
                if alert.timestamp < cutoff_date and alert.resolved
            ]
            
            for alert_id in alerts_to_remove:
                del self._alerts[alert_id]
            
            # Clean up metrics history
            self._metrics_history = [
                m for m in self._metrics_history
                if m.timestamp >= cutoff_date
            ]
            
            logger.info(f"Cleaned up {len(alerts_to_remove)} old alerts and metrics")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def shutdown(self):
        """Shutdown the monitoring system gracefully."""
        logger.info("Shutting down TokenMonitoringSystem")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Clean up old data
        self.cleanup_old_data()
        
        logger.info("TokenMonitoringSystem shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Convenience functions for direct usage
def get_token_usage_status(user_id: str, db: Optional[PostgresDB] = None) -> TokenUsageStatus:
    """
    Convenience function to get token usage status.
    
    Args:
        user_id: User identifier
        db: Database instance (optional)
        
    Returns:
        TokenUsageStatus with current usage information
    """
    monitoring_system = TokenMonitoringSystem(db)
    return monitoring_system.get_token_usage_status(user_id)


def detect_anomalies(db: Optional[PostgresDB] = None) -> List[AnomalyDetectionResult]:
    """
    Convenience function to detect anomalies.
    
    Args:
        db: Database instance (optional)
        
    Returns:
        List of detected anomalies
    """
    monitoring_system = TokenMonitoringSystem(db)
    return monitoring_system.detect_anomalies()


def generate_usage_report(user_id: Optional[str] = None, days: int = 7,
                         db: Optional[PostgresDB] = None) -> Dict[str, Any]:
    """
    Convenience function to generate usage report.
    
    Args:
        user_id: Specific user to report on (optional)
        days: Number of days to include in report
        db: Database instance (optional)
        
    Returns:
        Dictionary with usage report data
    """
    monitoring_system = TokenMonitoringSystem(db)
    return monitoring_system.generate_usage_report(user_id, days)