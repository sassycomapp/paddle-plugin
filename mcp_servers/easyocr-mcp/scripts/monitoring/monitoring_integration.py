#!/usr/bin/env python3
"""
EasyOCR MCP Server Monitoring and Logging Integration

This module provides comprehensive monitoring and logging integration
with the existing system architecture.

Author: Kilo Code
License: Apache 2.0
"""

import os
import sys
import json
import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MetricType(Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class LogEntry:
    """Log entry data structure."""
    timestamp: str
    level: str
    message: str
    service: str
    component: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Metric:
    """Metric data structure."""
    name: str
    type: str
    value: float
    timestamp: str
    tags: Optional[Dict[str, str]] = None
    description: Optional[str] = None


@dataclass
class HealthStatus:
    """Health status data structure."""
    service: str
    status: str
    timestamp: str
    uptime: float
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    active_connections: int
    error_rate: float
    response_time: float


class MonitoringIntegration:
    """Handles monitoring and logging integration with existing system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize monitoring integration."""
        self.project_root = Path(__file__).parent.parent.parent
        self.config_path = config_path or str(self.project_root / "config" / "monitoring_config.json")
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize monitoring components
        self.log_buffer = []
        self.metrics_buffer = []
        self.health_status = None
        
        # Setup logging
        self._setup_logging()
        
        # Setup metrics collection
        self._setup_metrics_collection()
        
        # Setup health monitoring
        self._setup_health_monitoring()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Set defaults if not present
            if 'enabled' not in config:
                config['enabled'] = True
            
            if 'log_level' not in config:
                config['log_level'] = 'INFO'
            
            if 'metrics_interval' not in config:
                config['metrics_interval'] = 30
            
            if 'health_check_interval' not in config:
                config['health_check_interval'] = 60
            
            if 'log_retention_days' not in config:
                config['log_retention_days'] = 30
            
            if 'metrics_retention_days' not in config:
                config['metrics_retention_days'] = 7
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load monitoring configuration: {e}")
            # Return default configuration
            return {
                'enabled': True,
                'log_level': 'INFO',
                'metrics_interval': 30,
                'health_check_interval': 60,
                'log_retention_days': 30,
                'metrics_retention_days': 7
            }
    
    def _setup_logging(self):
        """Setup logging integration."""
        try:
            self.logger.info("Setting up logging integration...")
            
            # Create logging directory
            log_dir = self.project_root / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Setup file logging
            log_file = log_dir / 'easyocr_mcp.log'
            error_log_file = log_dir / 'easyocr_mcp_error.log'
            
            # Create file handlers
            file_handler = logging.FileHandler(log_file)
            error_handler = logging.FileHandler(error_log_file)
            
            # Create formatters
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            file_handler.setFormatter(formatter)
            error_handler.setFormatter(formatter)
            
            # Add handlers to root logger
            logging.getLogger().addHandler(file_handler)
            logging.getLogger().addHandler(error_handler)
            
            # Set log level
            log_level = getattr(logging, self.config['log_level'].upper())
            logging.getLogger().setLevel(log_level)
            
            self.logger.info("Logging integration setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup logging integration: {e}")
    
    def _setup_metrics_collection(self):
        """Setup metrics collection."""
        try:
            self.logger.info("Setting up metrics collection...")
            
            # Create metrics directory
            metrics_dir = self.project_root / 'metrics'
            metrics_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize metrics
            self.metrics = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0.0,
                'total_processing_time': 0.0,
                'memory_usage': 0.0,
                'cpu_usage': 0.0,
                'disk_usage': 0.0,
                'active_connections': 0,
                'last_request_time': None
            }
            
            # Create metrics file
            self.metrics_file = metrics_dir / 'metrics.json'
            
            self.logger.info("Metrics collection setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup metrics collection: {e}")
    
    def _setup_health_monitoring(self):
        """Setup health monitoring."""
        try:
            self.logger.info("Setting up health monitoring...")
            
            # Create health directory
            health_dir = self.project_root / 'health'
            health_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize health status
            self.health_status = HealthStatus(
                service='easyocr-mcp',
                status='healthy',
                timestamp=datetime.now().isoformat(),
                uptime=0.0,
                memory_usage=0.0,
                cpu_usage=0.0,
                disk_usage=0.0,
                active_connections=0,
                error_rate=0.0,
                response_time=0.0
            )
            
            # Create health file
            self.health_file = health_dir / 'health.json'
            
            self.logger.info("Health monitoring setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup health monitoring: {e}")
    
    def log_event(self, level: LogLevel, message: str, component: str, **kwargs):
        """Log an event with structured data."""
        try:
            # Create log entry
            log_entry = LogEntry(
                timestamp=datetime.now().isoformat(),
                level=level.value,
                message=message,
                service='easyocr-mcp',
                component=component,
                **kwargs
            )
            
            # Add to buffer
            self.log_buffer.append(log_entry)
            
            # Log to console
            logger.log(
                getattr(logging, level.value),
                f"[{component}] {message}",
                extra={
                    'service': 'easyocr-mcp',
                    'component': component,
                    **kwargs
                }
            )
            
            # Write to file
            self._write_log_entry(log_entry)
            
            # Check for error rate threshold
            if level == LogLevel.ERROR:
                self._check_error_threshold()
            
        except Exception as e:
            self.logger.error(f"Failed to log event: {e}")
    
    def _write_log_entry(self, log_entry: LogEntry):
        """Write log entry to file."""
        try:
            log_dir = self.project_root / 'logs'
            log_file = log_dir / 'structured_logs.json'
            
            # Read existing logs
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Add new log entry
            logs.append(asdict(log_entry))
            
            # Write back to file
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to write log entry: {e}")
    
    def record_metric(self, name: str, value: float, metric_type: MetricType, **kwargs):
        """Record a metric."""
        try:
            # Create metric
            metric = Metric(
                name=name,
                type=metric_type.value,
                value=value,
                timestamp=datetime.now().isoformat(),
                **kwargs
            )
            
            # Add to buffer
            self.metrics_buffer.append(metric)
            
            # Update in-memory metrics
            self._update_in_memory_metrics(name, value)
            
            # Write to file
            self._write_metric(metric)
            
        except Exception as e:
            self.logger.error(f"Failed to record metric: {e}")
    
    def _update_in_memory_metrics(self, name: str, value: float):
        """Update in-memory metrics."""
        try:
            if name == 'total_requests':
                self.metrics['total_requests'] += 1
            elif name == 'successful_requests':
                self.metrics['successful_requests'] += 1
            elif name == 'failed_requests':
                self.metrics['failed_requests'] += 1
            elif name == 'response_time':
                self.metrics['total_processing_time'] += value
                self.metrics['average_response_time'] = (
                    self.metrics['total_processing_time'] / 
                    max(self.metrics['total_requests'], 1)
                )
            elif name == 'memory_usage':
                self.metrics['memory_usage'] = value
            elif name == 'cpu_usage':
                self.metrics['cpu_usage'] = value
            elif name == 'disk_usage':
                self.metrics['disk_usage'] = value
            elif name == 'active_connections':
                self.metrics['active_connections'] = int(value)
            
            # Update last request time
            if name == 'total_requests':
                self.metrics['last_request_time'] = datetime.now().isoformat()
            
            # Write metrics to file
            self._write_metrics()
            
        except Exception as e:
            self.logger.error(f"Failed to update in-memory metrics: {e}")
    
    def _write_metric(self, metric: Metric):
        """Write metric to file."""
        try:
            metrics_dir = self.project_root / 'metrics'
            metrics_file = metrics_dir / 'metrics.json'
            
            # Read existing metrics
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
            else:
                metrics = []
            
            # Add new metric
            metrics.append(asdict(metric))
            
            # Write back to file
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to write metric: {e}")
    
    def _write_metrics(self):
        """Write in-memory metrics to file."""
        try:
            metrics_dir = self.project_root / 'metrics'
            metrics_file = metrics_dir / 'current_metrics.json'
            
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to write metrics: {e}")
    
    def update_health_status(self, **kwargs):
        """Update health status."""
        try:
            # Update health status
            for key, value in kwargs.items():
                if hasattr(self.health_status, key):
                    setattr(self.health_status, key, value)
            
            # Update timestamp
            self.health_status.timestamp = datetime.now().isoformat()
            
            # Calculate error rate
            if self.metrics['total_requests'] > 0:
                self.health_status.error_rate = (
                    self.metrics['failed_requests'] / 
                    self.metrics['total_requests']
                )
            
            # Calculate uptime
            if self.health_status.uptime == 0:
                self.health_status.uptime = time.time()
            else:
                self.health_status.uptime = time.time() - self.health_status.uptime
            
            # Write health status to file
            self._write_health_status()
            
        except Exception as e:
            self.logger.error(f"Failed to update health status: {e}")
    
    def _write_health_status(self):
        """Write health status to file."""
        try:
            health_dir = self.project_root / 'health'
            health_file = health_dir / 'health.json'
            
            with open(health_file, 'w') as f:
                json.dump(asdict(self.health_status), f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to write health status: {e}")
    
    def _check_error_threshold(self):
        """Check error rate threshold."""
        try:
            if self.metrics['total_requests'] > 0:
                error_rate = self.metrics['failed_requests'] / self.metrics['total_requests']
                
                if error_rate > 0.1:  # 10% error rate threshold
                    self.logger.warning(f"High error rate detected: {error_rate:.2%}")
                    
                    # Log error event
                    self.log_event(
                        LogLevel.WARNING,
                        f"High error rate detected: {error_rate:.2%}",
                        'monitoring'
                    )
                    
                    # Update health status
                    self.update_health_status(status='degraded')
                    
        except Exception as e:
            self.logger.error(f"Failed to check error threshold: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        try:
            return asdict(self.health_status)
        except Exception as e:
            self.logger.error(f"Failed to get health status: {e}")
            return {}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        try:
            return self.metrics
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {e}")
            return {}
    
    def get_logs(self, level: Optional[LogLevel] = None, component: Optional[str] = None, 
                 limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs with optional filtering."""
        try:
            log_dir = self.project_root / 'logs'
            log_file = log_dir / 'structured_logs.json'
            
            if not log_file.exists():
                return []
            
            with open(log_file, 'r') as f:
                logs = json.load(f)
            
            # Filter logs
            filtered_logs = logs
            if level:
                filtered_logs = [log for log in filtered_logs if log['level'] == level.value]
            if component:
                filtered_logs = [log for log in filtered_logs if log['component'] == component]
            
            # Limit results
            return filtered_logs[-limit:]
            
        except Exception as e:
            self.logger.error(f"Failed to get logs: {e}")
            return []
    
    def cleanup_old_logs(self):
        """Clean up old log entries."""
        try:
            retention_days = self.config.get('log_retention_days', 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            log_dir = self.project_root / 'logs'
            log_file = log_dir / 'structured_logs.json'
            
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                
                # Filter old logs
                filtered_logs = [
                    log for log in logs 
                    if datetime.fromisoformat(log['timestamp']) > cutoff_date
                ]
                
                # Write back to file
                with open(log_file, 'w') as f:
                    json.dump(filtered_logs, f, indent=2)
                
                self.logger.info(f"Cleaned up {len(logs) - len(filtered_logs)} old log entries")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
    
    def cleanup_old_metrics(self):
        """Clean up old metric entries."""
        try:
            retention_days = self.config.get('metrics_retention_days', 7)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            metrics_dir = self.project_root / 'metrics'
            metrics_file = metrics_dir / 'metrics.json'
            
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                
                # Filter old metrics
                filtered_metrics = [
                    metric for metric in metrics 
                    if datetime.fromisoformat(metric['timestamp']) > cutoff_date
                ]
                
                # Write back to file
                with open(metrics_file, 'w') as f:
                    json.dump(filtered_metrics, f, indent=2)
                
                self.logger.info(f"Cleaned up {len(metrics) - len(filtered_metrics)} old metric entries")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {e}")
    
    def export_logs(self, output_path: str, format: str = 'json'):
        """Export logs to file."""
        try:
            logs = self.get_logs()
            
            if format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(logs, f, indent=2)
            elif format == 'csv':
                import csv
                if logs:
                    with open(output_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                        writer.writeheader()
                        writer.writerows(logs)
            
            self.logger.info(f"Exported {len(logs)} logs to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export logs: {e}")
    
    def export_metrics(self, output_path: str, format: str = 'json'):
        """Export metrics to file."""
        try:
            metrics = self.get_metrics()
            
            if format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(metrics, f, indent=2)
            elif format == 'csv':
                import csv
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=metrics.keys())
                    writer.writeheader()
                    writer.writerow(metrics)
            
            self.logger.info(f"Exported metrics to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
    
    def start_monitoring(self):
        """Start monitoring process."""
        try:
            self.logger.info("Starting monitoring process...")
            
            # Start monitoring loop
            while True:
                try:
                    # Update health status
                    self.update_health_status()
                    
                    # Cleanup old data
                    self.cleanup_old_logs()
                    self.cleanup_old_metrics()
                    
                    # Sleep for monitoring interval
                    time.sleep(self.config.get('metrics_interval', 30))
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.logger.error(f"Monitoring loop error: {e}")
                    time.sleep(60)  # Wait before retrying
            
            self.logger.info("Monitoring process stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")


def main():
    """Main entry point for monitoring integration."""
    try:
        # Create monitoring integration
        monitoring = MonitoringIntegration()
        
        # Start monitoring
        monitoring.start_monitoring()
        
    except Exception as e:
        logger.error(f"Monitoring integration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()