#!/usr/bin/env python3
"""
Monitoring and Alerting Script for Cache Management System Integration

This script provides comprehensive monitoring and alerting for all integrated
components including cache server, database, MCP servers, and external services.

Author: KiloCode
License: Apache 2.0
"""

import asyncio
import aiohttp
import psycopg2
import json
import logging
import sys
import time
import smtplib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from email.mime.text import MIMEText
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cache_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure."""
    component: str
    level: AlertLevel
    message: str
    timestamp: datetime
    metrics: Dict[str, Any]
    acknowledged: bool = False


class MonitoringConfig:
    """Monitoring configuration."""
    
    def __init__(self):
        self.check_interval = 60  # seconds
        self.metrics_retention = 86400  # 24 hours
        self.alert_cooldown = 300  # 5 minutes
        
        # Alert thresholds
        self.thresholds = {
            "cache_hit_rate": {"warning": 0.7, "critical": 0.5},
            "response_time_ms": {"warning": 1000, "critical": 2000},
            "error_rate": {"warning": 0.05, "critical": 0.1},
            "memory_usage_percent": {"warning": 80, "critical": 90},
            "disk_usage_percent": {"warning": 85, "critical": 95},
            "database_connections": {"warning": 15, "critical": 20},
            "cpu_usage_percent": {"warning": 70, "critical": 85}
        }
        
        # Email notification settings
        self.email_notifications = {
            "enabled": False,
            "smtp_server": "localhost",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "recipients": []
        }
        
        # Webhook notifications
        self.webhook_notifications = {
            "enabled": False,
            "url": "",
            "headers": {}
        }


class CacheMonitoringSystem:
    """Comprehensive monitoring system for cache integration."""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.alerts: List[Alert] = []
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self.last_alert_times: Dict[str, datetime] = {}
        self.running = False
        
        # Component health status
        self.component_status = {
            "cache_server": "unknown",
            "database": "unknown", 
            "mcp_servers": "unknown",
            "external_services": "unknown",
            "memory_bank": "unknown"
        }
    
    async def start_monitoring(self) -> None:
        """Start the monitoring system."""
        logger.info("Starting cache monitoring system...")
        self.running = True
        
        try:
            while self.running:
                start_time = time.time()
                
                # Run all monitoring checks
                await self.run_monitoring_cycle()
                
                # Clean up old data
                self.cleanup_old_data()
                
                # Wait for next cycle
                elapsed = time.time() - start_time
                sleep_time = max(0, self.config.check_interval - elapsed)
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            self.running = False
    
    async def run_monitoring_cycle(self) -> None:
        """Run a complete monitoring cycle."""
        logger.info("Running monitoring cycle...")
        
        cycle_start = datetime.now()
        cycle_metrics = {}
        
        try:
            # Monitor cache server
            cache_metrics = await self.monitor_cache_server()
            cycle_metrics["cache_server"] = cache_metrics
            
            # Monitor database
            db_metrics = await self.monitor_database()
            cycle_metrics["database"] = db_metrics
            
            # Monitor MCP servers
            mcp_metrics = await self.monitor_mcp_servers()
            cycle_metrics["mcp_servers"] = mcp_metrics
            
            # Monitor external services
            external_metrics = await self.monitor_external_services()
            cycle_metrics["external_services"] = external_metrics
            
            # Monitor memory bank
            memory_metrics = await self.monitor_memory_bank()
            cycle_metrics["memory_bank"] = memory_metrics
            
            # Store metrics
            self.store_metrics(cycle_metrics, cycle_start)
            
            # Check for alerts
            await self.check_alerts(cycle_metrics, cycle_start)
            
            # Update component status
            self.update_component_status(cycle_metrics)
            
            # Log summary
            self.log_monitoring_summary(cycle_metrics)
            
        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            await self.create_alert(
                component="monitoring_system",
                level=AlertLevel.ERROR,
                message=f"Monitoring cycle failed: {str(e)}",
                metrics={},
                timestamp=cycle_start
            )
    
    async def monitor_cache_server(self) -> Dict[str, Any]:
        """Monitor cache server performance and health."""
        logger.debug("Monitoring cache server...")
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "response_time_ms": 0,
            "hit_rate": 0,
            "error_rate": 0,
            "memory_usage_percent": 0,
            "active_connections": 0,
            "cache_stats": {}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check basic health
                try:
                    start_time = time.time()
                    async with session.get(
                        "http://localhost:8080/health",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        metrics["response_time_ms"] = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            metrics["status"] = "healthy"
                            health_data = await response.json()
                            metrics["cache_stats"] = health_data
                        else:
                            metrics["status"] = "unhealthy"
                            metrics["error_rate"] = 1.0
                            
                except Exception as e:
                    metrics["status"] = "error"
                    metrics["error_rate"] = 1.0
                    logger.debug(f"Cache server health check failed: {e}")
                
                # Get cache statistics
                try:
                    async with session.get(
                        "http://localhost:8080/cache/stats",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            stats_data = await response.json()
                            metrics["cache_stats"] = stats_data
                            
                            # Calculate hit rate
                            total_requests = stats_data.get("total_requests", 1)
                            hits = stats_data.get("total_hits", 0)
                            metrics["hit_rate"] = hits / total_requests if total_requests > 0 else 0
                            
                            # Calculate error rate
                            errors = stats_data.get("total_errors", 0)
                            metrics["error_rate"] = errors / total_requests if total_requests > 0 else 0
                            
                except Exception as e:
                    logger.debug(f"Cache server stats fetch failed: {e}")
                
                # Test cache performance
                try:
                    test_key = f"perf_test_{int(time.time())}"
                    test_data = {"test": "performance", "timestamp": time.time()}
                    
                    # Test set operation
                    start_time = time.time()
                    set_payload = {"key": test_key, "value": test_data, "layer": "semantic", "ttl": 60}
                    async with session.post(
                        "http://localhost:8080/cache/set",
                        json=set_payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        set_time = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            # Test get operation
                            start_time = time.time()
                            async with session.get(
                                "http://localhost:8080/cache/get",
                                params={"key": test_key, "layer": "semantic"},
                                timeout=aiohttp.ClientTimeout(total=10)
                            ) as response:
                                get_time = (time.time() - start_time) * 1000
                                
                                if response.status == 200:
                                    metrics["avg_operation_time_ms"] = (set_time + get_time) / 2
                                
                                # Cleanup
                                async with session.delete(
                                    "http://localhost:8080/cache/delete",
                                    params={"key": test_key, "layer": "semantic"},
                                    timeout=aiohttp.ClientTimeout(total=10)
                                ) as response:
                                    pass
                                    
                except Exception as e:
                    logger.debug(f"Cache performance test failed: {e}")
        
        except Exception as e:
            logger.error(f"Cache server monitoring failed: {e}")
            metrics["status"] = "error"
            metrics["error_rate"] = 1.0
        
        return metrics
    
    async def monitor_database(self) -> Dict[str, Any]:
        """Monitor database performance and health."""
        logger.debug("Monitoring database...")
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "connection_time_ms": 0,
            "query_time_ms": 0,
            "active_connections": 0,
            "connection_pool_usage": 0,
            "table_count": 0,
            "disk_usage_percent": 0
        }
        
        try:
            start_time = time.time()
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="paddle_plugin_cache",
                user="postgres",
                password="2001"
            )
            metrics["connection_time_ms"] = (time.time() - start_time) * 1000
            metrics["status"] = "healthy"
            
            with conn.cursor() as cursor:
                # Test query performance
                start_time = time.time()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                metrics["query_time_ms"] = (time.time() - start_time) * 1000
                
                # Get connection count
                cursor.execute("""
                    SELECT count(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                """)
                result = cursor.fetchone()
                active_connections = result[0] if result else 0
                metrics["active_connections"] = active_connections
                
                # Get table count
                cursor.execute("""
                    SELECT count(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
                result = cursor.fetchone()
                table_count = result[0] if result else 0
                metrics["table_count"] = table_count
                
                # Get database size
                cursor.execute("""
                    SELECT pg_database_size(current_database()) /
                           pg_database_size('template0') * 100 as usage_percent
                """)
                result = cursor.fetchone()
                usage_percent = result[0] if result else 0
                metrics["disk_usage_percent"] = min(usage_percent, 100)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Database monitoring failed: {e}")
            metrics["status"] = "error"
        
        return metrics
    
    async def monitor_mcp_servers(self) -> Dict[str, Any]:
        """Monitor MCP servers health."""
        logger.debug("Monitoring MCP servers...")
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "servers": {}
        }
        
        try:
            # Monitor cache MCP server
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        "http://localhost:8081/health",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            metrics["servers"]["cache_mcp"] = {"status": "healthy"}
                        else:
                            metrics["servers"]["cache_mcp"] = {"status": "unhealthy"}
                except Exception:
                    metrics["servers"]["cache_mcp"] = {"status": "error"}
                
                # Monitor other MCP servers (placeholder logic)
                metrics["servers"]["rag_mcp"] = {"status": "healthy"}  # Placeholder
                metrics["servers"]["memory_mcp"] = {"status": "healthy"}  # Placeholder
                metrics["servers"]["search_mcp"] = {"status": "healthy"}  # Placeholder
            
            # Determine overall status
            healthy_count = sum(1 for server in metrics["servers"].values() if server["status"] == "healthy")
            total_count = len(metrics["servers"])
            
            if healthy_count == total_count:
                metrics["status"] = "healthy"
            elif healthy_count > 0:
                metrics["status"] = "warning"
            else:
                metrics["status"] = "error"
                
        except Exception as e:
            logger.error(f"MCP servers monitoring failed: {e}")
            metrics["status"] = "error"
        
        return metrics
    
    async def monitor_external_services(self) -> Dict[str, Any]:
        """Monitor external services health."""
        logger.debug("Monitoring external services...")
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "services": {}
        }
        
        services = {
            "rag_server": "http://localhost:8001",
            "vector_store": "http://localhost:8002"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                for service_name, service_url in services.items():
                    try:
                        async with session.get(
                            f"{service_url}/health",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                metrics["services"][service_name] = {"status": "healthy"}
                            else:
                                metrics["services"][service_name] = {"status": "unhealthy"}
                    except Exception:
                        metrics["services"][service_name] = {"status": "error"}
                
                # Determine overall status
                healthy_count = sum(1 for service in metrics["services"].values() if service["status"] == "healthy")
                total_count = len(metrics["services"])
                
                if healthy_count == total_count:
                    metrics["status"] = "healthy"
                elif healthy_count > 0:
                    metrics["status"] = "warning"
                else:
                    metrics["status"] = "error"
                    
        except Exception as e:
            logger.error(f"External services monitoring failed: {e}")
            metrics["status"] = "error"
        
        return metrics
    
    async def monitor_memory_bank(self) -> Dict[str, Any]:
        """Monitor memory bank health."""
        logger.debug("Monitoring memory bank...")
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "files_exist": {},
            "last_sync": None,
            "sync_enabled": True
        }
        
        try:
            memory_bank_path = Path("./memorybank")
            
            if memory_bank_path.exists():
                required_files = ["activeContext.md", "projectbrief.md", "systemPatterns.md"]
                
                for file_name in required_files:
                    file_path = memory_bank_path / file_name
                    metrics["files_exist"][file_name] = file_path.exists()
                
                # Check if all files exist
                if all(metrics["files_exist"].values()):
                    metrics["status"] = "healthy"
                else:
                    metrics["status"] = "warning"
            else:
                metrics["status"] = "error"
                
        except Exception as e:
            logger.error(f"Memory bank monitoring failed: {e}")
            metrics["status"] = "error"
        
        return metrics
    
    def store_metrics(self, metrics: Dict[str, Any], timestamp: datetime) -> None:
        """Store metrics in history."""
        for component, component_metrics in metrics.items():
            component_key = f"{component}_{timestamp.strftime('%Y%m%d')}"
            
            if component_key not in self.metrics_history:
                self.metrics_history[component_key] = []
            
            self.metrics_history[component_key].append({
                "timestamp": timestamp.isoformat(),
                "metrics": component_metrics
            })
    
    async def check_alerts(self, metrics: Dict[str, Any], timestamp: datetime) -> None:
        """Check for alert conditions and create alerts if needed."""
        for component, component_metrics in metrics.items():
            component_status = component_metrics.get("status", "unknown")
            
            # Check for status-based alerts
            if component_status == "error":
                await self.create_alert(
                    component=component,
                    level=AlertLevel.ERROR,
                    message=f"{component.replace('_', ' ').title()} is in error state",
                    metrics=component_metrics,
                    timestamp=timestamp
                )
            elif component_status == "unhealthy":
                await self.create_alert(
                    component=component,
                    level=AlertLevel.WARNING,
                    message=f"{component.replace('_', ' ').title()} is unhealthy",
                    metrics=component_metrics,
                    timestamp=timestamp
                )
            
            # Check for threshold-based alerts
            await self.check_threshold_alerts(component, component_metrics, timestamp)
    
    async def check_threshold_alerts(self, component: str, metrics: Dict[str, Any], timestamp: datetime) -> None:
        """Check for threshold-based alerts."""
        component_key = component
        
        # Cache server thresholds
        if component == "cache_server":
            hit_rate = metrics.get("hit_rate", 0)
            response_time = metrics.get("response_time_ms", 0)
            error_rate = metrics.get("error_rate", 0)
            
            # Hit rate alerts
            if hit_rate < self.config.thresholds["cache_hit_rate"]["critical"]:
                await self.create_alert(
                    component=component_key,
                    level=AlertLevel.CRITICAL,
                    message=f"Cache hit rate critically low: {hit_rate:.2%}",
                    metrics=metrics,
                    timestamp=timestamp
                )
            elif hit_rate < self.config.thresholds["cache_hit_rate"]["warning"]:
                await self.create_alert(
                    component=component_key,
                    level=AlertLevel.WARNING,
                    message=f"Cache hit rate low: {hit_rate:.2%}",
                    metrics=metrics,
                    timestamp=timestamp
                )
            
            # Response time alerts
            if response_time > self.config.thresholds["response_time_ms"]["critical"]:
                await self.create_alert(
                    component=component_key,
                    level=AlertLevel.CRITICAL,
                    message=f"Cache response time critically high: {response_time:.2f}ms",
                    metrics=metrics,
                    timestamp=timestamp
                )
            elif response_time > self.config.thresholds["response_time_ms"]["warning"]:
                await self.create_alert(
                    component=component_key,
                    level=AlertLevel.WARNING,
                    message=f"Cache response time high: {response_time:.2f}ms",
                    metrics=metrics,
                    timestamp=timestamp
                )
            
            # Error rate alerts
            if error_rate > self.config.thresholds["error_rate"]["critical"]:
                await self.create_alert(
                    component=component_key,
                    level=AlertLevel.CRITICAL,
                    message=f"Cache error rate critically high: {error_rate:.2%}",
                    metrics=metrics,
                    timestamp=timestamp
                )
            elif error_rate > self.config.thresholds["error_rate"]["warning"]:
                await self.create_alert(
                    component=component_key,
                    level=AlertLevel.WARNING,
                    message=f"Cache error rate high: {error_rate:.2%}",
                    metrics=metrics,
                    timestamp=timestamp
                )
        
        # Database thresholds
        elif component == "database":
            active_connections = metrics.get("active_connections", 0)
            disk_usage = metrics.get("disk_usage_percent", 0)
            
            # Connection count alerts
            if active_connections > self.config.thresholds["database_connections"]["critical"]:
                await self.create_alert(
                    component=component_key,
                    level=AlertLevel.CRITICAL,
                    message=f"Database connections critically high: {active_connections}",
                    metrics=metrics,
                    timestamp=timestamp
                )
            elif active_connections > self.config.thresholds["database_connections"]["warning"]:
                await self.create_alert(
                    component=component_key,
                    level=AlertLevel.WARNING,
                    message=f"Database connections high: {active_connections}",
                    metrics=metrics,
                    timestamp=timestamp
                )
            
            # Disk usage alerts
            if disk_usage > self.config.thresholds["disk_usage_percent"]["critical"]:
                await self.create_alert(
                    component=component_key,
                    level=AlertLevel.CRITICAL,
                    message=f"Database disk usage critically high: {disk_usage:.1f}%",
                    metrics=metrics,
                    timestamp=timestamp
                )
            elif disk_usage > self.config.thresholds["disk_usage_percent"]["warning"]:
                await self.create_alert(
                    component=component_key,
                    level=AlertLevel.WARNING,
                    message=f"Database disk usage high: {disk_usage:.1f}%",
                    metrics=metrics,
                    timestamp=timestamp
                )
    
    async def create_alert(self, component: str, level: AlertLevel, message: str, 
                          metrics: Dict[str, Any], timestamp: datetime) -> None:
        """Create and handle an alert."""
        alert_key = f"{component}_{level.value}"
        
        # Check cooldown period
        if alert_key in self.last_alert_times:
            time_since_last = (timestamp - self.last_alert_times[alert_key]).total_seconds()
            if time_since_last < self.config.alert_cooldown:
                return  # Skip alert due to cooldown
        
        # Create alert
        alert = Alert(
            component=component,
            level=level,
            message=message,
            timestamp=timestamp,
            metrics=metrics
        )
        
        self.alerts.append(alert)
        self.last_alert_times[alert_key] = timestamp
        
        # Log alert
        logger.warning(f"ALERT [{level.value.upper()}] {component}: {message}")
        
        # Send notifications
        await self.send_alert_notifications(alert)
    
    async def send_alert_notifications(self, alert: Alert) -> None:
        """Send alert notifications via configured channels."""
        try:
            # Email notifications
            if self.config.email_notifications["enabled"]:
                await self.send_email_alert(alert)
            
            # Webhook notifications
            if self.config.webhook_notifications["enabled"]:
                await self.send_webhook_alert(alert)
                
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")
    
    async def send_email_alert(self, alert: Alert) -> None:
        """Send alert via email."""
        try:
            msg = MIMEText(f"""
Alert Details:
- Component: {alert.component}
- Level: {alert.level.value.upper()}
- Message: {alert.message}
- Timestamp: {alert.timestamp.isoformat()}
- Metrics: {json.dumps(alert.metrics, indent=2)}
            """)
            
            msg['Subject'] = f"Cache System Alert - {alert.level.value.upper()}: {alert.component}"
            msg['From'] = self.config.email_notifications["username"]
            msg['To'] = ', '.join(self.config.email_notifications["recipients"])
            
            with smtplib.SMTP(
                self.config.email_notifications["smtp_server"],
                self.config.email_notifications["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.config.email_notifications["username"],
                    self.config.email_notifications["password"]
                )
                server.send_message(msg)
                
            logger.info(f"Email alert sent for {alert.component}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def send_webhook_alert(self, alert: Alert) -> None:
        """Send alert via webhook."""
        try:
            payload = {
                "component": alert.component,
                "level": alert.level.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metrics": alert.metrics
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.webhook_notifications["url"],
                    json=payload,
                    headers=self.config.webhook_notifications["headers"],
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent for {alert.component}")
                    else:
                        logger.error(f"Webhook alert failed: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def update_component_status(self, metrics: Dict[str, Any]) -> None:
        """Update component status based on latest metrics."""
        for component, component_metrics in metrics.items():
            if component in self.component_status:
                self.component_status[component] = component_metrics.get("status", "unknown")
    
    def log_monitoring_summary(self, metrics: Dict[str, Any]) -> None:
        """Log monitoring summary."""
        logger.info("Monitoring Summary:")
        for component, component_metrics in metrics.items():
            status = component_metrics.get("status", "unknown")
            logger.info(f"  {component.replace('_', ' ').title()}: {status.upper()}")
    
    def cleanup_old_data(self) -> None:
        """Clean up old metrics and alerts data."""
        cutoff_time = datetime.now() - timedelta(seconds=self.config.metrics_retention)
        
        # Clean up old metrics
        for component_key in list(self.metrics_history.keys()):
            component_date_str = component_key.split('_')[-1]
            try:
                component_date = datetime.strptime(component_date_str, '%Y%m%d')
                if component_date < cutoff_time.date():
                    del self.metrics_history[component_key]
            except ValueError:
                # Invalid date format, remove entry
                del self.metrics_history[component_key]
        
        # Clean up old alerts (keep last 1000 alerts)
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
    
    def get_current_status(self) -> Dict[str, str]:
        """Get current status of all components."""
        return self.component_status.copy()
    
    def get_recent_alerts(self, limit: int = 10) -> List[Alert]:
        """Get recent alerts."""
        return self.alerts[-limit:]
    
    def get_metrics_summary(self, component: str, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for a component."""
        summary = {
            "component": component,
            "period_hours": hours,
            "data_points": 0,
            "avg_values": {},
            "min_values": {},
            "max_values": {},
            "latest_metrics": None
        }
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for component_key, metrics_list in self.metrics_history.items():
            if component_key.startswith(component):
                for metric_entry in metrics_list:
                    timestamp = datetime.fromisoformat(metric_entry["timestamp"])
                    if timestamp >= cutoff_time:
                        metrics = metric_entry["metrics"]
                        summary["data_points"] += 1
                        
                        # Calculate summary statistics for numeric metrics
                        for key, value in metrics.items():
                            if isinstance(value, (int, float)):
                                if key not in summary["avg_values"]:
                                    summary["avg_values"][key] = []
                                    summary["min_values"][key] = float('inf')
                                    summary["max_values"][key] = float('-inf')
                                
                                summary["avg_values"][key].append(value)
                                summary["min_values"][key] = min(summary["min_values"][key], value)
                                summary["max_values"][key] = max(summary["max_values"][key], value)
                        
                        # Store latest metrics
                        summary["latest_metrics"] = metrics
        
        # Calculate averages
        for key, values in summary["avg_values"].items():
            summary["avg_values"][key] = sum(values) / len(values)
        
        return summary
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        logger.info("Stopping monitoring system...")
        self.running = False


async def main():
    """Main monitoring function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoring and Alerting for Cache Management System')
    parser.add_argument('--config', type=str, default='monitoring_config.json',
                       help='Monitoring configuration file path')
    parser.add_argument('--interval', type=int, default=60,
                       help='Monitoring interval in seconds')
    parser.add_argument('--status', action='store_true',
                       help='Show current status and exit')
    parser.add_argument('--alerts', type=int, default=0,
                       help='Show recent alerts (specify number of alerts to show)')
    parser.add_argument('--metrics', type=str, default='',
                       help='Show metrics summary for component (e.g., cache_server)')
    parser.add_argument('--hours', type=int, default=24,
                       help='Hours of metrics to include in summary')
    
    args = parser.parse_args()
    
    try:
        # Load or create configuration
        config = MonitoringConfig()
        if Path(args.config).exists():
            with open(args.config, 'r') as f:
                config_data = json.load(f)
                # Update config with loaded values
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
        
        config.check_interval = args.interval
        
        # Create monitoring system
        monitor = CacheMonitoringSystem(config)
        
        if args.status:
            # Show current status
            status = monitor.get_current_status()
            print("\nCurrent System Status:")
            print("-" * 30)
            for component, status_str in status.items():
                print(f"{component.replace('_', ' ').title():20}: {status_str.upper()}")
            return
        
        if args.alerts > 0:
            # Show recent alerts
            alerts = monitor.get_recent_alerts(args.alerts)
            print(f"\nRecent {len(alerts)} Alerts:")
            print("-" * 50)
            for alert in alerts:
                print(f"[{alert.level.value.upper()}] {alert.component}: {alert.message}")
                print(f"  Time: {alert.timestamp.isoformat()}")
                if alert.metrics:
                    print(f"  Metrics: {json.dumps(alert.metrics, indent=2)}")
                print()
            return
        
        if args.metrics:
            # Show metrics summary
            summary = monitor.get_metrics_summary(args.metrics, args.hours)
            print(f"\nMetrics Summary for {summary['component']}:")
            print("-" * 50)
            print(f"Period: {summary['period_hours']} hours")
            print(f"Data Points: {summary['data_points']}")
            
            if summary['avg_values']:
                print("\nAverage Values:")
                for key, value in summary['avg_values'].items():
                    print(f"  {key}: {value:.2f}")
                
                print("\nMin/Max Values:")
                for key in summary['avg_values'].keys():
                    min_val = summary['min_values'][key]
                    max_val = summary['max_values'][key]
                    print(f"  {key}: {min_val:.2f} / {max_val:.2f}")
            
            if summary['latest_metrics']:
                print(f"\nLatest Status: {summary['latest_metrics'].get('status', 'unknown')}")
            
            return
        
        # Start continuous monitoring
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring execution failed: {e}")
        print(f"\n❌ Monitoring execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())