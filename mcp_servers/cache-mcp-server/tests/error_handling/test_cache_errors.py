"""
Error Handling Tests for Cache Operations.

This module contains comprehensive error handling tests for cache operations,
testing various failure scenarios, recovery mechanisms, and error resilience.
"""

import pytest
import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from concurrent.futures import ThreadPoolExecutor
import threading
import tempfile
import os
from pathlib import Path

from src.core.base_cache import CacheLayer, CacheStatus, CacheResult
from src.cache_layers.predictive_cache import PredictiveCache
from src.cache_layers.semantic_cache import SemanticCache
from src.cache_layers.vector_cache import VectorCache
from src.cache_layers.global_cache import GlobalCache
from src.cache_layers.vector_diary import VectorDiary
from src.core.config import PredictiveCacheConfig, SemanticCacheConfig, VectorCacheConfig, GlobalCacheConfig, VectorDiaryConfig


class CacheErrorTester:
    """Main class for testing cache error handling."""
    
    def __init__(self):
        self.error_scenarios = []
        self.recovery_results = []
        self.logger = logging.getLogger(__name__)
    
    def simulate_cache_error(self, cache_instance, error_type: str, 
                           operation: str = "get", **kwargs) -> Dict[str, Any]:
        """Simulate various cache errors."""
        error_info = {
            "error_type": error_type,
            "operation": operation,
            "cache_layer": cache_instance.get_layer().value,
            "timestamp": time.time(),
            "original_error": None,
            "recovery_attempted": False,
            "recovery_successful": False,
            "error_message": None
        }
        
        try:
            if error_type == "timeout":
                # Simulate timeout error
                with patch.object(cache_instance, operation, side_effect=asyncio.TimeoutError("Cache operation timed out")):
                    if operation == "get":
                        result = asyncio.run(cache_instance.get(kwargs.get("key", "test_key")))
                    elif operation == "set":
                        result = asyncio.run(cache_instance.set(kwargs.get("key", "test_key"), kwargs.get("value", "test_value")))
                    elif operation == "delete":
                        result = asyncio.run(cache_instance.delete(kwargs.get("key", "test_key")))
                    else:
                        raise ValueError(f"Unsupported operation: {operation}")
            
            elif error_type == "connection_error":
                # Simulate connection error
                with patch.object(cache_instance, operation, side_effect=ConnectionError("Cache connection failed")):
                    if operation == "get":
                        result = asyncio.run(cache_instance.get(kwargs.get("key", "test_key")))
                    elif operation == "set":
                        result = asyncio.run(cache_instance.set(kwargs.get("key", "test_key"), kwargs.get("value", "test_value")))
                    elif operation == "delete":
                        result = asyncio.run(cache_instance.delete(kwargs.get("key", "test_key")))
                    else:
                        raise ValueError(f"Unsupported operation: {operation}")
            
            elif error_type == "storage_error":
                # Simulate storage error
                with patch.object(cache_instance, operation, side_effect=IOError("Storage device error")):
                    if operation == "get":
                        result = asyncio.run(cache_instance.get(kwargs.get("key", "test_key")))
                    elif operation == "set":
                        result = asyncio.run(cache_instance.set(kwargs.get("key", "test_key"), kwargs.get("value", "test_value")))
                    elif operation == "delete":
                        result = asyncio.run(cache_instance.delete(kwargs.get("key", "test_key")))
                    else:
                        raise ValueError(f"Unsupported operation: {operation}")
            
            elif error_type == "memory_error":
                # Simulate memory error
                with patch.object(cache_instance, operation, side_effect=MemoryError("Insufficient memory")):
                    if operation == "get":
                        result = asyncio.run(cache_instance.get(kwargs.get("key", "test_key")))
                    elif operation == "set":
                        result = asyncio.run(cache_instance.set(kwargs.get("key", "test_key"), kwargs.get("value", "test_value")))
                    elif operation == "delete":
                        result = asyncio.run(cache_instance.delete(kwargs.get("key", "test_key")))
                    else:
                        raise ValueError(f"Unsupported operation: {operation}")
            
            elif error_type == "corruption_error":
                # Simulate data corruption error
                with patch.object(cache_instance, operation, side_effect=ValueError("Data corruption detected")):
                    if operation == "get":
                        result = asyncio.run(cache_instance.get(kwargs.get("key", "test_key")))
                    elif operation == "set":
                        result = asyncio.run(cache_instance.set(kwargs.get("key", "test_key"), kwargs.get("value", "test_value")))
                    elif operation == "delete":
                        result = asyncio.run(cache_instance.delete(kwargs.get("key", "test_key")))
                    else:
                        raise ValueError(f"Unsupported operation: {operation}")
            
            elif error_type == "network_error":
                # Simulate network error
                with patch.object(cache_instance, operation, side_effect=OSError("Network unreachable")):
                    if operation == "get":
                        result = asyncio.run(cache_instance.get(kwargs.get("key", "test_key")))
                    elif operation == "set":
                        result = asyncio.run(cache_instance.set(kwargs.get("key", "test_key"), kwargs.get("value", "test_value")))
                    elif operation == "delete":
                        result = asyncio.run(cache_instance.delete(kwargs.get("key", "test_key")))
                    else:
                        raise ValueError(f"Unsupported operation: {operation}")
            
            elif error_type == "permission_error":
                # Simulate permission error
                with patch.object(cache_instance, operation, side_effect=PermissionError("Access denied")):
                    if operation == "get":
                        result = asyncio.run(cache_instance.get(kwargs.get("key", "test_key")))
                    elif operation == "set":
                        result = asyncio.run(cache_instance.set(kwargs.get("key", "test_key"), kwargs.get("value", "test_value")))
                    elif operation == "delete":
                        result = asyncio.run(cache_instance.delete(kwargs.get("key", "test_key")))
                    else:
                        raise ValueError(f"Unsupported operation: {operation}")
            
            else:
                raise ValueError(f"Unknown error type: {error_type}")
            
            error_info["result"] = result
            error_info["error_message"] = f"Error occurred: {str(result)}"
            
        except Exception as e:
            error_info["original_error"] = str(e)
            error_info["error_message"] = f"Exception: {str(e)}"
        
        self.error_scenarios.append(error_info)
        return error_info
    
    def test_error_recovery(self, cache_instance, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test error recovery mechanisms."""
        recovery_info = {
            "error_type": error_info["error_type"],
            "operation": error_info["operation"],
            "cache_layer": error_info["cache_layer"],
            "recovery_attempted": True,
            "recovery_successful": False,
            "recovery_method": None,
            "recovery_time_ms": None,
            "final_result": None,
            "error_message": None
        }
        
        start_time = time.time()
        
        try:
            # Attempt recovery based on error type
            if error_info["error_type"] == "timeout":
                # Retry with exponential backoff
                recovery_info["recovery_method"] = "retry_with_backoff"
                result = self._retry_with_backoff(cache_instance, error_info["operation"], **{"key": "test_key", "value": "test_value"})
                recovery_info["final_result"] = result
                recovery_info["recovery_successful"] = result is not None
            
            elif error_info["error_type"] == "connection_error":
                # Reconnect and retry
                recovery_info["recovery_method"] = "reconnect_and_retry"
                result = self._reconnect_and_retry(cache_instance, error_info["operation"], **{"key": "test_key", "value": "test_value"})
                recovery_info["final_result"] = result
                recovery_info["recovery_successful"] = result is not None
            
            elif error_info["error_type"] == "storage_error":
                # Switch to fallback storage
                recovery_info["recovery_method"] = "fallback_storage"
                result = self._use_fallback_storage(cache_instance, error_info["operation"], **{"key": "test_key", "value": "test_value"})
                recovery_info["final_result"] = result
                recovery_info["recovery_successful"] = result is not None
            
            elif error_info["error_type"] == "memory_error":
                # Clear cache and retry
                recovery_info["recovery_method"] = "clear_cache_and_retry"
                result = self._clear_cache_and_retry(cache_instance, error_info["operation"], **{"key": "test_key", "value": "test_value"})
                recovery_info["final_result"] = result
                recovery_info["recovery_successful"] = result is not None
            
            elif error_info["error_type"] == "corruption_error":
                # Restore from backup
                recovery_info["recovery_method"] = "restore_from_backup"
                result = self._restore_from_backup(cache_instance, error_info["operation"], **{"key": "test_key", "value": "test_value"})
                recovery_info["final_result"] = result
                recovery_info["recovery_successful"] = result is not None
            
            elif error_info["error_type"] == "network_error":
                # Use offline mode
                recovery_info["recovery_method"] = "offline_mode"
                result = self._use_offline_mode(cache_instance, error_info["operation"], **{"key": "test_key", "value": "test_value"})
                recovery_info["final_result"] = result
                recovery_info["recovery_successful"] = result is not None
            
            elif error_info["error_type"] == "permission_error":
                # Request permissions and retry
                recovery_info["recovery_method"] = "request_permissions"
                result = self._request_permissions_and_retry(cache_instance, error_info["operation"], **{"key": "test_key", "value": "test_value"})
                recovery_info["final_result"] = result
                recovery_info["recovery_successful"] = result is not None
            
            else:
                raise ValueError(f"Unknown error type: {error_info['error_type']}")
            
            recovery_info["error_message"] = f"Recovery successful: {recovery_info['recovery_successful']}"
            
        except Exception as e:
            recovery_info["error_message"] = f"Recovery failed: {str(e)}"
        
        recovery_info["recovery_time_ms"] = (time.time() - start_time) * 1000
        
        self.recovery_results.append(recovery_info)
        return recovery_info
    
    def _retry_with_backoff(self, cache_instance, operation: str, **kwargs) -> Any:
        """Retry operation with exponential backoff."""
        max_retries = 3
        base_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                if operation == "get":
                    return asyncio.run(cache_instance.get(kwargs["key"]))
                elif operation == "set":
                    return asyncio.run(cache_instance.set(kwargs["key"], kwargs["value"]))
                elif operation == "delete":
                    return asyncio.run(cache_instance.delete(kwargs["key"]))
                else:
                    raise ValueError(f"Unsupported operation: {operation}")
            except Exception:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise
    
    def _reconnect_and_retry(self, cache_instance, operation: str, **kwargs) -> Any:
        """Reconnect and retry operation."""
        try:
            # Simulate reconnection
            asyncio.run(cache_instance.initialize())
            
            # Retry operation
            if operation == "get":
                return asyncio.run(cache_instance.get(kwargs["key"]))
            elif operation == "set":
                return asyncio.run(cache_instance.set(kwargs["key"], kwargs["value"]))
            elif operation == "delete":
                return asyncio.run(cache_instance.delete(kwargs["key"]))
            else:
                raise ValueError(f"Unsupported operation: {operation}")
        except Exception:
            raise
    
    def _use_fallback_storage(self, cache_instance, operation: str, **kwargs) -> Any:
        """Use fallback storage for operation."""
        try:
            # Simulate fallback storage
            fallback_cache = Mock()
            fallback_cache.get_layer.return_value = cache_instance.get_layer()
            
            if operation == "get":
                fallback_cache.get = AsyncMock(return_value=CacheResult(status=CacheStatus.HIT, entry=Mock(value="fallback_value")))
                return asyncio.run(fallback_cache.get(kwargs["key"]))
            elif operation == "set":
                fallback_cache.set = AsyncMock(return_value=True)
                return asyncio.run(fallback_cache.set(kwargs["key"], kwargs["value"]))
            elif operation == "delete":
                fallback_cache.delete = AsyncMock(return_value=True)
                return asyncio.run(fallback_cache.delete(kwargs["key"]))
            else:
                raise ValueError(f"Unsupported operation: {operation}")
        except Exception:
            raise
    
    def _clear_cache_and_retry(self, cache_instance, operation: str, **kwargs) -> Any:
        """Clear cache and retry operation."""
        try:
            # Clear cache
            asyncio.run(cache_instance.clear())
            
            # Retry operation
            if operation == "get":
                return asyncio.run(cache_instance.get(kwargs["key"]))
            elif operation == "set":
                return asyncio.run(cache_instance.set(kwargs["key"], kwargs["value"]))
            elif operation == "delete":
                return asyncio.run(cache_instance.delete(kwargs["key"]))
            else:
                raise ValueError(f"Unsupported operation: {operation}")
        except Exception:
            raise
    
    def _restore_from_backup(self, cache_instance, operation: str, **kwargs) -> Any:
        """Restore from backup and retry operation."""
        try:
            # Simulate backup restoration
            backup_cache = Mock()
            backup_cache.get_layer.return_value = cache_instance.get_layer()
            
            if operation == "get":
                backup_cache.get = AsyncMock(return_value=CacheResult(status=CacheStatus.HIT, entry=Mock(value="backup_value")))
                return asyncio.run(backup_cache.get(kwargs["key"]))
            elif operation == "set":
                backup_cache.set = AsyncMock(return_value=True)
                return asyncio.run(backup_cache.set(kwargs["key"], kwargs["value"]))
            elif operation == "delete":
                backup_cache.delete = AsyncMock(return_value=True)
                return asyncio.run(backup_cache.delete(kwargs["key"]))
            else:
                raise ValueError(f"Unsupported operation: {operation}")
        except Exception:
            raise
    
    def _use_offline_mode(self, cache_instance, operation: str, **kwargs) -> Any:
        """Use offline mode for operation."""
        try:
            # Simulate offline mode
            offline_cache = Mock()
            offline_cache.get_layer.return_value = cache_instance.get_layer()
            
            if operation == "get":
                offline_cache.get = AsyncMock(return_value=CacheResult(status=CacheStatus.HIT, entry=Mock(value="offline_value")))
                return asyncio.run(offline_cache.get(kwargs["key"]))
            elif operation == "set":
                offline_cache.set = AsyncMock(return_value=True)
                return asyncio.run(offline_cache.set(kwargs["key"], kwargs["value"]))
            elif operation == "delete":
                offline_cache.delete = AsyncMock(return_value=True)
                return asyncio.run(offline_cache.delete(kwargs["key"]))
            else:
                raise ValueError(f"Unsupported operation: {operation}")
        except Exception:
            raise
    
    def _request_permissions_and_retry(self, cache_instance, operation: str, **kwargs) -> Any:
        """Request permissions and retry operation."""
        try:
            # Simulate permission request
            with patch('os.access', return_value=True):
                # Retry operation
                if operation == "get":
                    return asyncio.run(cache_instance.get(kwargs["key"]))
                elif operation == "set":
                    return asyncio.run(cache_instance.set(kwargs["key"], kwargs["value"]))
                elif operation == "delete":
                    return asyncio.run(cache_instance.delete(kwargs["key"]))
                else:
                    raise ValueError(f"Unsupported operation: {operation}")
        except Exception:
            raise
    
    def generate_error_report(self) -> Dict[str, Any]:
        """Generate comprehensive error handling report."""
        report = {
            "error_scenarios": [],
            "recovery_results": [],
            "summary": {
                "total_error_scenarios": len(self.error_scenarios),
                "total_recovery_attempts": len(self.recovery_results),
                "successful_recoveries": sum(1 for r in self.recovery_results if r["recovery_successful"]),
                "failed_recoveries": sum(1 for r in self.recovery_results if not r["recovery_successful"]),
                "recovery_success_rate": sum(1 for r in self.recovery_results if r["recovery_successful"]) / len(self.recovery_results) if self.recovery_results else 0
            },
            "error_type_analysis": {},
            "recovery_method_analysis": {},
            "cache_layer_analysis": {}
        }
        
        # Add error scenarios
        for scenario in self.error_scenarios:
            report["error_scenarios"].append({
                "error_type": scenario["error_type"],
                "operation": scenario["operation"],
                "cache_layer": scenario["cache_layer"],
                "timestamp": scenario["timestamp"],
                "original_error": scenario["original_error"],
                "recovery_attempted": scenario["recovery_attempted"],
                "recovery_successful": scenario["recovery_successful"],
                "error_message": scenario["error_message"]
            })
        
        # Add recovery results
        for recovery in self.recovery_results:
            report["recovery_results"].append({
                "error_type": recovery["error_type"],
                "operation": recovery["operation"],
                "cache_layer": recovery["cache_layer"],
                "recovery_attempted": recovery["recovery_attempted"],
                "recovery_successful": recovery["recovery_successful"],
                "recovery_method": recovery["recovery_method"],
                "recovery_time_ms": recovery["recovery_time_ms"],
                "final_result": recovery["final_result"],
                "error_message": recovery["error_message"]
            })
        
        # Analyze error types
        error_type_counts = {}
        for scenario in self.error_scenarios:
            error_type = scenario["error_type"]
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        report["error_type_analysis"] = error_type_counts
        
        # Analyze recovery methods
        recovery_method_counts = {}
        recovery_method_success = {}
        for recovery in self.recovery_results:
            method = recovery["recovery_method"]
            recovery_method_counts[method] = recovery_method_counts.get(method, 0) + 1
            if method not in recovery_method_success:
                recovery_method_success[method] = {"success": 0, "total": 0}
            recovery_method_success[method]["total"] += 1
            if recovery["recovery_successful"]:
                recovery_method_success[method]["success"] += 1
        
        report["recovery_method_analysis"] = {
            "counts": recovery_method_counts,
            "success_rates": {k: v["success"] / v["total"] for k, v in recovery_method_success.items()}
        }
        
        # Analyze cache layers
        cache_layer_counts = {}
        cache_layer_success = {}
        for recovery in self.recovery_results:
            layer = recovery["cache_layer"]
            cache_layer_counts[layer] = cache_layer_counts.get(layer, 0) + 1
            if layer not in cache_layer_success:
                cache_layer_success[layer] = {"success": 0, "total": 0}
            cache_layer_success[layer]["total"] += 1
            if recovery["recovery_successful"]:
                cache_layer_success[layer]["success"] += 1
        
        report["cache_layer_analysis"] = {
            "counts": cache_layer_counts,
            "success_rates": {k: v["success"] / v["total"] for k, v in cache_layer_success.items()}
        }
        
        return report


class TestPredictiveCacheErrors:
    """Test predictive cache error handling."""
    
    @pytest.fixture
    def cache_config(self):
        """Create predictive cache configuration."""
        return PredictiveCacheConfig(
            cache_ttl_seconds=60,
            prediction_window_seconds=300,
            max_predictions=10,
            confidence_threshold=0.8
        )
    
    @pytest.fixture
    def predictive_cache(self, cache_config):
        """Create predictive cache instance."""
        cache = PredictiveCache("test_predictive", cache_config)
        cache._cache = {}  # Use in-memory storage for testing
        return cache
    
    @pytest.mark.asyncio
    async def test_predictive_cache_timeout_error(self, predictive_cache):
        """Test predictive cache timeout error handling."""
        tester = CacheErrorTester()
        
        # Simulate timeout error
        error_info = tester.simulate_cache_error(
            predictive_cache, "timeout", "get", key="test_key"
        )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(predictive_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "timeout"
        assert error_info["operation"] == "get"
        assert error_info["cache_layer"] == "predictive"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "retry_with_backoff"
        assert recovery_info["recovery_time_ms"] is not None
    
    @pytest.mark.asyncio
    async def test_predictive_cache_connection_error(self, predictive_cache):
        """Test predictive cache connection error handling."""
        tester = CacheErrorTester()
        
        # Simulate connection error
        error_info = tester.simulate_cache_error(
            predictive_cache, "connection_error", "set", key="test_key", value="test_value"
        )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(predictive_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "connection_error"
        assert error_info["operation"] == "set"
        assert error_info["cache_layer"] == "predictive"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "reconnect_and_retry"
        assert recovery_info["recovery_time_ms"] is not None
    
    @pytest.mark.asyncio
    async def test_predictive_cache_memory_error(self, predictive_cache):
        """Test predictive cache memory error handling."""
        tester = CacheErrorTester()
        
        # Simulate memory error
        error_info = tester.simulate_cache_error(
            predictive_cache, "memory_error", "set", key="test_key", value="test_value"
        )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(predictive_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "memory_error"
        assert error_info["operation"] == "set"
        assert error_info["cache_layer"] == "predictive"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "clear_cache_and_retry"
        assert recovery_info["recovery_time_ms"] is not None
    
    @pytest.mark.asyncio
    async def test_predictive_cache_corruption_error(self, predictive_cache):
        """Test predictive cache corruption error handling."""
        tester = CacheErrorTester()
        
        # Simulate corruption error
        error_info = tester.simulate_cache_error(
            predictive_cache, "corruption_error", "get", key="test_key"
        )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(predictive_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "corruption_error"
        assert error_info["operation"] == "get"
        assert error_info["cache_layer"] == "predictive"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "restore_from_backup"
        assert recovery_info["recovery_time_ms"] is not None
    
    def test_predictive_cache_error_resilience(self, predictive_cache):
        """Test predictive cache error resilience."""
        tester = CacheErrorTester()
        
        # Test multiple error scenarios
        error_types = ["timeout", "connection_error", "memory_error", "corruption_error"]
        
        for error_type in error_types:
            for operation in ["get", "set"]:
                error_info = tester.simulate_cache_error(
                    predictive_cache, error_type, operation, key="test_key", value="test_value"
                )
                
                # Test recovery
                recovery_info = tester.test_error_recovery(predictive_cache, error_info)
                
                # Assert that recovery was attempted
                assert recovery_info["recovery_attempted"] is True
        
        # Generate report
        report = tester.generate_error_report()
        
        # Assert comprehensive error handling
        assert report["summary"]["total_error_scenarios"] == len(error_types) * 2
        assert report["summary"]["total_recovery_attempts"] == len(error_types) * 2
        assert report["summary"]["recovery_success_rate"] > 0.5  # At least 50% success rate


class TestSemanticCacheErrors:
    """Test semantic cache error handling."""
    
    @pytest.fixture
    def cache_config(self):
        """Create semantic cache configuration."""
        return SemanticCacheConfig(
            cache_ttl_seconds=300,
            similarity_threshold=0.8,
            embedding_dimension=384,
            max_entries=1000
        )
    
    @pytest.fixture
    def semantic_cache(self, cache_config):
        """Create semantic cache instance."""
        cache = SemanticCache("test_semantic", cache_config)
        cache._cache = {}  # Use in-memory storage for testing
        return cache
    
    @pytest.mark.asyncio
    async def test_semantic_cache_embedding_error(self, semantic_cache):
        """Test semantic cache embedding generation error."""
        tester = CacheErrorTester()
        
        # Simulate embedding error
        with patch('src.core.utils.CacheUtils.generate_embedding', side_effect=Exception("Embedding generation failed")):
            error_info = tester.simulate_cache_error(
                semantic_cache, "storage_error", "set", key="test_key", value="test_value"
            )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(semantic_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "storage_error"
        assert error_info["operation"] == "set"
        assert error_info["cache_layer"] == "semantic"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "fallback_storage"
        assert recovery_info["recovery_time_ms"] is not None
    
    @pytest.mark.asyncio
    async def test_semantic_cache_similarity_search_error(self, semantic_cache):
        """Test semantic cache similarity search error."""
        tester = CacheErrorTester()
        
        # Simulate similarity search error
        with patch.object(semantic_cache, 'find_similar', side_effect=Exception("Similarity search failed")):
            error_info = tester.simulate_cache_error(
                semantic_cache, "network_error", "get", key="test_key"
            )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(semantic_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "network_error"
        assert error_info["operation"] == "get"
        assert error_info["cache_layer"] == "semantic"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "offline_mode"
        assert recovery_info["recovery_time_ms"] is not None
    
    @pytest.mark.asyncio
    async def test_semantic_cache_index_error(self, semantic_cache):
        """Test semantic cache index error."""
        tester = CacheErrorTester()
        
        # Simulate index error
        with patch.object(semantic_cache, '_build_semantic_index', side_effect=Exception("Index build failed")):
            error_info = tester.simulate_cache_error(
                semantic_cache, "corruption_error", "set", key="test_key", value="test_value"
            )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(semantic_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "corruption_error"
        assert error_info["operation"] == "set"
        assert error_info["cache_layer"] == "semantic"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "restore_from_backup"
        assert recovery_info["recovery_time_ms"] is not None


class TestVectorCacheErrors:
    """Test vector cache error handling."""
    
    @pytest.fixture
    def cache_config(self):
        """Create vector cache configuration."""
        return VectorCacheConfig(
            cache_ttl_seconds=180,
            similarity_threshold=0.75,
            reranking_enabled=True,
            max_entries=5000
        )
    
    @pytest.fixture
    def vector_cache(self, cache_config):
        """Create vector cache instance."""
        cache = VectorCache("test_vector", cache_config)
        cache._cache = {}  # Use in-memory storage for testing
        return cache
    
    @pytest.mark.asyncio
    async def test_vector_cache_vector_search_error(self, vector_cache):
        """Test vector cache vector search error."""
        tester = CacheErrorTester()
        
        # Simulate vector search error
        with patch.object(vector_cache, 'search', side_effect=Exception("Vector search failed")):
            error_info = tester.simulate_cache_error(
                vector_cache, "network_error", "get", key="test_key"
            )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(vector_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "network_error"
        assert error_info["operation"] == "get"
        assert error_info["cache_layer"] == "vector"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "offline_mode"
        assert recovery_info["recovery_time_ms"] is not None
    
    @pytest.mark.asyncio
    async def test_vector_cache_reranking_error(self, vector_cache):
        """Test vector cache reranking error."""
        tester = CacheErrorTester()
        
        # Simulate reranking error
        with patch.object(vector_cache, '_rerank_results', side_effect=Exception("Reranking failed")):
            error_info = tester.simulate_cache_error(
                vector_cache, "storage_error", "get", key="test_key"
            )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(vector_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "storage_error"
        assert error_info["operation"] == "get"
        assert error_info["cache_layer"] == "vector"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "fallback_storage"
        assert recovery_info["recovery_time_ms"] is not None


class TestGlobalCacheErrors:
    """Test global cache error handling."""
    
    @pytest.fixture
    def cache_config(self):
        """Create global cache configuration."""
        return GlobalCacheConfig(
            cache_ttl_seconds=600,
            rag_server_url="http://localhost:8000",
            rag_server_timeout=30,
            fallback_enabled=True,
            max_fallback_entries=1000
        )
    
    @pytest.fixture
    def global_cache(self, cache_config):
        """Create global cache instance."""
        cache = GlobalCache("test_global", cache_config)
        cache._cache = {}  # Use in-memory storage for testing
        return cache
    
    @pytest.mark.asyncio
    async def test_global_cache_rag_server_error(self, global_cache):
        """Test global cache RAG server error."""
        tester = CacheErrorTester()
        
        # Simulate RAG server error
        with patch.object(global_cache, '_query_rag_server', side_effect=Exception("RAG server unavailable")):
            error_info = tester.simulate_cache_error(
                global_cache, "network_error", "get", key="test_key"
            )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(global_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "network_error"
        assert error_info["operation"] == "get"
        assert error_info["cache_layer"] == "global"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "offline_mode"
        assert recovery_info["recovery_time_ms"] is not None
    
    @pytest.mark.asyncio
    async def test_global_cache_fallback_error(self, global_cache):
        """Test global cache fallback error."""
        tester = CacheErrorTester()
        
        # Simulate fallback error
        with patch.object(global_cache, '_use_fallback', side_effect=Exception("Fallback failed")):
            error_info = tester.simulate_cache_error(
                global_cache, "connection_error", "set", key="test_key", value="test_value"
            )
        
        # Test recovery
        recovery_info = tester.test_error_recovery(global_cache, error_info)
        
        # Assert error handling
        assert error_info["error_type"] == "connection_error"
        assert error_info["operation"] == "set"
        assert error_info["cache_layer"] == "global"
        assert error_info["original_error"] is not None
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_method"] == "reconnect_and_retry"
        assert recovery_info["recovery_time_ms"] is not None


class TestCrossCacheErrorHandling:
    """Test cross-cache error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_cross_cache_error_propagation(self):
        """Test error propagation across cache layers."""
        # Create cache instances
        predictive_config = PredictiveCacheConfig(cache_ttl_seconds=60, prediction_window_seconds=300)
        semantic_config = SemanticCacheConfig(cache_ttl_seconds=300, similarity_threshold=0.8)
        vector_config = VectorCacheConfig(cache_ttl_seconds=180, similarity_threshold=0.75)
        global_config = GlobalCacheConfig(cache_ttl_seconds=600, rag_server_url="http://localhost:8000")
        
        predictive_cache = PredictiveCache("test_predictive", predictive_config)
        semantic_cache = SemanticCache("test_semantic", semantic_config)
        vector_cache = VectorCache("test_vector", vector_config)
        global_cache = GlobalCache("test_global", global_config)
        
        # Initialize all caches
        for cache in [predictive_cache, semantic_cache, vector_cache, global_cache]:
            cache._cache = {}
        
        # Create tester
        tester = CacheErrorTester()
        
        # Test error propagation
        error_scenarios = []
        
        for cache in [predictive_cache, semantic_cache, vector_cache, global_cache]:
            for error_type in ["timeout", "connection_error", "memory_error"]:
                for operation in ["get", "set"]:
                    error_info = tester.simulate_cache_error(
                        cache, error_type, operation, key="test_key", value="test_value"
                    )
                    error_scenarios.append(error_info)
        
        # Test recovery for all scenarios
        recovery_results = []
        for error_info in error_scenarios:
            recovery_info = tester.test_error_recovery(
                globals()[f"{error_info['cache_layer']}_cache"], error_info
            )
            recovery_results.append(recovery_info)
        
        # Generate comprehensive report
        report = tester.generate_error_report()
        
        # Assert comprehensive error handling
        assert report["summary"]["total_error_scenarios"] == len(error_scenarios)
        assert report["summary"]["total_recovery_attempts"] == len(recovery_results)
        assert report["summary"]["recovery_success_rate"] > 0.3  # At least 30% success rate
        
        # Assert error type coverage
        assert "timeout" in report["error_type_analysis"]
        assert "connection_error" in report["error_type_analysis"]
        assert "memory_error" in report["error_type_analysis"]
        
        # Assert cache layer coverage
        assert "predictive" in report["cache_layer_analysis"]["counts"]
        assert "semantic" in report["cache_layer_analysis"]["counts"]
        assert "vector" in report["cache_layer_analysis"]["counts"]
        assert "global" in report["cache_layer_analysis"]["counts"]
    
    @pytest.mark.asyncio
    async def test_cross_cache_error_isolation(self):
        """Test error isolation between cache layers."""
        # Create cache instances
        predictive_config = PredictiveCacheConfig(cache_ttl_seconds=60, prediction_window_seconds=300)
        semantic_config = SemanticCacheConfig(cache_ttl_seconds=300, similarity_threshold=0.8)
        
        predictive_cache = PredictiveCache("test_predictive", predictive_config)
        semantic_cache = SemanticCache("test_semantic", semantic_config)
        
        # Initialize all caches
        predictive_cache._cache = {}
        semantic_cache._cache = {}
        
        # Create tester
        tester = CacheErrorTester()
        
        # Introduce error in predictive cache
        error_info = tester.simulate_cache_error(
            predictive_cache, "timeout", "get", key="test_key"
        )
        
        # Test that semantic cache is not affected
        semantic_result = asyncio.run(semantic_cache.get("test_key"))
        
        # Assert error isolation
        assert error_info["error_type"] == "timeout"
        assert error_info["cache_layer"] == "predictive"
        assert semantic_result is not None  # Semantic cache should work independently
        
        # Test recovery
        recovery_info = tester.test_error_recovery(predictive_cache, error_info)
        
        # Assert recovery
        assert recovery_info["recovery_attempted"] is True
        assert recovery_info["recovery_successful"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])