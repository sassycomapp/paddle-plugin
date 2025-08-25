#!/usr/bin/env python3
"""
Health Check Script for Cache MCP Server

This script provides comprehensive health checks for the cache MCP server including:
- Database connectivity
- Cache layer health
- External service integration
- Performance metrics
- System resource monitoring

Author: KiloCode
License: Apache 2.0
"""

import os
import sys
import logging
import asyncio
import aiohttp
import time
import psutil
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""
    # Database settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "paddle_plugin_cache"
    db_user: str = "postgres"
    db_password: str = "2001"
    
    # Cache server settings
    cache_server_host: str = "localhost"
    cache_server_port: int = 8080
    cache_server_timeout: int = 10
    
    # External service settings
    rag_server_endpoint: str = "http://localhost:8001"
    vector_store_endpoint: str = "http://localhost:8002"
    kilocode_endpoint: str = "http://localhost:8080"
    
    # Health check settings
    check_interval: int = 30
    timeout: int = 10
    retry_attempts: int = 3
    retry_delay: int = 1
    
    # Performance thresholds
    max_response_time: float = 1.0  # seconds
    max_error_rate: float = 0.05     # 5%
    max_memory_usage: float = 0.8    # 80%
    max_cpu_usage: float = 0.8      # 80%
    max_disk_usage: float = 0.8     # 80%
    
    # Alerting settings
    alert_enabled: bool = True
    alert_email: Optional[str] = None
    alert_webhook: Optional[str] = None


class HealthChecker:
    """Handles health checks for the cache MCP server."""
    
    def __init__(self, config: HealthCheckConfig):
        """Initialize health checker."""
        self.config = config
        self.project_root = Path(__file__).parent.parent.parent
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.start_time = time.time()
        
        # Health status tracking
        self.health_status = {
            "overall": "unknown",
            "database": "unknown",
            "cache_server": "unknown",
            "external_services": {},
            "performance": {},
            "system_resources": {}
        }
        
        # Metrics tracking
        self.metrics = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "response_times": [],
            "error_rates": [],
            "memory_usage": [],
            "cpu_usage": [],
            "disk_usage": []
        }
    
    async def initialize(self):
        """Initialize the health checker."""
        try:
            self.logger.info("Initializing health checker...")
            
            # Create aiohttp session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
            
            self.logger.info("Health checker initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize health checker: {e}")
            raise
    
    async def close(self):
        """Close the health checker."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def run_health_checks(self):
        """Run comprehensive health checks."""
        try:
            self.logger.info("Running comprehensive health checks...")
            
            # Update metrics
            self.metrics["total_checks"] += 1
            
            start_time = time.time()
            
            # Run individual health checks
            await self._check_database()
            await self._check_cache_server()
            await self._check_external_services()
            await self._check_performance()
            await self._check_system_resources()
            
            # Calculate overall health status
            await self._calculate_overall_health()
            
            # Record response time
            response_time = time.time() - start_time
            self.metrics["response_times"].append(response_time)
            
            # Check if response time exceeds threshold
            if response_time > self.config.max_response_time:
                self.logger.warning(f"Response time {response_time:.2f}s exceeds threshold {self.config.max_response_time}s")
            
            # Log health status
            self.logger.info(f"Health check completed: {self.health_status['overall']}")
            
            # Send alerts if needed
            if self.config.alert_enabled and self.health_status["overall"] != "healthy":
                await self._send_alerts()
            
            return self.health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            self.metrics["failed_checks"] += 1
            raise
    
    async def _check_database(self):
        """Check database connectivity and health."""
        try:
            self.logger.info("Checking database health...")
            
            # Try to connect to database
            import asyncpg
            
            conn = await asyncpg.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                user=self.config.db_user,
                password=self.config.db_password,
                database=self.config.db_name
            )
            
            # Check database tables
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            
            table_names = [table['table_name'] for table in tables]
            expected_tables = ["predictive_cache", "semantic_cache", "vector_cache", "vector_diary"]
            
            missing_tables = set(expected_tables) - set(table_names)
            
            if missing_tables:
                self.logger.warning(f"Missing database tables: {missing_tables}")
                self.health_status["database"] = "degraded"
            else:
                self.health_status["database"] = "healthy"
                self.logger.info(f"Database healthy with {len(tables)} tables")
            
            # Check database performance
            stats = await conn.fetch("""
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
                    COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries
                FROM predictive_cache
            """)
            
            self.health_status["database_stats"] = stats[0]
            
            await conn.close()
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            self.health_status["database"] = "unhealthy"
            self.metrics["failed_checks"] += 1
    
    async def _check_cache_server(self):
        """Check cache server health."""
        try:
            self.logger.info("Checking cache server health...")
            
            # Check cache server endpoint
            async with self.session.get(
                f"http://{self.config.cache_server_host}:{self.config.cache_server_port}/health",
                timeout=self.config.timeout
            ) as response:
                if response.status == 200:
                    self.health_status["cache_server"] = "healthy"
                    
                    # Get cache server metrics
                    try:
                        metrics_response = await response.json()
                        self.health_status["cache_server_metrics"] = metrics_response
                    except:
                        self.logger.warning("Could not parse cache server metrics")
                        
                else:
                    self.logger.warning(f"Cache server health check failed: {response.status}")
                    self.health_status["cache_server"] = "degraded"
            
            # Test cache functionality
            await self._test_cache_functionality()
            
        except Exception as e:
            self.logger.error(f"Cache server health check failed: {e}")
            self.health_status["cache_server"] = "unhealthy"
            self.metrics["failed_checks"] += 1
    
    async def _test_cache_functionality(self):
        """Test cache functionality."""
        try:
            # Test cache set
            set_response = await self.session.post(
                f"http://{self.config.cache_server_host}:{self.config.cache_server_port}/cache/set",
                json={
                    "key": "health_check_test",
                    "value": "test_value",
                    "layer": "semantic"
                },
                timeout=self.config.timeout
            )
            
            if set_response.status == 200:
                # Test cache get
                get_response = await self.session.get(
                    f"http://{self.config.cache_server_host}:{self.config.cache_server_port}/cache/get",
                    params={"key": "health_check_test"},
                    timeout=self.config.timeout
                )
                
                if get_response.status == 200:
                    self.health_status["cache_functionality"] = "healthy"
                else:
                    self.logger.warning("Cache get test failed")
                    self.health_status["cache_functionality"] = "degraded"
            else:
                self.logger.warning("Cache set test failed")
                self.health_status["cache_functionality"] = "degraded"
                
        except Exception as e:
            self.logger.error(f"Cache functionality test failed: {e}")
            self.health_status["cache_functionality"] = "unhealthy"
    
    async def _check_external_services(self):
        """Check external service integration."""
        try:
            self.logger.info("Checking external services...")
            
            # Check MCP RAG Server
            if self.config.rag_server_endpoint:
                try:
                    async with self.session.get(
                        f"{self.config.rag_server_endpoint}/health",
                        timeout=self.config.timeout
                    ) as response:
                        if response.status == 200:
                            self.health_status["external_services"]["rag_server"] = "healthy"
                        else:
                            self.health_status["external_services"]["rag_server"] = "degraded"
                except Exception as e:
                    self.logger.error(f"RAG Server check failed: {e}")
                    self.health_status["external_services"]["rag_server"] = "unhealthy"
            
            # Check Vector Store MCP
            if self.config.vector_store_endpoint:
                try:
                    async with self.session.get(
                        f"{self.config.vector_store_endpoint}/health",
                        timeout=self.config.timeout
                    ) as response:
                        if response.status == 200:
                            self.health_status["external_services"]["vector_store"] = "healthy"
                        else:
                            self.health_status["external_services"]["vector_store"] = "degraded"
                except Exception as e:
                    self.logger.error(f"Vector Store check failed: {e}")
                    self.health_status["external_services"]["vector_store"] = "unhealthy"
            
            # Check KiloCode Orchestration
            if self.config.kilocode_endpoint:
                try:
                    async with self.session.get(
                        f"{self.config.kilocode_endpoint}/health",
                        timeout=self.config.timeout
                    ) as response:
                        if response.status == 200:
                            self.health_status["external_services"]["kilocode"] = "healthy"
                        else:
                            self.health_status["external_services"]["kilocode"] = "degraded"
                except Exception as e:
                    self.logger.error(f"KiloCode check failed: {e}")
                    self.health_status["external_services"]["kilocode"] = "unhealthy"
            
        except Exception as e:
            self.logger.error(f"External services check failed: {e}")
            self.metrics["failed_checks"] += 1
    
    async def _check_performance(self):
        """Check performance metrics."""
        try:
            self.logger.info("Checking performance metrics...")
            
            # Get cache server performance metrics
            try:
                async with self.session.get(
                    f"http://{self.config.cache_server_host}:{self.config.cache_server_port}/metrics",
                    timeout=self.config.timeout
                ) as response:
                    if response.status == 200:
                        metrics = await response.json()
                        self.health_status["performance"] = metrics
                        
                        # Check performance thresholds
                        if "response_time" in metrics:
                            if metrics["response_time"] > self.config.max_response_time:
                                self.logger.warning(f"Response time exceeds threshold: {metrics['response_time']}")
                        
                        if "error_rate" in metrics:
                            if metrics["error_rate"] > self.config.max_error_rate:
                                self.logger.warning(f"Error rate exceeds threshold: {metrics['error_rate']}")
                        
                    else:
                        self.logger.warning(f"Could not get performance metrics: {response.status}")
                        
            except Exception as e:
                self.logger.error(f"Performance metrics check failed: {e}")
                
        except Exception as e:
            self.logger.error(f"Performance check failed: {e}")
            self.metrics["failed_checks"] += 1
    
    async def _check_system_resources(self):
        """Check system resource usage."""
        try:
            self.logger.info("Checking system resources...")
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100.0
            self.health_status["system_resources"]["memory_usage"] = memory_usage
            self.metrics["memory_usage"].append(memory_usage)
            
            if memory_usage > self.config.max_memory_usage:
                self.logger.warning(f"Memory usage exceeds threshold: {memory_usage:.2%}")
            
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1) / 100.0
            self.health_status["system_resources"]["cpu_usage"] = cpu_usage
            self.metrics["cpu_usage"].append(cpu_usage)
            
            if cpu_usage > self.config.max_cpu_usage:
                self.logger.warning(f"CPU usage exceeds threshold: {cpu_usage:.2%}")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent / 100.0
            self.health_status["system_resources"]["disk_usage"] = disk_usage
            self.metrics["disk_usage"].append(disk_usage)
            
            if disk_usage > self.config.max_disk_usage:
                self.logger.warning(f"Disk usage exceeds threshold: {disk_usage:.2%}")
            
            # Network usage
            net_io = psutil.net_io_counters()
            self.health_status["system_resources"]["network_bytes_sent"] = net_io.bytes_sent
            self.health_status["system_resources"]["network_bytes_recv"] = net_io.bytes_recv
            
        except Exception as e:
            self.logger.error(f"System resources check failed: {e}")
            self.metrics["failed_checks"] += 1
    
    async def _calculate_overall_health(self):
        """Calculate overall health status."""
        try:
            healthy_components = 0
            total_components = 0
            
            # Check database
            total_components += 1
            if self.health_status["database"] == "healthy":
                healthy_components += 1
            
            # Check cache server
            total_components += 1
            if self.health_status["cache_server"] == "healthy":
                healthy_components += 1
            
            # Check external services
            for service in self.health_status["external_services"].values():
                total_components += 1
                if service == "healthy":
                    healthy_components += 1
            
            # Check system resources
            for resource in self.health_status["system_resources"].values():
                if isinstance(resource, (int, float)):
                    total_components += 1
                    if resource <= self.config.max_memory_usage:
                        healthy_components += 1
            
            # Calculate overall health
            if total_components > 0:
                health_ratio = healthy_components / total_components
                
                if health_ratio >= 0.9:
                    self.health_status["overall"] = "healthy"
                elif health_ratio >= 0.7:
                    self.health_status["overall"] = "degraded"
                else:
                    self.health_status["overall"] = "unhealthy"
            else:
                self.health_status["overall"] = "unknown"
            
            # Update metrics
            if self.health_status["overall"] == "healthy":
                self.metrics["successful_checks"] += 1
            else:
                self.metrics["failed_checks"] += 1
                
        except Exception as e:
            self.logger.error(f"Failed to calculate overall health: {e}")
            self.health_status["overall"] = "unknown"
    
    async def _send_alerts(self):
        """Send alerts for unhealthy components."""
        try:
            self.logger.info("Sending alerts...")
            
            alert_message = {
                "timestamp": datetime.now().isoformat(),
                "overall_health": self.health_status["overall"],
                "components": self.health_status,
                "metrics": self.metrics
            }
            
            # Send webhook alert
            if self.config.alert_webhook:
                try:
                    async with self.session.post(
                        self.config.alert_webhook,
                        json=alert_message,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            self.logger.info("Webhook alert sent successfully")
                        else:
                            self.logger.warning(f"Webhook alert failed: {response.status}")
                except Exception as e:
                    self.logger.error(f"Failed to send webhook alert: {e}")
            
            # Send email alert (if configured)
            if self.config.alert_email:
                self.logger.info(f"Email alert would be sent to {self.config.alert_email}")
                # Implementation would depend on email service
            
        except Exception as e:
            self.logger.error(f"Failed to send alerts: {e}")
    
    async def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        try:
            # Run health checks
            await self.run_health_checks()
            
            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "health_status": self.health_status,
                "metrics": self.metrics,
                "recommendations": await self._generate_recommendations()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate health report: {e}")
            raise
    
    async def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on health status."""
        recommendations = []
        
        # Database recommendations
        if self.health_status["database"] == "unhealthy":
            recommendations.append("Check database connectivity and configuration")
        
        # Cache server recommendations
        if self.health_status["cache_server"] == "unhealthy":
            recommendations.append("Restart cache server and check logs")
        
        # External service recommendations
        for service, status in self.health_status["external_services"].items():
            if status == "unhealthy":
                recommendations.append(f"Check {service} connectivity and configuration")
        
        # Performance recommendations
        if "performance" in self.health_status:
            performance = self.health_status["performance"]
            if "response_time" in performance and performance["response_time"] > self.config.max_response_time:
                recommendations.append("Consider optimizing cache performance or increasing resources")
        
        # System resource recommendations
        if "system_resources" in self.health_status:
            resources = self.health_status["system_resources"]
            if "memory_usage" in resources and resources["memory_usage"] > self.config.max_memory_usage:
                recommendations.append("Consider increasing memory or optimizing memory usage")
            if "cpu_usage" in resources and resources["cpu_usage"] > self.config.max_cpu_usage:
                recommendations.append("Consider increasing CPU resources or optimizing CPU usage")
            if "disk_usage" in resources and resources["disk_usage"] > self.config.max_disk_usage:
                recommendations.append("Consider increasing disk space or cleaning up disk space")
        
        return recommendations


async def main():
    """Main entry point for health checks."""
    try:
        # Create health check configuration
        config = HealthCheckConfig(
            db_host="localhost",
            db_port=5432,
            db_name="paddle_plugin_cache",
            db_user="postgres",
            db_password="2001",
            cache_server_host="localhost",
            cache_server_port=8080,
            rag_server_endpoint="http://localhost:8001",
            vector_store_endpoint="http://localhost:8002",
            kilocode_endpoint="http://localhost:8080",
            check_interval=30,
            timeout=10,
            retry_attempts=3,
            retry_delay=1,
            max_response_time=1.0,
            max_error_rate=0.05,
            max_memory_usage=0.8,
            max_cpu_usage=0.8,
            max_disk_usage=0.8,
            alert_enabled=True,
            alert_webhook="http://localhost:9090/alerts"
        )
        
        # Initialize health checker
        health_checker = HealthChecker(config)
        
        # Initialize
        await health_checker.initialize()
        
        # Run health checks
        report = await health_checker.get_health_report()
        
        # Print report
        print("\n" + "="*50)
        print("CACHE MCP SERVER HEALTH REPORT")
        print("="*50)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Uptime: {report['uptime_seconds']:.2f} seconds")
        print(f"Overall Health: {report['health_status']['overall'].upper()}")
        print("\nComponent Status:")
        for component, status in report['health_status'].items():
            if component != "overall":
                print(f"  {component}: {status.upper()}")
        print("\nMetrics:")
        print(f"  Total Checks: {report['metrics']['total_checks']}")
        print(f"  Successful: {report['metrics']['successful_checks']}")
        print(f"  Failed: {report['metrics']['failed_checks']}")
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
        print("="*50)
        
        # Close health checker
        await health_checker.close()
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        print(f"Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())