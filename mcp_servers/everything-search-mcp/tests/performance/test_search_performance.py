#!/usr/bin/env python3
"""
Performance Tests for Search Operations

This module contains performance tests for search operations in the Everything Search MCP Server.
Tests cover search performance with large datasets, concurrent operations, and resource usage.

Author: Kilo Code
Version: 1.0.0
"""

import pytest
import asyncio
import unittest.mock as mock
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import os
import json
import time
import psutil
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the src directory to the Python path
sys_path = str(Path(__file__).parent.parent.parent / "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from everything_search_mcp_server import EverythingSearchMCPServer


class TestSearchPerformance:
    """Test suite for search performance."""
    
    @pytest.fixture
    def mock_server(self):
        """Create a mock server instance for testing."""
        with patch('everything_search_mcp_server.everything_sdk') as mock_sdk:
            # Mock SDK availability
            mock_sdk.initialize = Mock()
            
            # Create server instance with mocked SDK
            server = EverythingSearchMCPServer()
            server.sdk_available = True
            server.sdk_path = "C:\\Everything64.dll"
            
            return server
    
    @pytest.fixture
    def large_dataset(self):
        """Create a large dataset for performance testing."""
        # Generate mock search results
        results = []
        for i in range(10000):  # 10,000 results
            results.append({
                'name': f'file_{i:05d}.txt',
                'path': f'C:\\test\\folder\\subfolder\\file_{i:05d}.txt',
                'size': 1024 + (i % 1024),  # Variable size
                'modified': f'2023-01-{i % 31 + 1:02d}T00:00:00',
                'extension': 'txt',
                'is_directory': False
            })
        return results
    
    @pytest.fixture
    def medium_dataset(self):
        """Create a medium dataset for performance testing."""
        # Generate mock search results
        results = []
        for i in range(1000):  # 1,000 results
            results.append({
                'name': f'file_{i:05d}.txt',
                'path': f'C:\\test\\folder\\subfolder\\file_{i:05d}.txt',
                'size': 1024 + (i % 1024),  # Variable size
                'modified': f'2023-01-{i % 31 + 1:02d}T00:00:00',
                'extension': 'txt',
                'is_directory': False
            })
        return results
    
    @pytest.fixture
    def small_dataset(self):
        """Create a small dataset for performance testing."""
        # Generate mock search results
        results = []
        for i in range(100):  # 100 results
            results.append({
                'name': f'file_{i:05d}.txt',
                'path': f'C:\\test\\folder\\subfolder\\file_{i:05d}.txt',
                'size': 1024 + (i % 1024),  # Variable size
                'modified': f'2023-01-{i % 31 + 1:02d}T00:00:00',
                'extension': 'txt',
                'is_directory': False
            })
        return results
    
    def measure_performance(self, func, *args, **kwargs):
        """Measure performance of a function."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        return {
            'result': result,
            'execution_time': execution_time,
            'memory_usage': memory_usage,
            'peak_memory': max(start_memory, end_memory)
        }
    
    @pytest.mark.asyncio
    async def test_search_performance_small_dataset(self, mock_server, small_dataset):
        """Test search performance with small dataset."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=small_dataset)
        
        # Measure search performance
        performance = self.measure_performance(
            asyncio.run, 
            mock_server.search_files("test", max_results=100)
        )
        
        # Check performance metrics
        assert performance['execution_time'] < 1.0  # Should complete in less than 1 second
        assert performance['memory_usage'] < 1024 * 1024  # Should use less than 1MB
        assert performance['result']['total_count'] == 100
        assert len(performance['result']['results']) == 100
    
    @pytest.mark.asyncio
    async def test_search_performance_medium_dataset(self, mock_server, medium_dataset):
        """Test search performance with medium dataset."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        # Measure search performance
        performance = self.measure_performance(
            asyncio.run, 
            mock_server.search_files("test", max_results=1000)
        )
        
        # Check performance metrics
        assert performance['execution_time'] < 2.0  # Should complete in less than 2 seconds
        assert performance['memory_usage'] < 5 * 1024 * 1024  # Should use less than 5MB
        assert performance['result']['total_count'] == 1000
        assert len(performance['result']['results']) == 1000
    
    @pytest.mark.asyncio
    async def test_search_performance_large_dataset(self, mock_server, large_dataset):
        """Test search performance with large dataset."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=large_dataset)
        
        # Measure search performance
        performance = self.measure_performance(
            asyncio.run, 
            mock_server.search_files("test", max_results=10000)
        )
        
        # Check performance metrics
        assert performance['execution_time'] < 5.0  # Should complete in less than 5 seconds
        assert performance['memory_usage'] < 20 * 1024 * 1024  # Should use less than 20MB
        assert performance['result']['total_count'] == 10000
        assert len(performance['result']['results']) == 10000
    
    @pytest.mark.asyncio
    async def test_search_performance_with_wildcards(self, mock_server, medium_dataset):
        """Test search performance with wildcard patterns."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        # Measure wildcard search performance
        performance = self.measure_performance(
            asyncio.run, 
            mock_server.search_files("file_*.txt", max_results=1000)
        )
        
        # Check performance metrics
        assert performance['execution_time'] < 2.0  # Should complete in less than 2 seconds
        assert performance['memory_usage'] < 5 * 1024 * 1024  # Should use less than 5MB
        assert performance['result']['total_count'] == 1000
    
    @pytest.mark.asyncio
    async def test_search_performance_with_regex(self, mock_server, medium_dataset):
        """Test search performance with regex patterns."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        # Measure regex search performance
        performance = self.measure_performance(
            asyncio.run, 
            mock_server.search_files_advanced(r"file_\d+\.txt", max_results=1000, regex=True)
        )
        
        # Check performance metrics
        assert performance['execution_time'] < 3.0  # Should complete in less than 3 seconds
        assert performance['memory_usage'] < 5 * 1024 * 1024  # Should use less than 5MB
        assert performance['result']['total_count'] == 1000
    
    @pytest.mark.asyncio
    async def test_search_performance_case_sensitivity(self, mock_server, medium_dataset):
        """Test search performance with case sensitivity."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        # Measure case sensitive search performance
        performance = self.measure_performance(
            asyncio.run, 
            mock_server.search_files_advanced("FILE", max_results=1000, case_sensitive=True)
        )
        
        # Check performance metrics
        assert performance['execution_time'] < 2.0  # Should complete in less than 2 seconds
        assert performance['memory_usage'] < 5 * 1024 * 1024  # Should use less than 5MB
        assert performance['result']['total_count'] == 0  # Should find no results due to case sensitivity
    
    @pytest.mark.asyncio
    async def test_search_performance_whole_word(self, mock_server, medium_dataset):
        """Test search performance with whole word matching."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        # Measure whole word search performance
        performance = self.measure_performance(
            asyncio.run, 
            mock_server.search_files_advanced("file", max_results=1000, whole_word=True)
        )
        
        # Check performance metrics
        assert performance['execution_time'] < 2.0  # Should complete in less than 2 seconds
        assert performance['memory_usage'] < 5 * 1024 * 1024  # Should use less than 5MB
        assert performance['result']['total_count'] == 0  # Should find no results due to whole word matching
    
    @pytest.mark.asyncio
    async def test_search_performance_extension_filter(self, mock_server, medium_dataset):
        """Test search performance with extension filtering."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        # Measure extension search performance
        performance = self.measure_performance(
            asyncio.run, 
            mock_server.search_by_extension("txt", max_results=1000)
        )
        
        # Check performance metrics
        assert performance['execution_time'] < 2.0  # Should complete in less than 2 seconds
        assert performance['memory_usage'] < 5 * 1024 * 1024  # Should use less than 5MB
        assert performance['result']['total_count'] == 1000
    
    @pytest.mark.asyncio
    async def test_search_performance_size_filter(self, mock_server, medium_dataset):
        """Test search performance with size filtering."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_size = Mock(return_value=medium_dataset)
        
        # Measure size search performance
        performance = self.measure_performance(
            asyncio.run, 
            mock_server.search_by_size(min_size=1000, max_size=2000, size_unit="bytes", max_results=1000)
        )
        
        # Check performance metrics
        assert performance['execution_time'] < 2.0  # Should complete in less than 2 seconds
        assert performance['memory_usage'] < 5 * 1024 * 1024  # Should use less than 5MB
        assert performance['result']['total_count'] == 1000
    
    @pytest.mark.asyncio
    async def test_search_performance_date_filter(self, mock_server, medium_dataset):
        """Test search performance with date filtering."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_date = Mock(return_value=medium_dataset)
        
        # Measure date search performance
        performance = self.measure_performance(
            asyncio.run, 
            mock_server.search_by_date(date_from="2023-01-01", date_to="2023-01-31", max_results=1000)
        )
        
        # Check performance metrics
        assert performance['execution_time'] < 2.0  # Should complete in less than 2 seconds
        assert performance['memory_usage'] < 5 * 1024 * 1024  # Should use less than 5MB
        assert performance['result']['total_count'] == 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self, mock_server, medium_dataset):
        """Test concurrent search performance."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        # Test concurrent searches
        async def concurrent_search(query, max_results):
            return await mock_server.search_files(query, max_results=max_results)
        
        queries = ["test1", "test2", "test3", "test4", "test5"]
        max_concurrent = 5
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        # Run concurrent searches
        tasks = [concurrent_search(query, 1000) for query in queries]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        # Check performance metrics
        assert execution_time < 3.0  # Should complete in less than 3 seconds
        assert memory_usage < 10 * 1024 * 1024  # Should use less than 10MB
        assert len(results) == 5
        
        # Check that all searches returned results
        for result in results:
            assert result['total_count'] == 1000
            assert len(result['results']) == 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_search_performance_with_limits(self, mock_server, medium_dataset):
        """Test concurrent search performance with result limits."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        # Test concurrent searches with different limits
        async def concurrent_search_with_limit(query, max_results):
            return await mock_server.search_files(query, max_results=max_results)
        
        search_params = [
            ("test1", 100),
            ("test2", 500),
            ("test3", 1000),
            ("test4", 2000),
            ("test5", 5000)
        ]
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        # Run concurrent searches with different limits
        tasks = [concurrent_search_with_limit(query, limit) for query, limit in search_params]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        # Check performance metrics
        assert execution_time < 3.0  # Should complete in less than 3 seconds
        assert memory_usage < 15 * 1024 * 1024  # Should use less than 15MB
        assert len(results) == 5
        
        # Check that searches respected their limits
        for i, result in enumerate(results):
            expected_limit = search_params[i][1]
            assert result['total_count'] <= expected_limit
            assert len(result['results']) <= expected_limit
    
    @pytest.mark.asyncio
    async def test_memory_usage_scaling(self, mock_server):
        """Test memory usage scaling with dataset size."""
        dataset_sizes = [100, 1000, 10000, 50000]
        memory_usage_results = []
        
        for size in dataset_sizes:
            # Create dataset
            dataset = []
            for i in range(size):
                dataset.append({
                    'name': f'file_{i:05d}.txt',
                    'path': f'C:\\test\\folder\\subfolder\\file_{i:05d}.txt',
                    'size': 1024 + (i % 1024),
                    'modified': f'2023-01-{i % 31 + 1:02d}T00:00:00',
                    'extension': 'txt',
                    'is_directory': False
                })
            
            # Mock search results
            mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=dataset)
            
            # Measure memory usage
            start_memory = psutil.Process().memory_info().rss
            result = await mock_server.search_files("test", max_results=size)
            end_memory = psutil.Process().memory_info().rss
            
            memory_usage = end_memory - start_memory
            memory_usage_results.append({
                'dataset_size': size,
                'memory_usage': memory_usage,
                'memory_usage_per_item': memory_usage / size if size > 0 else 0
            })
        
        # Check memory usage scaling
        for i in range(1, len(memory_usage_results)):
            prev = memory_usage_results[i-1]
            curr = memory_usage_results[i]
            
            # Memory usage should scale roughly linearly with dataset size
            expected_ratio = curr['dataset_size'] / prev['dataset_size']
            actual_ratio = curr['memory_usage'] / prev['memory_usage']
            
            # Allow for some overhead (up to 2x the expected ratio)
            assert actual_ratio <= expected_ratio * 2, f"Memory usage scaling issue: {actual_ratio} > {expected_ratio * 2}"
    
    @pytest.mark.asyncio
    async def test_search_performance_with_different_max_results(self, mock_server, medium_dataset):
        """Test search performance with different max_results values."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        max_results_values = [10, 50, 100, 500, 1000]
        performance_results = []
        
        for max_results in max_results_values:
            performance = self.measure_performance(
                asyncio.run,
                mock_server.search_files("test", max_results=max_results)
            )
            
            performance_results.append({
                'max_results': max_results,
                'execution_time': performance['execution_time'],
                'memory_usage': performance['memory_usage']
            })
        
        # Check that performance scales appropriately
        for i in range(1, len(performance_results)):
            prev = performance_results[i-1]
            curr = performance_results[i]
            
            # Execution time should generally increase with max_results
            # but not necessarily linearly due to internal optimizations
            assert curr['execution_time'] >= prev['execution_time'] * 0.5  # Should not be too much slower
    
    @pytest.mark.asyncio
    async def test_search_performance_error_handling(self, mock_server):
        """Test search performance with error conditions."""
        # Test with SDK unavailable
        mock_server.sdk_available = False
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        with pytest.raises(RuntimeError):
            await mock_server.search_files("test")
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        # Error handling should be fast
        assert execution_time < 0.1  # Should complete in less than 0.1 seconds
        assert memory_usage < 1024 * 1024  # Should use less than 1MB
    
    @pytest.mark.asyncio
    async def test_search_performance_timeout_handling(self, mock_server):
        """Test search performance with timeout handling."""
        # Mock a slow search
        async def slow_search(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate slow search
            return []
        
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = slow_search
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = await mock_server.search_files("test")
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        # Check that search completed within reasonable time
        assert execution_time < 0.2  # Should complete in less than 0.2 seconds
        assert memory_usage < 1024 * 1024  # Should use less than 1MB
        assert result['total_count'] == 0
    
    @pytest.mark.asyncio
    async def test_search_performance_result_processing(self, mock_server, medium_dataset):
        """Test search performance with result processing."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = await mock_server.search_files("test", max_results=1000)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        # Check performance metrics
        assert execution_time < 2.0  # Should complete in less than 2 seconds
        assert memory_usage < 5 * 1024 * 1024  # Should use less than 5MB
        
        # Check result processing
        assert result['total_count'] == 1000
        assert len(result['results']) == 1000
        
        # Check that all results have proper formatting
        for item in result['results']:
            assert 'name' in item
            assert 'path' in item
            assert 'size' in item
            assert 'modified' in item
            assert 'extension' in item
            assert 'is_directory' in item
    
    @pytest.mark.asyncio
    async def test_search_performance_logging_overhead(self, mock_server, medium_dataset):
        """Test search performance with logging overhead."""
        # Mock search results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=medium_dataset)
        
        # Enable logging
        with patch.object(mock_server.logger, 'info') as mock_log:
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            result = await mock_server.search_files("test", max_results=1000)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            # Check performance metrics
            assert execution_time < 2.0  # Should complete in less than 2 seconds
            assert memory_usage < 5 * 1024 * 1024  # Should use less than 5MB
            
            # Check that logging was called
            mock_log.assert_called()
            
            # Check that result is still correct
            assert result['total_count'] == 1000
            assert len(result['results']) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])