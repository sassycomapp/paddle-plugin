"""
Stress Tests for High Load Scenarios.

This module contains stress tests for the cache management system under high load conditions,
testing concurrent operations, memory pressure, and system limits.
"""

import pytest
import asyncio
import time
import threading
import psutil
import signal
import sys
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
import multiprocessing as mp
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import random

from src.core.base_cache import CacheLayer, CacheStatus
from src.cache_layers.predictive_cache import PredictiveCache
from src.cache_layers.semantic_cache import SemanticCache
from src.cache_layers.vector_cache import VectorCache
from src.cache_layers.global_cache import GlobalCache
from src.cache_layers.vector_diary import VectorDiary
from src.core.config import PredictiveCacheConfig, SemanticCacheConfig, VectorCacheConfig, GlobalCacheConfig, VectorDiaryConfig


@dataclass
class StressTestResult:
    """Stress test result data structure."""
    test_name: str
    cache_layer: str
    duration_seconds: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    avg_response_time_ms: float
    max_response_time_ms: float
    min_response_time_ms: float
    throughput_ops_per_sec: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate: float
    system_load_avg: float
    memory_pressure_detected: bool
    cpu_pressure_detected: bool
    timeout_occurred: bool
    exceptions: List[str]


class HighLoadTester:
    """Main class for testing high load scenarios."""
    
    def __init__(self):
        self.results = []
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.initial_cpu = psutil.cpu_percent()
        self.system_load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        
    def monitor_system_resources(self, duration_seconds: int, interval_seconds: int = 1):
        """Monitor system resources during stress testing."""
        def monitor():
            start_time = time.time()
            memory_samples = []
            cpu_samples = []
            
            while time.time() - start_time < duration_seconds:
                memory_samples.append(self.process.memory_info().rss / 1024 / 1024)
                cpu_samples.append(psutil.cpu_percent())
                time.sleep(interval_seconds)
            
            return {
                "avg_memory_mb": np.mean(memory_samples),
                "max_memory_mb": np.max(memory_samples),
                "avg_cpu_percent": np.mean(cpu_samples),
                "max_cpu_percent": np.max(cpu_samples),
                "memory_growth_mb": np.max(memory_samples) - self.initial_memory,
                "cpu_growth_percent": np.max(cpu_samples) - self.initial_cpu
            }
        
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        return monitor_thread
    
    def generate_load_pattern(self, pattern_type: str, duration_seconds: int, 
                            base_ops_per_sec: int = 100) -> List[Tuple[int, int]]:
        """Generate load patterns for stress testing."""
        load_pattern = []
        intervals = duration_seconds
        
        if pattern_type == "constant":
            # Constant load
            for i in range(intervals):
                load_pattern.append((base_ops_per_sec, 1))
        
        elif pattern_type == "linear_increase":
            # Linear increase
            for i in range(intervals):
                ops_per_sec = base_ops_per_sec + (base_ops_per_sec * i // intervals)
                load_pattern.append((ops_per_sec, 1))
        
        elif pattern_type == "spike":
            # Spike pattern
            for i in range(intervals):
                if i % 10 < 2:  # Spike every 10 seconds for 2 seconds
                    ops_per_sec = base_ops_per_sec * 5
                else:
                    ops_per_sec = base_ops_per_sec
                load_pattern.append((ops_per_sec, 1))
        
        elif pattern_type == "burst":
            # Burst pattern
            for i in range(intervals):
                if i % 5 == 0:  # Burst every 5 seconds
                    ops_per_sec = base_ops_per_sec * 3
                else:
                    ops_per_sec = base_ops_per_sec // 2
                load_pattern.append((ops_per_sec, 1))
        
        elif pattern_type == "random":
            # Random load
            for i in range(intervals):
                ops_per_sec = base_ops_per_sec + random.randint(-base_ops_per_sec//2, base_ops_per_sec*2)
                ops_per_sec = max(1, ops_per_sec)  # Ensure at least 1 op/sec
                load_pattern.append((ops_per_sec, 1))
        
        return load_pattern
    
    async def run_concurrent_load_test(self, cache_instance, operation: str,
                                     load_pattern: List[Tuple[int, int]],
                                     test_data: List[Any],
                                     timeout_seconds: int = 300) -> StressTestResult:
        """Run a concurrent load test."""
        print(f"Running concurrent {operation} load test...")
        
        start_time = time.time()
        end_time = start_time + timeout_seconds
        
        # Track metrics
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        response_times = []
        exceptions = []
        
        # Create worker function
        async def worker(worker_id: int, ops_per_sec: int):
            nonlocal total_operations, successful_operations, failed_operations
            
            while time.time() < end_time:
                try:
                    # Calculate operations for this second
                    ops_this_second = int(ops_per_sec)
                    
                    for _ in range(ops_this_second):
                        if time.time() >= end_time:
                            break
                        
                        # Perform operation
                        op_start = time.time()
                        
                        if operation == "get":
                            key = test_data[random.randint(0, len(test_data) - 1)]
                            result = await cache_instance.get(key)
                        elif operation == "set":
                            key = f"stress_key_{worker_id}_{total_operations}"
                            value = test_data[random.randint(0, len(test_data) - 1)]
                            result = await cache_instance.set(key, value)
                        elif operation == "delete":
                            key = test_data[random.randint(0, len(test_data) - 1)]
                            result = await cache_instance.delete(key)
                        else:
                            raise ValueError(f"Unknown operation: {operation}")
                        
                        op_end = time.time()
                        response_time = (op_end - op_start) * 1000
                        
                        # Update metrics
                        total_operations += 1
                        response_times.append(response_time)
                        
                        if result is not None and (operation == "get" and hasattr(result, 'status') and result.status == CacheStatus.HIT) or (operation in ["set", "delete"] and result):
                            successful_operations += 1
                        else:
                            failed_operations += 1
                        
                        # Small delay to spread out operations
                        await asyncio.sleep(1.0 / ops_per_sec)
                
                except Exception as e:
                    failed_operations += 1
                    exceptions.append(str(e))
        
        # Start monitoring
        monitor_thread = self.monitor_system_resources(timeout_seconds)
        
        # Create and start workers
        workers = []
        for i, (ops_per_sec, _) in enumerate(load_pattern):
            if time.time() >= end_time:
                break
            
            worker_task = asyncio.create_task(worker(i, ops_per_sec))
            workers.append(worker_task)
            
            # Control worker creation rate
            await asyncio.sleep(0.1)
        
        # Wait for workers to complete or timeout
        try:
            await asyncio.wait_for(asyncio.gather(*workers, return_exceptions=True), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            print(f"Test timed out after {timeout_seconds} seconds")
        
        # Wait for monitoring to complete
        monitor_thread.join()
        
        # Calculate final metrics
        actual_duration = time.time() - start_time
        avg_response_time = np.mean(response_times) if response_times else 0
        max_response_time = np.max(response_times) if response_times else 0
        min_response_time = np.min(response_times) if response_times else 0
        throughput = total_operations / actual_duration if actual_duration > 0 else 0
        error_rate = failed_operations / total_operations if total_operations > 0 else 0
        
        # Check system pressure
        current_memory = self.process.memory_info().rss / 1024 / 1024
        current_cpu = psutil.cpu_percent()
        memory_pressure = current_memory > (self.initial_memory + 500)  # 500MB growth threshold
        cpu_pressure = current_cpu > 90  # 90% CPU threshold
        
        # Create result
        result = StressTestResult(
            test_name=f"concurrent_{operation}_load",
            cache_layer=cache_instance.get_layer().value,
            duration_seconds=actual_duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            avg_response_time_ms=avg_response_time,
            max_response_time_ms=max_response_time,
            min_response_time_ms=min_response_time,
            throughput_ops_per_sec=throughput,
            memory_usage_mb=current_memory - self.initial_memory,
            cpu_usage_percent=current_cpu - self.initial_cpu,
            error_rate=error_rate,
            system_load_avg=psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            memory_pressure_detected=memory_pressure,
            cpu_pressure_detected=cpu_pressure,
            timeout_occurred=actual_duration >= timeout_seconds,
            exceptions=exceptions
        )
        
        self.results.append(result)
        return result
    
    def run_memory_pressure_test(self, cache_instance, operation: str,
                               test_data: List[Any], target_memory_mb: int = 1000) -> StressTestResult:
        """Run memory pressure test."""
        print(f"Running memory pressure test for {operation}...")
        
        start_time = time.time()
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        response_times = []
        exceptions = []
        
        # Monitor memory usage
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        while True:
            try:
                # Check memory usage
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory
                
                # Stop if we've reached target memory or timeout
                if memory_growth >= target_memory_mb or time.time() - start_time > 300:
                    break
                
                # Perform operation
                op_start = time.time()
                
                if operation == "set":
                    key = f"memory_key_{total_operations}"
                    value = test_data[total_operations % len(test_data)]
                    result = cache_instance.set(key, value)
                elif operation == "get":
                    key = test_data[total_operations % len(test_data)]
                    result = cache_instance.get(key)
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                op_end = time.time()
                response_time = (op_end - op_start) * 1000
                
                # Update metrics
                total_operations += 1
                response_times.append(response_time)
                
                if result:
                    successful_operations += 1
                else:
                    failed_operations += 1
                
            except Exception as e:
                failed_operations += 1
                exceptions.append(str(e))
        
        # Calculate final metrics
        actual_duration = time.time() - start_time
        avg_response_time = np.mean(response_times) if response_times else 0
        max_response_time = np.max(response_times) if response_times else 0
        min_response_time = np.min(response_times) if response_times else 0
        throughput = total_operations / actual_duration if actual_duration > 0 else 0
        error_rate = failed_operations / total_operations if total_operations > 0 else 0
        
        # Check system pressure
        current_memory = self.process.memory_info().rss / 1024 / 1024
        current_cpu = psutil.cpu_percent()
        memory_pressure = current_memory > (initial_memory + target_memory_mb * 0.9)
        cpu_pressure = current_cpu > 90
        
        # Create result
        result = StressTestResult(
            test_name=f"memory_pressure_{operation}",
            cache_layer=cache_instance.get_layer().value,
            duration_seconds=actual_duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            avg_response_time_ms=avg_response_time,
            max_response_time_ms=max_response_time,
            min_response_time_ms=min_response_time,
            throughput_ops_per_sec=throughput,
            memory_usage_mb=current_memory - initial_memory,
            cpu_usage_percent=current_cpu - self.initial_cpu,
            error_rate=error_rate,
            system_load_avg=psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            memory_pressure_detected=memory_pressure,
            cpu_pressure_detected=cpu_pressure,
            timeout_occurred=actual_duration >= 300,
            exceptions=exceptions
        )
        
        self.results.append(result)
        return result
    
    def run_cpu_pressure_test(self, cache_instance, operation: str,
                            test_data: List[Any], target_cpu_percent: int = 95) -> StressTestResult:
        """Run CPU pressure test."""
        print(f"Running CPU pressure test for {operation}...")
        
        start_time = time.time()
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        response_times = []
        exceptions = []
        
        # Monitor CPU usage
        initial_cpu = psutil.cpu_percent()
        
        while True:
            try:
                # Check CPU usage
                current_cpu = psutil.cpu_percent()
                cpu_growth = current_cpu - initial_cpu
                
                # Stop if we've reached target CPU or timeout
                if current_cpu >= target_cpu_percent or time.time() - start_time > 300:
                    break
                
                # Perform operation
                op_start = time.time()
                
                if operation == "set":
                    key = f"cpu_key_{total_operations}"
                    value = test_data[total_operations % len(test_data)]
                    result = cache_instance.set(key, value)
                elif operation == "get":
                    key = test_data[total_operations % len(test_data)]
                    result = cache_instance.get(key)
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                op_end = time.time()
                response_time = (op_end - op_start) * 1000
                
                # Update metrics
                total_operations += 1
                response_times.append(response_time)
                
                if result:
                    successful_operations += 1
                else:
                    failed_operations += 1
                
                # Add some CPU load
                _ = [i*i for i in range(1000)]
                
            except Exception as e:
                failed_operations += 1
                exceptions.append(str(e))
        
        # Calculate final metrics
        actual_duration = time.time() - start_time
        avg_response_time = np.mean(response_times) if response_times else 0
        max_response_time = np.max(response_times) if response_times else 0
        min_response_time = np.min(response_times) if response_times else 0
        throughput = total_operations / actual_duration if actual_duration > 0 else 0
        error_rate = failed_operations / total_operations if total_operations > 0 else 0
        
        # Check system pressure
        current_memory = self.process.memory_info().rss / 1024 / 1024
        current_cpu = psutil.cpu_percent()
        memory_pressure = current_memory > (self.initial_memory + 500)
        cpu_pressure = current_cpu >= target_cpu_percent
        
        # Create result
        result = StressTestResult(
            test_name=f"cpu_pressure_{operation}",
            cache_layer=cache_instance.get_layer().value,
            duration_seconds=actual_duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            avg_response_time_ms=avg_response_time,
            max_response_time_ms=max_response_time,
            min_response_time_ms=min_response_time,
            throughput_ops_per_sec=throughput,
            memory_usage_mb=current_memory - self.initial_memory,
            cpu_usage_percent=current_cpu - self.initial_cpu,
            error_rate=error_rate,
            system_load_avg=psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            memory_pressure_detected=memory_pressure,
            cpu_pressure_detected=cpu_pressure,
            timeout_occurred=actual_duration >= 300,
            exceptions=exceptions
        )
        
        self.results.append(result)
        return result
    
    def generate_stress_test_report(self) -> Dict[str, Any]:
        """Generate a comprehensive stress test report."""
        if not self.results:
            return {"error": "No stress test results available"}
        
        report = {
            "test_summary": {
                "total_tests": len(self.results),
                "cache_layers": list(set(r.cache_layer for r in self.results)),
                "test_types": list(set(r.test_name for r in self.results))
            },
            "stress_test_results": [],
            "aggregated_metrics": {
                "avg_duration_seconds": np.mean([r.duration_seconds for r in self.results]),
                "avg_total_operations": np.mean([r.total_operations for r in self.results]),
                "avg_successful_operations": np.mean([r.successful_operations for r in self.results]),
                "avg_failed_operations": np.mean([r.failed_operations for r in self.results]),
                "avg_response_time_ms": np.mean([r.avg_response_time_ms for r in self.results]),
                "avg_throughput_ops_per_sec": np.mean([r.throughput_ops_per_sec for r in self.results]),
                "avg_memory_usage_mb": np.mean([r.memory_usage_mb for r in self.results]),
                "avg_cpu_usage_percent": np.mean([r.cpu_usage_percent for r in self.results]),
                "avg_error_rate": np.mean([r.error_rate for r in self.results]),
                "timeout_rate": np.mean([1 if r.timeout_occurred else 0 for r in self.results]),
                "memory_pressure_rate": np.mean([1 if r.memory_pressure_detected else 0 for r in self.results]),
                "cpu_pressure_rate": np.mean([1 if r.cpu_pressure_detected else 0 for r in self.results])
            },
            "system_metrics": {
                "initial_memory_mb": self.initial_memory,
                "final_memory_mb": self.process.memory_info().rss / 1024 / 1024,
                "initial_cpu_percent": self.initial_cpu,
                "final_cpu_percent": psutil.cpu_percent(),
                "memory_growth_mb": self.process.memory_info().rss / 1024 / 1024 - self.initial_memory,
                "cpu_growth_percent": psutil.cpu_percent() - self.initial_cpu,
                "system_load_avg": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            },
            "recommendations": self._generate_recommendations()
        }
        
        # Add individual test results
        for result in self.results:
            report["stress_test_results"].append({
                "test_name": result.test_name,
                "cache_layer": result.cache_layer,
                "duration_seconds": result.duration_seconds,
                "total_operations": result.total_operations,
                "successful_operations": result.successful_operations,
                "failed_operations": result.failed_operations,
                "avg_response_time_ms": result.avg_response_time_ms,
                "max_response_time_ms": result.max_response_time_ms,
                "min_response_time_ms": result.min_response_time_ms,
                "throughput_ops_per_sec": result.throughput_ops_per_sec,
                "memory_usage_mb": result.memory_usage_mb,
                "cpu_usage_percent": result.cpu_usage_percent,
                "error_rate": result.error_rate,
                "system_load_avg": result.system_load_avg,
                "memory_pressure_detected": result.memory_pressure_detected,
                "cpu_pressure_detected": result.cpu_pressure_detected,
                "timeout_occurred": result.timeout_occurred,
                "exceptions": result.exceptions
            })
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check for high error rates
        avg_error_rate = np.mean([r.error_rate for r in self.results])
        if avg_error_rate > 0.05:
            recommendations.append("High error rate detected. Consider increasing timeout values or implementing better error handling.")
        
        # Check for memory pressure
        memory_pressure_rate = np.mean([1 if r.memory_pressure_detected else 0 for r in self.results])
        if memory_pressure_rate > 0.5:
            recommendations.append("Memory pressure detected frequently. Consider implementing better memory management or increasing system memory.")
        
        # Check for CPU pressure
        cpu_pressure_rate = np.mean([1 if r.cpu_pressure_detected else 0 for r in self.results])
        if cpu_pressure_rate > 0.5:
            recommendations.append("CPU pressure detected frequently. Consider optimizing cache operations or increasing CPU resources.")
        
        # Check for timeouts
        timeout_rate = np.mean([1 if r.timeout_occurred else 0 for r in self.results])
        if timeout_rate > 0.2:
            recommendations.append("High timeout rate detected. Consider increasing timeout values or optimizing performance.")
        
        # Check response times
        avg_response_time = np.mean([r.avg_response_time_ms for r in self.results])
        if avg_response_time > 100:
            recommendations.append("High response times detected. Consider optimizing cache operations or increasing system resources.")
        
        # Check throughput
        avg_throughput = np.mean([r.throughput_ops_per_sec for r in self.results])
        if avg_throughput < 10:
            recommendations.append("Low throughput detected. Consider optimizing cache operations or increasing system resources.")
        
        return recommendations


class TestPredictiveCacheStress:
    """Test predictive cache under stress conditions."""
    
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
    async def test_predictive_cache_high_load_get(self, predictive_cache):
        """Test predictive cache under high load for get operations."""
        tester = HighLoadTester()
        
        # Prepare test data
        test_keys = [f"key_{i}" for i in range(100)]
        
        # Initialize cache with some data
        for key in test_keys[:50]:
            await predictive_cache.set(key, f"value_{key}")
        
        # Generate load pattern
        load_pattern = tester.generate_load_pattern("spike", duration_seconds=60, base_ops_per_sec=100)
        
        # Run stress test
        result = await tester.run_concurrent_load_test(
            predictive_cache, "get", load_pattern, test_keys, timeout_seconds=60
        )
        
        # Assert stress test requirements
        assert result.error_rate < 0.1  # Should handle some errors under stress
        assert result.throughput_ops_per_sec > 50  # Should maintain reasonable throughput
        assert not result.memory_pressure_detected or result.memory_usage_mb < 1000  # Memory should be manageable
        assert not result.cpu_pressure_detected or result.cpu_usage_percent < 95  # CPU should be manageable
    
    @pytest.mark.asyncio
    async def test_predictive_cache_high_load_set(self, predictive_cache):
        """Test predictive cache under high load for set operations."""
        tester = HighLoadTester()
        
        # Prepare test data
        test_values = [f"value_{i}" for i in range(100)]
        
        # Generate load pattern
        load_pattern = tester.generate_load_pattern("burst", duration_seconds=60, base_ops_per_sec=50)
        
        # Run stress test
        result = await tester.run_concurrent_load_test(
            predictive_cache, "set", load_pattern, test_values, timeout_seconds=60
        )
        
        # Assert stress test requirements
        assert result.error_rate < 0.1  # Should handle some errors under stress
        assert result.throughput_ops_per_sec > 25  # Should maintain reasonable throughput
        assert not result.memory_pressure_detected or result.memory_usage_mb < 1000  # Memory should be manageable
    
    def test_predictive_cache_memory_pressure(self, predictive_cache):
        """Test predictive cache under memory pressure."""
        tester = HighLoadTester()
        
        # Prepare test data
        test_values = [f"value_{i}" for i in range(1000)]
        
        # Run memory pressure test
        result = tester.run_memory_pressure_test(
            predictive_cache, "set", test_values, target_memory_mb=500
        )
        
        # Assert stress test requirements
        assert result.total_operations > 100  # Should perform many operations
        assert result.error_rate < 0.2  # Should handle some errors under memory pressure
        assert result.memory_usage_mb >= 400  # Should reach target memory pressure
    
    def test_predictive_cache_cpu_pressure(self, predictive_cache):
        """Test predictive cache under CPU pressure."""
        tester = HighLoadTester()
        
        # Prepare test data
        test_values = [f"value_{i}" for i in range(100)]
        
        # Run CPU pressure test
        result = tester.run_cpu_pressure_test(
            predictive_cache, "get", test_values, target_cpu_percent=90
        )
        
        # Assert stress test requirements
        assert result.total_operations > 50  # Should perform many operations
        assert result.error_rate < 0.2  # Should handle some errors under CPU pressure
        assert result.cpu_usage_percent >= 80  # Should reach target CPU pressure


class TestSemanticCacheStress:
    """Test semantic cache under stress conditions."""
    
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
    async def test_semantic_cache_high_load_get(self, semantic_cache):
        """Test semantic cache under high load for get operations."""
        tester = HighLoadTester()
        
        # Prepare test data
        test_keys = [f"key_{i}" for i in range(100)]
        
        # Initialize cache with some data
        for key in test_keys[:50]:
            await semantic_cache.set(key, f"value_{key}")
        
        # Generate load pattern
        load_pattern = tester.generate_load_pattern("constant", duration_seconds=60, base_ops_per_sec=80)
        
        # Run stress test
        result = await tester.run_concurrent_load_test(
            semantic_cache, "get", load_pattern, test_keys, timeout_seconds=60
        )
        
        # Assert stress test requirements
        assert result.error_rate < 0.1  # Should handle some errors under stress
        assert result.throughput_ops_per_sec > 40  # Should maintain reasonable throughput
        assert not result.memory_pressure_detected or result.memory_usage_mb < 1000  # Memory should be manageable
    
    @pytest.mark.asyncio
    async def test_semantic_cache_high_load_similar(self, semantic_cache):
        """Test semantic cache under high load for similar operations."""
        tester = HighLoadTester()
        
        # Prepare test data
        test_queries = [f"query_{i}" for i in range(50)]
        
        # Initialize cache with some data
        for i, query in enumerate(test_queries):
            await semantic_cache.set(query, f"response_{i}")
        
        # Generate load pattern
        load_pattern = tester.generate_load_pattern("linear_increase", duration_seconds=60, base_ops_per_sec=20)
        
        # Run stress test
        start_time = time.time()
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        response_times = []
        
        for ops_per_sec, _ in load_pattern:
            if time.time() - start_time >= 60:
                break
            
            for _ in range(int(ops_per_sec)):
                try:
                    query = test_queries[random.randint(0, len(test_queries) - 1)]
                    op_start = time.time()
                    result = await semantic_cache.find_similar(query, n_results=5, min_similarity=0.7)
                    op_end = time.time()
                    
                    response_time = (op_end - op_start) * 1000
                    response_times.append(response_time)
                    total_operations += 1
                    successful_operations += 1
                    
                except Exception as e:
                    failed_operations += 1
        
        # Calculate metrics
        actual_duration = time.time() - start_time
        avg_response_time = np.mean(response_times) if response_times else 0
        throughput = total_operations / actual_duration if actual_duration > 0 else 0
        error_rate = failed_operations / total_operations if total_operations > 0 else 0
        
        # Assert stress test requirements
        assert error_rate < 0.1  # Should handle some errors under stress
        assert throughput > 5  # Should maintain reasonable throughput
        assert avg_response_time < 500  # Should handle similarity search under stress


class TestVectorCacheStress:
    """Test vector cache under stress conditions."""
    
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
    async def test_vector_cache_high_load_search(self, vector_cache):
        """Test vector cache under high load for search operations."""
        tester = HighLoadTester()
        
        # Prepare test data
        test_queries = [f"query_{i}" for i in range(50)]
        
        # Initialize cache with some data
        for i, query in enumerate(test_queries):
            await vector_cache.set(query, f"response_{i}")
        
        # Generate load pattern
        load_pattern = tester.generate_load_pattern("random", duration_seconds=60, base_ops_per_sec=30)
        
        # Run stress test
        start_time = time.time()
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        response_times = []
        
        for ops_per_sec, _ in load_pattern:
            if time.time() - start_time >= 60:
                break
            
            for _ in range(int(ops_per_sec)):
                try:
                    query = test_queries[random.randint(0, len(test_queries) - 1)]
                    op_start = time.time()
                    result = await vector_cache.search(query, n_results=10, min_similarity=0.7)
                    op_end = time.time()
                    
                    response_time = (op_end - op_start) * 1000
                    response_times.append(response_time)
                    total_operations += 1
                    successful_operations += 1
                    
                except Exception as e:
                    failed_operations += 1
        
        # Calculate metrics
        actual_duration = time.time() - start_time
        avg_response_time = np.mean(response_times) if response_times else 0
        throughput = total_operations / actual_duration if actual_duration > 0 else 0
        error_rate = failed_operations / total_operations if total_operations > 0 else 0
        
        # Assert stress test requirements
        assert error_rate < 0.1  # Should handle some errors under stress
        assert throughput > 3  # Should maintain reasonable throughput
        assert avg_response_time < 800  # Should handle vector search under stress


class TestGlobalCacheStress:
    """Test global cache under stress conditions."""
    
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
    async def test_global_cache_high_load_query(self, global_cache):
        """Test global cache under high load for query operations."""
        tester = HighLoadTester()
        
        # Prepare test data
        test_queries = [f"query_{i}" for i in range(50)]
        
        # Initialize cache with some data
        for i, query in enumerate(test_queries):
            await global_cache.set(query, f"response_{i}")
        
        # Generate load pattern
        load_pattern = tester.generate_load_pattern("constant", duration_seconds=60, base_ops_per_sec=40)
        
        # Run stress test
        result = await tester.run_concurrent_load_test(
            global_cache, "get", load_pattern, test_queries, timeout_seconds=60
        )
        
        # Assert stress test requirements
        assert result.error_rate < 0.1  # Should handle some errors under stress
        assert result.throughput_ops_per_sec > 20  # Should maintain reasonable throughput
        assert not result.memory_pressure_detected or result.memory_usage_mb < 1000  # Memory should be manageable


class TestCrossCacheStress:
    """Test cross-cache stress scenarios."""
    
    @pytest.mark.asyncio
    async def test_cross_cache_concurrent_stress(self):
        """Test all cache layers under concurrent stress."""
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
        test_data = [f"data_{i}" for i in range(100)]
        
        # Initialize caches with data
        for cache in [predictive_cache, semantic_cache, vector_cache, global_cache]:
            for i, data in enumerate(test_data[:50]):
                await cache.set(f"key_{i}", data)
        
        # Create tester
        tester = HighLoadTester()
        
        # Run concurrent stress test
        start_time = time.time()
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        response_times = []
        
        async def worker(worker_id: int):
            nonlocal total_operations, successful_operations, failed_operations
            
            while time.time() - start_time < 60:  # 60 seconds test
                try:
                    # Randomly select cache and operation
                    cache = random.choice([predictive_cache, semantic_cache, vector_cache, global_cache])
                    operation = random.choice(["get", "set"])
                    
                    if operation == "get":
                        key = f"key_{random.randint(0, 49)}"
                        op_start = time.time()
                        result = await cache.get(key)
                        op_end = time.time()
                    else:
                        key = f"stress_key_{worker_id}_{total_operations}"
                        value = test_data[random.randint(0, len(test_data) - 1)]
                        op_start = time.time()
                        result = await cache.set(key, value)
                        op_end = time.time()
                    
                    response_time = (op_end - op_start) * 1000
                    response_times.append(response_time)
                    total_operations += 1
                    
                    if result is not None and (operation == "get" and hasattr(result, 'status') and result.status == CacheStatus.HIT) or (operation == "set" and result):
                        successful_operations += 1
                    else:
                        failed_operations += 1
                    
                    # Small delay
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    failed_operations += 1
        
        # Start multiple workers
        workers = []
        for i in range(10):  # 10 concurrent workers
            worker_task = asyncio.create_task(worker(i))
            workers.append(worker_task)
        
        # Wait for test duration
        await asyncio.sleep(60)
        
        # Cancel workers
        for worker in workers:
            worker.cancel()
        
        # Calculate metrics
        actual_duration = time.time() - start_time
        avg_response_time = np.mean(response_times) if response_times else 0
        throughput = total_operations / actual_duration if actual_duration > 0 else 0
        error_rate = failed_operations / total_operations if total_operations > 0 else 0
        
        # Assert stress test requirements
        assert error_rate < 0.1  # Should handle some errors under concurrent stress
        assert throughput > 50  # Should maintain reasonable concurrent throughput
        assert avg_response_time < 100  # Should handle concurrent operations well


if __name__ == "__main__":
    pytest.main([__file__, "-v"])