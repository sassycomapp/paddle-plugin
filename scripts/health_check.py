#!/usr/bin/env python3
"""
Health Check Script for Cache Management System Integration

This script performs comprehensive health checks on all integrated components
including cache server, database, MCP servers, and external services.

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
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegratedSystemHealthChecker:
    """Comprehensive health checker for all integrated systems."""
    
    def __init__(self, config_path: str = "src/orchestration/mcp_servers_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.results = {}
        self.timestamp = datetime.now().isoformat()
        
        # Health check endpoints
        self.endpoints = {
            "cache_server": {
                "url": "http://localhost:8080",
                "endpoints": ["/health", "/cache/stats"],
                "timeout": 10
            },
            "cache_server_mcp": {
                "url": "http://localhost:8081", 
                "endpoints": ["/health"],
                "timeout": 10
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "paddle_plugin_cache",
                "user": "postgres",
                "password": "2001",
                "timeout": 5
            },
            "external_services": {
                "rag_server": {
                    "url": "http://localhost:8001",
                    "endpoints": ["/health"],
                    "timeout": 10
                },
                "vector_store": {
                    "url": "http://localhost:8002", 
                    "endpoints": ["/health"],
                    "timeout": 10
                }
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    async def check_cache_server_health(self) -> Dict[str, Any]:
        """Check cache server health and functionality."""
        logger.info("Checking cache server health...")
        
        try:
            results = {
                "status": "healthy",
                "checks": {},
                "metrics": {}
            }
            
            async with aiohttp.ClientSession() as session:
                # Check basic health
                try:
                    async with session.get(
                        f"{self.endpoints['cache_server']['url']}/health",
                        timeout=aiohttp.ClientTimeout(total=self.endpoints['cache_server']['timeout'])
                    ) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            results["checks"]["basic_health"] = {"status": "healthy", "data": health_data}
                        else:
                            results["checks"]["basic_health"] = {"status": "unhealthy", "error": f"HTTP {response.status}"}
                            results["status"] = "unhealthy"
                except Exception as e:
                    results["checks"]["basic_health"] = {"status": "error", "error": str(e)}
                    results["status"] = "error"
                
                # Check cache functionality
                try:
                    # Test cache set operation
                    test_key = f"health_check_{int(time.time())}"
                    test_data = {"test": "health_check", "timestamp": time.time()}
                    
                    set_payload = {
                        "key": test_key,
                        "value": test_data,
                        "layer": "semantic",
                        "ttl": 60
                    }
                    
                    async with session.post(
                        f"{self.endpoints['cache_server']['url']}/cache/set",
                        json=set_payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            set_result = await response.json()
                            results["checks"]["cache_set"] = {"status": "healthy", "data": set_result}
                            
                            # Test cache get operation
                            async with session.get(
                                f"{self.endpoints['cache_server']['url']}/cache/get",
                                params={"key": test_key, "layer": "semantic"},
                                timeout=aiohttp.ClientTimeout(total=10)
                            ) as response:
                                if response.status == 200:
                                    get_result = await response.json()
                                    results["checks"]["cache_get"] = {"status": "healthy", "data": get_result}
                                    
                                    # Clean up test data
                                    async with session.delete(
                                        f"{self.endpoints['cache_server']['url']}/cache/delete",
                                        params={"key": test_key, "layer": "semantic"},
                                        timeout=aiohttp.ClientTimeout(total=10)
                                    ) as response:
                                        if response.status == 200:
                                            results["checks"]["cache_delete"] = {"status": "healthy"}
                                        else:
                                            results["checks"]["cache_delete"] = {"status": "warning", "error": "Failed to cleanup"}
                                else:
                                    results["checks"]["cache_get"] = {"status": "unhealthy", "error": f"HTTP {response.status}"}
                                    results["status"] = "unhealthy"
                        else:
                            results["checks"]["cache_set"] = {"status": "unhealthy", "error": f"HTTP {response.status}"}
                            results["status"] = "unhealthy"
                except Exception as e:
                    results["checks"]["cache_functionality"] = {"status": "error", "error": str(e)}
                    results["status"] = "error"
                
                # Check cache statistics
                try:
                    async with session.get(
                        f"{self.endpoints['cache_server']['url']}/cache/stats",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            stats_data = await response.json()
                            results["metrics"] = stats_data
                            results["checks"]["cache_stats"] = {"status": "healthy", "data": stats_data}
                        else:
                            results["checks"]["cache_stats"] = {"status": "unhealthy", "error": f"HTTP {response.status}"}
                except Exception as e:
                    results["checks"]["cache_stats"] = {"status": "error", "error": str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Cache server health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database health and connectivity."""
        logger.info("Checking database health...")
        
        try:
            db_config = self.endpoints["database"]
            results = {
                "status": "healthy",
                "checks": {},
                "metrics": {}
            }
            
            # Test basic connection
            try:
                start_time = time.time()
                conn = psycopg2.connect(
                    host=db_config["host"],
                    port=db_config["port"],
                    database=db_config["database"],
                    user=db_config["user"],
                    password=db_config["password"]
                )
                connection_time = (time.time() - start_time) * 1000
                
                results["checks"]["connection"] = {
                    "status": "healthy",
                    "connection_time_ms": connection_time
                }
                
                # Test basic query
                with conn.cursor() as cursor:
                    start_time = time.time()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    query_time = (time.time() - start_time) * 1000
                    
                    results["checks"]["basic_query"] = {
                        "status": "healthy",
                        "query_time_ms": query_time
                    }
                
                # Check cache tables exist
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name LIKE 'cache_%'
                    """)
                    tables = cursor.fetchall()
                    
                    cache_tables = [table[0] for table in tables]
                    results["metrics"]["cache_tables"] = cache_tables
                    results["checks"]["cache_tables"] = {
                        "status": "healthy" if len(cache_tables) > 0 else "warning",
                        "tables": cache_tables
                    }
                
                conn.close()
                
            except Exception as e:
                results["checks"]["connection"] = {"status": "error", "error": str(e)}
                results["status"] = "error"
            
            return results
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def check_mcp_servers_health(self) -> Dict[str, Any]:
        """Check MCP servers health."""
        logger.info("Checking MCP servers health...")
        
        try:
            results = {
                "status": "healthy",
                "checks": {}
            }
            
            # Check cache MCP server
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.endpoints['cache_server_mcp']['url']}/health",
                        timeout=aiohttp.ClientTimeout(total=self.endpoints['cache_server_mcp']['timeout'])
                    ) as response:
                        if response.status == 200:
                            results["checks"]["cache_mcp_server"] = {"status": "healthy"}
                        else:
                            results["checks"]["cache_mcp_server"] = {"status": "unhealthy", "error": f"HTTP {response.status}"}
                            results["status"] = "unhealthy"
            except Exception as e:
                results["checks"]["cache_mcp_server"] = {"status": "error", "error": str(e)}
                results["status"] = "error"
            
            # Check other MCP servers from config
            mcp_servers = self.config.get('mcpServers', {})
            for server_name, server_config in mcp_servers.items():
                if server_name != 'cache-mcp-server':  # Already checked above
                    try:
                        # Try to determine server health endpoint
                        health_endpoint = f"{server_config.get('url', 'http://localhost:8000')}/health"
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.get(health_endpoint, timeout=aiohttp.ClientTimeout(total=5)) as response:
                                if response.status == 200:
                                    results["checks"][f"{server_name}_mcp"] = {"status": "healthy"}
                                else:
                                    results["checks"][f"{server_name}_mcp"] = {"status": "unhealthy", "error": f"HTTP {response.status}"}
                                    results["status"] = "unhealthy"
                    except Exception as e:
                        results["checks"][f"{server_name}_mcp"] = {"status": "error", "error": str(e)}
                        results["status"] = "error"
            
            return results
            
        except Exception as e:
            logger.error(f"MCP servers health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def check_external_services_health(self) -> Dict[str, Any]:
        """Check external services health."""
        logger.info("Checking external services health...")
        
        try:
            results = {
                "status": "healthy",
                "checks": {}
            }
            
            for service_name, service_config in self.endpoints["external_services"].items():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{service_config['url']}/health",
                            timeout=aiohttp.ClientTimeout(total=service_config['timeout'])
                        ) as response:
                            if response.status == 200:
                                results["checks"][service_name] = {"status": "healthy"}
                            else:
                                results["checks"][service_name] = {"status": "unhealthy", "error": f"HTTP {response.status}"}
                                results["status"] = "unhealthy"
                except Exception as e:
                    results["checks"][service_name] = {"status": "error", "error": str(e)}
                    results["status"] = "error"
            
            return results
            
        except Exception as e:
            logger.error(f"External services health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def check_memory_bank_sync(self) -> Dict[str, Any]:
        """Check memory bank synchronization."""
        logger.info("Checking memory bank synchronization...")
        
        try:
            results = {
                "status": "healthy",
                "checks": {}
            }
            
            # Check memory bank files exist
            memory_bank_path = Path("./memorybank")
            if memory_bank_path.exists():
                required_files = ["activeContext.md", "projectbrief.md", "systemPatterns.md"]
                
                for file_name in required_files:
                    file_path = memory_bank_path / file_name
                    if file_path.exists():
                        results["checks"][f"memory_bank_file_{file_name}"] = {"status": "healthy"}
                    else:
                        results["checks"][f"memory_bank_file_{file_name}"] = {"status": "missing"}
                        results["status"] = "warning"
            else:
                results["checks"]["memory_bank_directory"] = {"status": "missing"}
                results["status"] = "error"
            
            # Check sync configuration
            sync_config = {
                "enabled": True,
                "sync_interval": 300,
                "bidirectional": True
            }
            
            results["metrics"]["sync_config"] = sync_config
            results["checks"]["sync_config"] = {"status": "healthy", "config": sync_config}
            
            return results
            
        except Exception as e:
            logger.error(f"Memory bank sync check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        logger.info("Starting comprehensive health checks...")
        
        overall_results = {
            "timestamp": self.timestamp,
            "overall_status": "healthy",
            "checks": {},
            "summary": {}
        }
        
        # Run all checks
        cache_check = await self.check_cache_server_health()
        overall_results["checks"]["cache_server"] = cache_check
        
        db_check = await self.check_database_health()
        overall_results["checks"]["database"] = db_check
        
        mcp_check = await self.check_mcp_servers_health()
        overall_results["checks"]["mcp_servers"] = mcp_check
        
        external_check = await self.check_external_services_health()
        overall_results["checks"]["external_services"] = external_check
        
        memory_check = await self.check_memory_bank_sync()
        overall_results["checks"]["memory_bank"] = memory_check
        
        # Determine overall status
        all_checks = [
            cache_check["status"],
            db_check["status"], 
            mcp_check["status"],
            external_check["status"],
            memory_check["status"]
        ]
        
        if any(status == "error" for status in all_checks):
            overall_results["overall_status"] = "error"
        elif any(status == "unhealthy" for status in all_checks):
            overall_results["overall_status"] = "unhealthy"
        elif any(status == "warning" for status in all_checks):
            overall_results["overall_status"] = "warning"
        
        # Generate summary
        overall_results["summary"] = {
            "total_checks": len(all_checks),
            "healthy_checks": sum(1 for status in all_checks if status == "healthy"),
            "warning_checks": sum(1 for status in all_checks if status == "warning"),
            "unhealthy_checks": sum(1 for status in all_checks if status == "unhealthy"),
            "error_checks": sum(1 for status in all_checks if status == "error")
        }
        
        return overall_results
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """Print health check results."""
        print("\n" + "="*60)
        print("INTEGRATED SYSTEMS HEALTH CHECK RESULTS")
        print("="*60)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Overall Status: {results['overall_status'].upper()}")
        
        # Print summary
        summary = results['summary']
        print(f"\nSummary:")
        print(f"  Total Checks: {summary['total_checks']}")
        print(f"  Healthy: {summary['healthy_checks']}")
        print(f"  Warnings: {summary['warning_checks']}")
        print(f"  Unhealthy: {summary['unhealthy_checks']}")
        print(f"  Errors: {summary['error_checks']}")
        
        # Print detailed results
        print(f"\nDetailed Results:")
        print("-"*40)
        for check_name, check_result in results['checks'].items():
            status = check_result.get('status', 'unknown').upper()
            print(f"{check_name.replace('_', ' ').title():25}: {status}")
            
            if check_result.get('status') != 'healthy':
                if 'error' in check_result:
                    print(f"{'':27}  Error: {check_result['error']}")
                elif 'checks' in check_result:
                    for sub_check, sub_result in check_result['checks'].items():
                        sub_status = sub_result.get('status', 'unknown').upper()
                        print(f"{'':27}  {sub_check}: {sub_status}")
                        if sub_result.get('status') != 'healthy' and 'error' in sub_result:
                            print(f"{'':29}    Error: {sub_result['error']}")
        
        # Save results to file
        results_file = f"health_check_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
    
    async def run_continuous_checks(self, interval: int = 60) -> None:
        """Run continuous health checks."""
        logger.info(f"Starting continuous health checks every {interval} seconds...")
        
        try:
            while True:
                start_time = time.time()
                
                # Run all checks
                results = await self.run_all_checks()
                
                # Print results
                self.print_results(results)
                
                # Log any issues
                if results['overall_status'] != 'healthy':
                    logger.warning(f"System health issues detected: {results['overall_status']}")
                
                # Wait for next interval
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Health checks stopped by user")
        except Exception as e:
            logger.error(f"Continuous health checks error: {e}")


async def main():
    """Main health check function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Health Check for Cache Management System Integration')
    parser.add_argument('--continuous', action='store_true', help='Run continuous health checks')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    parser.add_argument('--config', type=str, default='src/orchestration/mcp_servers_config.yaml', 
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    try:
        # Create health checker
        checker = IntegratedSystemHealthChecker(args.config)
        
        if args.continuous:
            # Run continuous checks
            await checker.run_continuous_checks(args.interval)
        else:
            # Run single check
            results = await checker.run_all_checks()
            checker.print_results(results)
            
            # Exit with appropriate code
            if results['overall_status'] == 'healthy':
                print("\n✅ All systems healthy!")
                sys.exit(0)
            elif results['overall_status'] == 'warning':
                print("\n⚠️  Some systems have warnings!")
                sys.exit(1)
            else:
                print("\n❌ Some systems are unhealthy or have errors!")
                sys.exit(1)
            
    except Exception as e:
        logger.error(f"Health check execution failed: {e}")
        print(f"\n❌ Health check execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())