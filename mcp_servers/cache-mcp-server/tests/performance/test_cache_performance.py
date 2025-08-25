"""
Performance Tests for Cache Operations.

This module contains comprehensive performance tests for cache operations,
testing response times, throughput, memory usage, and CPU utilization.
"""

import pytest
import asyncio
import time
import statistics
import psutil
import threading
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.core.base_cache import CacheLayer, CacheStatus
from src.cache_layers.predictive_cache import PredictiveCache
from src.cache_layers.semantic_cache import SemanticCache
from src.cache_layers.vector_cache import VectorCache
from src.cache_layers.global_cache import GlobalCache
from src.cache_layers.vector_diary import VectorDiary
from src.core.config import PredictiveCacheConfig, SemanticCacheConfig, VectorCacheConfig, GlobalCacheConfig, VectorDiaryConfig


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    operation: str
    cache_layer: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    total_time_seconds: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p90_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    throughput_ops_per_sec: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate: float


class CachePerformanceTester:
    """Main class for testing cache performance."""
    
    def __init__(self):
        self.metrics = []
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.initial_cpu = psutil.cpu_percent()
    
    def measure_performance(self, operation_func, *args, **kwargs) -> PerformanceMetrics:
        """Measure performance of an operation."""
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024
        start_cpu = psutil.cpu_percent()
        
        try:
            result = operation_func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024
        end_cpu = psutil.cpu_percent()
        
        response_time = (end_time - start_time) * 1000  # ms
        memory_usage = end_memory - start_memory
        cpu_usage = end_cpu - start_cpu
        
        return {
            "response_time_ms": response_time,
            "success": success,
            "memory_usage_mb": memory_usage,
            "cpu_usage_percent": cpu_usage,
            "error": error if not success else None
        }
    
    async def measure_async_performance(self, operation_func, *args, **kwargs) -> Dict[str, Any]:
        """Measure performance of an async operation."""
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024
        start_cpu = psutil.cpu_percent()
        
        try:
            result = await operation_func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024
        end_cpu = psutil.cpu_percent()
        
        response_time = (end_time - start_time) * 1000  # ms
        memory_usage = end_memory - start_memory
        cpu_usage = end_cpu - start_cpu
        
        return {
            "response_time_ms": response_time,
            "success": success,
            "memory_usage_mb": memory_usage,
            "cpu_usage_percent": cpu_usage,
            "error": error if not success else None
        }
    
    def run_performance_test(self, cache_instance, operation: str, 
                           test_data: List[Any], iterations: int = 100) -> PerformanceMetrics:
        """Run a comprehensive performance test."""
        print(f"Running {operation} performance test...")
        
        response_times = []
        successes = 0
        failures = 0
        memory_usage = []
        cpu_usage = []
        
        for i in range(iterations):
            # Prepare test data
            if operation == "get":
                key = test_data[i % len(test_data)]
                metrics = self.measure_performance(
                    cache_instance.get, key
                )
            elif operation == "set":
                key = f"test_key_{i}"
                value = test_data[i % len(test_data)]
                metrics = self.measure_performance(
                    cache_instance.set, key, value
                )
            elif operation == "delete":
                key = test_data[i % len(test_data)]
                metrics = self.measure_performance(
                    cache_instance.delete, key
                )
            elif operation == "exists":
                key = test_data[i % len(test_data)]
                metrics = self.measure_performance(
                    cache_instance.exists, key
                )
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            response_times.append(metrics["response_time_ms"])
            memory_usage.append(metrics["memory_usage_mb"])
            cpu_usage.append(metrics["cpu_usage_percent"])
            
            if metrics["success"]:
                successes += 1
            else:
                failures += 1
        
        # Calculate statistics
        total_time = sum(response_times) / 1000  # Convert to seconds
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.5)]
        p90 = sorted_times[int(len(sorted_times) * 0.9)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Calculate throughput
        throughput = iterations / total_time if total_time > 0 else 0
        
        # Calculate error rate
        error_rate = failures / iterations if iterations > 0 else 0
        
        # Calculate average memory and CPU usage
        avg_memory = statistics.mean(memory_usage)
        avg_cpu = statistics.mean(cpu_usage)
        
        # Create metrics object
        metrics = PerformanceMetrics(
            operation=operation,
            cache_layer=cache_instance.get_layer().value,
            total_operations=iterations,
            successful_operations=successes,
            failed_operations=failures,
            total_time_seconds=total_time,
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p50_response_time_ms=p50,
            p90_response_time_ms=p90,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            throughput_ops_per_sec=throughput,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            error_rate=error_rate
        )
        
        self.metrics.append(metrics)
        return metrics
    
    async def run_async_performance_test(self, cache_instance, operation: str,
                                       test_data: List[Any], iterations: int = 100) -> PerformanceMetrics:
        """Run a comprehensive async performance test."""
        print(f"Running async {operation} performance test...")
        
        response_times = []
        successes = 0
        failures = 0
        memory_usage = []
        cpu_usage = []
        
        for i in range(iterations):
            # Prepare test data
            if operation == "get":
                key = test_data[i % len(test_data)]
                metrics = await self.measure_async_performance(
                    cache_instance.get, key
                )
            elif operation == "set":
                key = f"test_key_{i}"
                value = test_data[i % len(test_data)]
                metrics = await self.measure_async_performance(
                    cache_instance.set, key, value
                )
            elif operation == "delete":
                key = test_data[i % len(test_data)]
                metrics = await self.measure_async_performance(
                    cache_instance.delete, key
                )
            elif operation == "exists":
                key = test_data[i % len(test_data)]
                metrics = await self.measure_async_performance(
                    cache_instance.exists, key
                )
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            response_times.append(metrics["response_time_ms"])
            memory_usage.append(metrics["memory_usage_mb"])
            cpu_usage.append(metrics["cpu_usage_percent"])
            
            if metrics["success"]:
                successes += 1
            else:
                failures += 1
        
        # Calculate statistics
        total_time = sum(response_times) / 1000  # Convert to seconds
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.5)]
        p90 = sorted_times[int(len(sorted_times) * 0.9)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Calculate throughput
        throughput = iterations / total_time if total_time > 0 else 0
        
        # Calculate error rate
        error_rate = failures / iterations if iterations > 0 else 0
        
        # Calculate average memory and CPU usage
        avg_memory = statistics.mean(memory_usage)
        avg_cpu = statistics.mean(cpu_usage)
        
        # Create metrics object
        metrics = PerformanceMetrics(
            operation=operation,
            cache_layer=cache_instance.get_layer().value,
            total_operations=iterations,
            successful_operations=successes,
            failed_operations=failures,
            total_time_seconds=total_time,
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p50_response_time_ms=p50,
            p90_response_time_ms=p90,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            throughput_ops_per_sec=throughput,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            error_rate=error_rate
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def run_concurrent_performance_test(self, cache_instance, operation: str,
                                      test_data: List[Any], concurrent_users: int = 10,
                                      operations_per_user: int = 10) -> PerformanceMetrics:
        """Run a concurrent performance test."""
        print(f"Running concurrent {operation} performance test with {concurrent_users} users...")
        
        response_times = []
        successes = 0
        failures = 0
        memory_usage = []
        cpu_usage = []
        
        def worker(user_id: int):
            nonlocal successes, failures
            user_times = []
            user_memory = []
            user_cpu = []
            
            for i in range(operations_per_user):
                if operation == "get":
                    key = test_data[(user_id * operations_per_user + i) % len(test_data)]
                    metrics = self.measure_performance(
                        cache_instance.get, key
                    )
                elif operation == "set":
                    key = f"test_key_{user_id}_{i}"
                    value = test_data[(user_id * operations_per_user + i) % len(test_data)]
                    metrics = self.measure_performance(
                        cache_instance.set, key, value
                    )
                elif operation == "delete":
                    key = test_data[(user_id * operations_per_user + i) % len(test_data)]
                    metrics = self.measure_performance(
                        cache_instance.delete, key
                    )
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                user_times.append(metrics["response_time_ms"])
                user_memory.append(metrics["memory_usage_mb"])
                user_cpu.append(metrics["cpu_usage_percent"])
                
                if metrics["success"]:
                    successes += 1
                else:
                    failures += 1
            
            return user_times, user_memory, user_cpu
        
        # Run concurrent workers
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(worker, i) for i in range(concurrent_users)]
            
            for future in as_completed(futures):
                user_times, user_memory, user_cpu = future.result()
                response_times.extend(user_times)
                memory_usage.extend(user_memory)
                cpu_usage.extend(user_cpu)
        
        # Calculate statistics
        total_time = max(response_times) / 1000 if response_times else 0
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.5)]
        p90 = sorted_times[int(len(sorted_times) * 0.9)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Calculate throughput
        total_operations = concurrent_users * operations_per_user
        throughput = total_operations / total_time if total_time > 0 else 0
        
        # Calculate error rate
        error_rate = failures / total_operations if total_operations > 0 else 0
        
        # Calculate average memory and CPU usage
        avg_memory = statistics.mean(memory_usage)
        avg_cpu = statistics.mean(cpu_usage)
        
        # Create metrics object
        metrics = PerformanceMetrics(
            operation=f"concurrent_{operation}",
            cache_layer=cache_instance.get_layer().value,
            total_operations=total_operations,
            successful_operations=successes,
            failed_operations=failures,
            total_time_seconds=total_time,
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p50_response_time_ms=p50,
            p90_response_time_ms=p90,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            throughput_ops_per_sec=throughput,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            error_rate=error_rate
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        if not self.metrics:
            return {"error": "No performance metrics available"}
        
        report = {
            "test_summary": {
                "total_tests": len(self.metrics),
                "cache_layers": list(set(m.cache_layer for m in self.metrics)),
                "operations": list(set(m.operation for m in self.metrics))
            },
            "performance_metrics": [],
            "aggregated_metrics": {
                "avg_response_time_ms": statistics.mean([m.avg_response_time_ms for m in self.metrics]),
                "avg_throughput_ops_per_sec": statistics.mean([m.throughput_ops_per_sec for m in self.metrics]),
                "avg_memory_usage_mb": statistics.mean([m.memory_usage_mb for m in self.metrics]),
                "avg_cpu_usage_percent": statistics.mean([m.cpu_usage_percent for m in self.metrics]),
                "avg_error_rate": statistics.mean([m.error_rate for m in self.metrics])
            },
            "memory_usage": {
                "initial_memory_mb": self.initial_memory,
                "final_memory_mb": self.process.memory_info().rss / 1024 / 1024,
                "memory_growth_mb": self.process.memory_info().rss / 1024 / 1024 - self.initial_memory
            },
            "cpu_usage": {
                "initial_cpu_percent": self.initial_cpu,
                "final_cpu_percent": psutil.cpu_percent(),
                "avg_cpu_percent": statistics.mean([m.cpu_usage_percent for m in self.metrics])
            }
        }
        
        # Add individual metrics
        for metric in self.metrics:
            report["performance_metrics"].append({
                "operation": metric.operation,
                "cache_layer": metric.cache_layer,
                "total_operations": metric.total_operations,
                "successful_operations": metric.successful_operations,
                "failed_operations": metric.failed_operations,
                "total_time_seconds": metric.total_time_seconds,
                "avg_response_time_ms": metric.avg_response_time_ms,
                "min_response_time_ms": metric.min_response_time_ms,
                "max_response_time_ms": metric.max_response_time_ms,
                "p50_response_time_ms": metric.p50_response_time_ms,
                "p90_response_time_ms": metric.p90_response_time_ms,
                "p95_response_time_ms": metric.p95_response_time_ms,
                "p99_response_time_ms": metric.p99_response_time_ms,
                "throughput_ops_per_sec": metric.throughput_ops_per_sec,
                "memory_usage_mb": metric.memory_usage_mb,
                "cpu_usage_percent": metric.cpu_usage_percent,
                "error_rate": metric.error_rate
            })
        
        return report


class TestPredictiveCachePerformance:
    """Test predictive cache performance."""
    
    @pytest.fixture
    def cache_config(self):
        """Create predictive cache configuration."""
        return PredictiveCacheConfig(
            cache_ttl_seconds=60,
            max_cache_size=1000,
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
    async def test_predictive_cache_get_performance(self, predictive_cache):
        """Test predictive cache get operation performance."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_keys = [f"key_{i}" for i in range(100)]
        
        # Initialize cache with some data
        for key in test_keys[:50]:
            await predictive_cache.set(key, f"value_{key}")
        
        # Run performance test
        metrics = await tester.run_async_performance_test(
            predictive_cache, "get", test_keys, iterations=1000
        )
        
        # Assert performance requirements
        assert metrics.avg_response_time_ms < 10  # Should be fast
        assert metrics.throughput_ops_per_sec > 100  # Should handle high throughput
        assert metrics.error_rate < 0.01  # Should have low error rate
        assert metrics.memory_usage_mb < 10  # Should use reasonable memory
    
    @pytest.mark.asyncio
    async def test_predictive_cache_set_performance(self, predictive_cache):
        """Test predictive cache set operation performance."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_values = [f"value_{i}" for i in range(100)]
        
        # Run performance test
        metrics = await tester.run_async_performance_test(
            predictive_cache, "set", test_values, iterations=1000
        )
        
        # Assert performance requirements
        assert metrics.avg_response_time_ms < 15  # Should be fast
        assert metrics.throughput_ops_per_sec > 50  # Should handle good throughput
        assert metrics.error_rate < 0.01  # Should have low error rate
    
    @pytest.mark.asyncio
    async def test_predictive_cache_concurrent_get_performance(self, predictive_cache):
        """Test predictive cache concurrent get performance."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_keys = [f"key_{i}" for i in range(100)]
        
        # Initialize cache with some data
        for key in test_keys[:50]:
            await predictive_cache.set(key, f"value_{key}")
        
        # Run concurrent performance test
        metrics = tester.run_concurrent_performance_test(
            predictive_cache, "get", test_keys, concurrent_users=20, operations_per_user=50
        )
        
        # Assert performance requirements
        assert metrics.avg_response_time_ms < 20  # Should handle concurrent access well
        assert metrics.throughput_ops_per_sec > 200  # Should handle high concurrent throughput
        assert metrics.error_rate < 0.01  # Should have low error rate under load
    
    @pytest.mark.asyncio
    async def test_predictive_cache_memory_usage(self, predictive_cache):
        """Test predictive cache memory usage."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_keys = [f"key_{i}" for i in range(1000)]
        test_values = [f"value_{i}" for i in range(1000)]
        
        # Measure memory before
        initial_memory = tester.process.memory_info().rss / 1024 / 1024
        
        # Set many entries
        for key, value in zip(test_keys, test_values):
            await predictive_cache.set(key, value)
        
        # Measure memory after
        final_memory = tester.process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        # Assert memory usage is reasonable
        assert memory_growth < 100  # Should not grow too much
        
        # Test memory cleanup
        await predictive_cache.clear()
        
        # Measure memory after cleanup
        cleanup_memory = tester.process.memory_info().rss / 1024 / 1024
        cleanup_growth = cleanup_memory - initial_memory
        
        # Assert cleanup is effective
        assert cleanup_growth < 10  # Should clean up most memory


class TestSemanticCachePerformance:
    """Test semantic cache performance."""
    
    @pytest.fixture
    def cache_config(self):
        """Create semantic cache configuration."""
        return SemanticCacheConfig(
            cache_ttl_seconds=300,
            max_cache_size=500,
            similarity_threshold=0.8,
            embedding_dimension=384,
            max_entries=1000
        )
    
    @pytest.fixture
    def semantic_cache(self, cache_config):
        """Create semantic cache instance."""
        cache = SemanticCache("test_semantic", cache_config)
        cache._cache = {}  # Use in-memory storage for testing
        cache._semantic_index = {}  # Use in-memory index for testing
        return cache
    
    @pytest.mark.asyncio
    async def test_semantic_cache_get_performance(self, semantic_cache):
        """Test semantic cache get operation performance."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_keys = [f"key_{i}" for i in range(100)]
        
        # Initialize cache with some data
        for key in test_keys[:50]:
            await semantic_cache.set(key, f"value_{key}")
        
        # Run performance test
        metrics = await tester.run_async_performance_test(
            semantic_cache, "get", test_keys, iterations=1000
        )
        
        # Assert performance requirements
        assert metrics.avg_response_time_ms < 15  # Should be fast
        assert metrics.throughput_ops_per_sec > 80  # Should handle good throughput
        assert metrics.error_rate < 0.01  # Should have low error rate
    
    @pytest.mark.asyncio
    async def test_semantic_cache_find_similar_performance(self, semantic_cache):
        """Test semantic cache find similar operation performance."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_queries = [f"query_{i}" for i in range(50)]
        
        # Initialize cache with some data
        for i, query in enumerate(test_queries):
            await semantic_cache.set(query, f"response_{i}")
        
        # Run performance test
        start_time = time.time()
        for query in test_queries:
            await semantic_cache.find_similar(query, n_results=5, min_similarity=0.7)
        end_time = time.time()
        
        # Calculate metrics
        total_time = end_time - start_time
        avg_response_time = (total_time / len(test_queries)) * 1000
        throughput = len(test_queries) / total_time
        
        # Assert performance requirements
        assert avg_response_time < 100  # Should be reasonably fast for similarity search
        assert throughput > 5  # Should handle similarity search throughput
    
    @pytest.mark.asyncio
    async def test_semantic_cache_embedding_performance(self, semantic_cache):
        """Test semantic cache embedding generation performance."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_texts = [f"test text {i}" for i in range(100)]
        
        # Run performance test
        start_time = time.time()
        for text in test_texts:
            await semantic_cache.set(text, f"response_{text}")
        end_time = time.time()
        
        # Calculate metrics
        total_time = end_time - start_time
        avg_response_time = (total_time / len(test_texts)) * 1000
        throughput = len(test_texts) / total_time
        
        # Assert performance requirements
        assert avg_response_time < 200  # Should handle embedding generation
        assert throughput > 2  # Should handle embedding throughput


class TestVectorCachePerformance:
    """Test vector cache performance."""
    
    @pytest.fixture
    def cache_config(self):
        """Create vector cache configuration."""
        return VectorCacheConfig(
            cache_ttl_seconds=180,
            max_cache_size=1000,
            similarity_threshold=0.75,
            reranking_enabled=True,
            max_entries=5000
        )
    
    @pytest.fixture
    def vector_cache(self, cache_config):
        """Create vector cache instance."""
        cache = VectorCache("test_vector", cache_config)
        cache._cache = {}  # Use in-memory storage for testing
        cache._vector_index = {}  # Use in-memory index for testing
        return cache
    
    @pytest.mark.asyncio
    async def test_vector_cache_search_performance(self, vector_cache):
        """Test vector cache search operation performance."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_queries = [f"query_{i}" for i in range(50)]
        
        # Initialize cache with some data
        for i, query in enumerate(test_queries):
            await vector_cache.set(query, f"response_{i}")
        
        # Run performance test
        start_time = time.time()
        for query in test_queries:
            await vector_cache.search(query, n_results=10, min_similarity=0.7)
        end_time = time.time()
        
        # Calculate metrics
        total_time = end_time - start_time
        avg_response_time = (total_time / len(test_queries)) * 1000
        throughput = len(test_queries) / total_time
        
        # Assert performance requirements
        assert avg_response_time < 150  # Should be reasonably fast for vector search
        assert throughput > 3  # Should handle vector search throughput
    
    @pytest.mark.asyncio
    async def test_vector_cache_reranking_performance(self, vector_cache):
        """Test vector cache reranking performance."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_queries = [f"query_{i}" for i in range(20)]
        
        # Initialize cache with some data
        for i, query in enumerate(test_queries):
            await vector_cache.set(query, f"response_{i}")
        
        # Run performance test with reranking
        start_time = time.time()
        for query in test_queries:
            await vector_cache.search(query, n_results=10, min_similarity=0.7, use_reranking=True)
        end_time = time.time()
        
        # Calculate metrics
        total_time = end_time - start_time
        avg_response_time = (total_time / len(test_queries)) * 1000
        throughput = len(test_queries) / total_time
        
        # Assert performance requirements
        assert avg_response_time < 300  # Should handle reranking
        assert throughput > 1  # Should handle reranking throughput


class TestGlobalCachePerformance:
    """Test global cache performance."""
    
    @pytest.fixture
    def cache_config(self):
        """Create global cache configuration."""
        return GlobalCacheConfig(
            cache_ttl_seconds=600,
            max_cache_size=2000,
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
    async def test_global_cache_query_performance(self, global_cache):
        """Test global cache query operation performance."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_queries = [f"query_{i}" for i in range(50)]
        
        # Initialize cache with some data
        for i, query in enumerate(test_queries):
            await global_cache.set(query, f"response_{i}")
        
        # Run performance test
        metrics = await tester.run_async_performance_test(
            global_cache, "get", test_queries, iterations=100
        )
        
        # Assert performance requirements
        assert metrics.avg_response_time_ms < 20  # Should be fast
        assert metrics.throughput_ops_per_sec > 40  # Should handle good throughput
        assert metrics.error_rate < 0.01  # Should have low error rate
    
    @pytest.mark.asyncio
    async def test_global_cache_fallback_performance(self, global_cache):
        """Test global cache fallback performance."""
        tester = CachePerformanceTester()
        
        # Prepare test data
        test_queries = [f"query_{i}" for i in range(20)]
        
        # Mock RAG server for fallback testing
        with patch('src.cache_layers.global_cache.GlobalCache._query_rag_server') as mock_rag:
            mock_rag.return_value = [
                {"source": "doc1", "content": "Relevant content", "score": 0.9}
            ]
            
            # Run performance test with fallback
            start_time = time.time()
            for query in test_queries:
                await global_cache.query_rag(query, n_results=5, use_fallback=True)
            end_time = time.time()
            
            # Calculate metrics
            total_time = end_time - start_time
            avg_response_time = (total_time / len(test_queries)) * 1000
            throughput = len(test_queries) / total_time
            
            # Assert performance requirements
            assert avg_response_time < 500  # Should handle fallback with timeout
            assert throughput > 0.5  # Should handle fallback throughput


class TestCachePerformanceComparison:
    """Test performance comparison between cache layers."""
    
    @pytest.mark.asyncio
    async def test_cache_layer_performance_comparison(self):
        """Compare performance between different cache layers."""
        # Create cache instances
        predictive_config = PredictiveCacheConfig(cache_ttl_seconds=60, max_cache_size=100)
        semantic_config = SemanticCacheConfig(cache_ttl_seconds=300, max_cache_size=100)
        vector_config = VectorCacheConfig(cache_ttl_seconds=180, max_cache_size=100)
        global_config = GlobalCacheConfig(cache_ttl_seconds=600, max_cache_size=100)
        
        predictive_cache = PredictiveCache("test_predictive", predictive_config)
        semantic_cache = SemanticCache("test_semantic", semantic_config)
        vector_cache = VectorCache("test_vector", vector_config)
        global_cache = GlobalCache("test_global", global_config)
        
        # Initialize all caches
        for cache in [predictive_cache, semantic_cache, vector_cache, global_cache]:
            cache._cache = {}
        
        # Prepare test data
        test_keys = [f"key_{i}" for i in range(50)]
        test_values = [f"value_{i}" for i in range(50)]
        
        # Initialize caches with data
        for cache in [predictive_cache, semantic_cache, vector_cache, global_cache]:
            for key, value in zip(test_keys, test_values):
                await cache.set(key, value)
        
        # Test performance for each cache
        tester = CachePerformanceTester()
        caches = {
            "predictive": predictive_cache,
            "semantic": semantic_cache,
            "vector": vector_cache,
            "global": global_cache
        }
        
        results = {}
        for name, cache in caches.items():
            metrics = await tester.run_async_performance_test(
                cache, "get", test_keys, iterations=100
            )
            results[name] = metrics
        
        # Compare results
        print("\nCache Layer Performance Comparison:")
        for name, metrics in results.items():
            print(f"{name}: {metrics.avg_response_time_ms:.2f}ms avg, "
                  f"{metrics.throughput_ops_per_sec:.2f} ops/sec")
        
        # Assert that all caches meet minimum performance requirements
        for name, metrics in results.items():
            assert metrics.avg_response_time_ms < 50  # All should be reasonably fast
            assert metrics.throughput_ops_per_sec > 20  # All should handle decent throughput
            assert metrics.error_rate < 0.01  # All should have low error rate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])