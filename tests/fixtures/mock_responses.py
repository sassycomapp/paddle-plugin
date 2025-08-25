"""
Mock Response Data for Testing

This module provides mock response data for various API and service responses
that are used in testing the token management system.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

# Mock API Responses
class MockAPIResponses:
    """Collection of mock API responses for testing."""
    
    @staticmethod
    def openai_chat_completion() -> Dict[str, Any]:
        """Mock OpenAI chat completion response."""
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you today?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 9,
                "total_tokens": 19
            }
        }
    
    @staticmethod
    def openai_embeddings() -> Dict[str, Any]:
        """Mock OpenAI embeddings response."""
        return {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                    "index": 0
                }
            ],
            "model": "text-embedding-ada-002",
            "usage": {
                "prompt_tokens": 8,
                "total_tokens": 8
            }
        }
    
    @staticmethod
    def anthropic_completion() -> Dict[str, Any]:
        """Mock Anthropic completion response."""
        return {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Hello! How can I help you today?"
                }
            ],
            "model": "claude-3-sonnet-20240229",
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 9,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0
            }
        }
    
    @staticmethod
    def vault_secrets_response() -> Dict[str, Any]:
        """Mock Vault secrets response."""
        return {
            "request_id": "12345678-1234-1234-1234-123456789012",
            "lease_id": "",
            "renewable": False,
            "lease_duration": 0,
            "data": {
                "database_host": "localhost",
                "database_port": 5432,
                "database_username": "token_manager",
                "database_password": "secure_password_123",
                "database_name": "token_management"
            },
            "wrap_info": None,
            "warnings": None,
            "auth": None
        }
    
    @staticmethod
    def vault_health_response() -> Dict[str, Any]:
        """Mock Vault health response."""
        return {
            "initialized": True,
            "sealed": False,
            "standby": False,
            "performance_standby": False,
            "replication_performance_mode": "disabled",
            "replication_dr_mode": "disabled",
            "server_time_utc": 1677652288,
            "version": "1.11.0",
            "cluster_name": "vault-cluster",
            "cluster_id": "12345678-1234-1234-1234-123456789012"
        }
    
    @staticmethod
    def memory_service_response() -> Dict[str, Any]:
        """Mock memory service response."""
        return {
            "id": "mem_123",
            "user_id": "user-1",
            "session_id": "session-1",
            "content": "This is a test memory entry",
            "metadata": {
                "type": "text",
                "created_at": "2024-01-20T14:30:15Z",
                "updated_at": "2024-01-20T14:30:15Z",
                "tags": ["test", "memory"]
            },
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        }
    
    @staticmethod
    def mcp_server_response() -> Dict[str, Any]:
        """Mock MCP server response."""
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "token_counter",
                        "description": "Count tokens in text",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "description": "Text to count tokens for"
                                }
                            },
                            "required": ["text"]
                        }
                    }
                ]
            }
        }
    
    @staticmethod
    def kilocode_response() -> Dict[str, Any]:
        """Mock KiloCode response."""
        return {
            "workflow_id": "wkf_123",
            "status": "completed",
            "steps": [
                {
                    "step_id": "step_1",
                    "name": "Token Counting",
                    "status": "completed",
                    "tokens_used": 150,
                    "duration_ms": 120
                },
                {
                    "step_id": "step_2", 
                    "name": "API Call",
                    "status": "completed",
                    "tokens_used": 75,
                    "duration_ms": 200
                }
            ],
            "total_tokens_used": 225,
            "total_duration_ms": 320,
            "result": {
                "output": "Workflow completed successfully",
                "metadata": {
                    "created_at": "2024-01-20T14:30:15Z",
                    "updated_at": "2024-01-20T14:30:15Z"
                }
            }
        }

# Mock Error Responses
class MockErrorResponses:
    """Collection of mock error responses for testing."""
    
    @staticmethod
    def rate_limit_exceeded() -> Dict[str, Any]:
        """Mock rate limit exceeded response."""
        return {
            "error": {
                "message": "Rate limit exceeded",
                "type": "rate_limit_error",
                "param": None,
                "code": "rate_limit_exceeded"
            },
            "type": "error"
        }
    
    @staticmethod
    def insufficient_tokens() -> Dict[str, Any]:
        """Mock insufficient tokens response."""
        return {
            "error": {
                "message": "Insufficient tokens for request",
                "type": "insufficient_tokens_error",
                "param": "tokens",
                "code": "insufficient_tokens"
            },
            "type": "error"
        }
    
    @staticmethod
    def authentication_failed() -> Dict[str, Any]:
        """Mock authentication failed response."""
        return {
            "error": {
                "message": "Authentication failed",
                "type": "authentication_error",
                "param": "api_key",
                "code": "authentication_failed"
            },
            "type": "error"
        }
    
    @staticmethod
    def invalid_request() -> Dict[str, Any]:
        """Mock invalid request response."""
        return {
            "error": {
                "message": "Invalid request",
                "type": "invalid_request_error",
                "param": "messages",
                "code": "invalid_request"
            },
            "type": "error"
        }
    
    @staticmethod
    def vault_unauthorized() -> Dict[str, Any]:
        """Mock Vault unauthorized response."""
        return {
            "errors": ["1 error occurred:\n\t* Invalid client token: invalid"],
            "request_id": "12345678-1234-1234-1234-123456789012"
        }
    
    @staticmethod
    def database_connection_error() -> Dict[str, Any]:
        """Mock database connection error response."""
        return {
            "error": {
                "message": "Database connection failed",
                "type": "database_error",
                "code": "connection_failed",
                "details": {
                    "host": "localhost",
                    "port": 5432,
                    "error": "Connection refused"
                }
            }
        }

# Mock Monitoring Responses
class MockMonitoringResponses:
    """Collection of mock monitoring responses for testing."""
    
    @staticmethod
    def system_health_metrics() -> Dict[str, Any]:
        """Mock system health metrics response."""
        return {
            "timestamp": "2024-01-20T14:30:15Z",
            "cpu_usage": 75.5,
            "memory_usage": 60.2,
            "disk_usage": 45.8,
            "network_io": {
                "in": 1024000,
                "out": 2048000
            },
            "database_connections": 25,
            "active_users": 150,
            "active_sessions": 200,
            "token_requests_per_minute": 300,
            "error_rate": 0.02,
            "response_time_avg": 150.5,
            "response_time_p95": 300.0,
            "response_time_p99": 500.0
        }
    
    @staticmethod
    def token_usage_summary() -> Dict[str, Any]:
        """Mock token usage summary response."""
        return {
            "period": "2024-01-20",
            "total_tokens_used": 150000,
            "total_requests": 1000,
            "unique_users": 50,
            "average_tokens_per_request": 150,
            "peak_tokens_per_minute": 5000,
            "cost_estimate": 15.00,
            "top_users": [
                {"user_id": "user-1", "tokens_used": 50000, "percentage": 33.3},
                {"user_id": "user-2", "tokens_used": 30000, "percentage": 20.0},
                {"user_id": "user-3", "tokens_used": 20000, "percentage": 13.3}
            ],
            "top_endpoints": [
                {"endpoint": "/api/chat/completions", "tokens_used": 80000, "percentage": 53.3},
                {"endpoint": "/api/embeddings", "tokens_used": 40000, "percentage": 26.7},
                {"endpoint": "/api/usage", "tokens_used": 30000, "percentage": 20.0}
            ]
        }
    
    @staticmethod
    def alert_list() -> List[Dict[str, Any]]:
        """Mock alert list response."""
        return [
            {
                "id": "alert-1",
                "type": "usage_threshold",
                "severity": "high",
                "title": "High Token Usage Alert",
                "message": "User user-1 has used 85% of their daily token limit",
                "user_id": "user-1",
                "timestamp": "2024-01-20T14:30:15Z",
                "status": "active",
                "resolved": False
            },
            {
                "id": "alert-2",
                "type": "system_health",
                "severity": "critical",
                "title": "System Health Critical",
                "message": "CPU usage exceeded 90% threshold",
                "user_id": None,
                "timestamp": "2024-01-20T15:45:30Z",
                "status": "active",
                "resolved": False
            }
        ]
    
    @staticmethod
    def performance_metrics() -> Dict[str, Any]:
        """Mock performance metrics response."""
        return {
            "timestamp": "2024-01-20T14:30:15Z",
            "token_counting": {
                "avg_time_ms": 50,
                "p95_time_ms": 100,
                "p99_time_ms": 200,
                "requests_per_second": 1000,
                "error_rate": 0.001
            },
            "rate_limiting": {
                "avg_time_ms": 10,
                "p95_time_ms": 25,
                "p99_time_ms": 50,
                "requests_per_second": 500,
                "error_rate": 0.01
            },
            "database_operations": {
                "avg_time_ms": 20,
                "p95_time_ms": 50,
                "p99_time_ms": 100,
                "queries_per_second": 200,
                "error_rate": 0.005
            },
            "api_calls": {
                "avg_time_ms": 500,
                "p95_time_ms": 1000,
                "p99_time_ms": 2000,
                "requests_per_second": 100,
                "error_rate": 0.02
            }
        }

# Mock Configuration Data
class MockConfigurationData:
    """Collection of mock configuration data for testing."""
    
    @staticmethod
    def rate_limit_config() -> Dict[str, Any]:
        """Mock rate limit configuration."""
        return {
            "default_limits": {
                "day": 10000,
                "hour": 1000,
                "minute": 100
            },
            "user_limits": {
                "user-1": {
                    "day": 20000,
                    "hour": 2000,
                    "minute": 200
                },
                "user-2": {
                    "day": 5000,
                    "hour": 500,
                    "minute": 50
                }
            },
            "burst_limits": {
                "default": 1000,
                "user-1": 2000,
                "user-2": 500
            }
        }
    
    @staticmethod
    def security_config() -> Dict[str, Any]:
        """Mock security configuration."""
        return {
            "token_expiry": {
                "access_token": 3600,
                "refresh_token": 86400,
                "session_token": 7200
            },
            "rate_limits": {
                "login_attempts": 5,
                "password_reset": 3,
                "api_calls": 1000
            },
            "encryption": {
                "algorithm": "AES-256",
                "key_rotation_days": 30,
                "salt_rounds": 12
            },
            "audit": {
                "log_level": "INFO",
                "retention_days": 90,
                "include_sensitive_data": False
            }
        }
    
    @staticmethod
    def monitoring_config() -> Dict[str, Any]:
        """Mock monitoring configuration."""
        return {
            "metrics": {
                "collection_interval": 60,
                "retention_days": 30,
                "export_enabled": True,
                "export_interval": 300
            },
            "alerts": {
                "enabled": True,
                "email_notifications": True,
                "slack_notifications": False,
                "thresholds": {
                    "cpu_usage": 80,
                    "memory_usage": 85,
                    "disk_usage": 90,
                    "error_rate": 0.05,
                    "response_time": 1000
                }
            },
            "health_checks": {
                "interval": 30,
                "timeout": 10,
                "retries": 3
            }
        }
    
    @staticmethod
    def vault_config() -> Dict[str, Any]:
        """Mock Vault configuration."""
        return {
            "url": "http://localhost:8200",
            "token": "s.1234567890",
            "timeout": 30,
            "retries": 3,
            "secrets": {
                "database": "secret/database/credentials",
                "api_keys": {
                    "openai": "secret/api_keys/openai",
                    "anthropic": "secret/api_keys/anthropic"
                },
                "config": "secret/config/app"
            }
        }

# Mock Test Data Generators
class MockTestDataGenerators:
    """Collection of mock test data generators."""
    
    @staticmethod
    def generate_token_usage_records(count: int = 100) -> List[Dict[str, Any]]:
        """Generate mock token usage records."""
        records = []
        for i in range(count):
            records.append({
                "id": f"usage_{i}",
                "user_id": f"user_{i % 10 + 1}",
                "session_id": f"session_{i}",
                "tokens_used": (i % 100) + 10,
                "api_endpoint": f"/api/endpoint_{i % 5}",
                "priority_level": ["high", "medium", "low"][i % 3],
                "timestamp": datetime.utcnow() - timedelta(minutes=i),
                "processing_time_ms": (i % 200) + 10,
                "success": i % 20 != 0  # 95% success rate
            })
        return records
    
    @staticmethod
    def generate_security_events(count: int = 50) -> List[Dict[str, Any]]:
        """Generate mock security events."""
        events = []
        event_types = ["token_access", "rate_limit_exceeded", "suspicious_activity", "authentication_failed"]
        severities = ["info", "warning", "critical"]
        
        for i in range(count):
            events.append({
                "id": f"sec_{i}",
                "event_type": event_types[i % len(event_types)],
                "user_id": f"user_{i % 10 + 1}" if i % 5 != 0 else None,
                "severity": severities[i % len(severities)],
                "description": f"Test security event {i}",
                "timestamp": datetime.utcnow() - timedelta(minutes=i),
                "ip_address": f"192.168.1.{i % 254 + 1}",
                "user_agent": f"Test Agent {i}"
            })
        return events
    
    @staticmethod
    def generate_performance_metrics(count: int = 24) -> List[Dict[str, Any]]:
        """Generate mock performance metrics."""
        metrics = []
        for i in range(count):
            metrics.append({
                "timestamp": datetime.utcnow() - timedelta(hours=i),
                "cpu_usage": 50 + (i % 30),
                "memory_usage": 40 + (i % 40),
                "disk_usage": 30 + (i % 50),
                "requests_per_second": 100 + (i % 200),
                "error_rate": 0.01 + (i % 10) * 0.001,
                "response_time_avg": 100 + (i % 100),
                "response_time_p95": 200 + (i % 200),
                "response_time_p99": 300 + (i % 300)
            })
        return metrics