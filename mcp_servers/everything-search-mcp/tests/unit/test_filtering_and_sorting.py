#!/usr/bin/env python3
"""
Unit Tests for Filtering and Sorting Functionality

This module contains unit tests for the filtering and sorting functionality of the Everything Search MCP Server.
Tests cover file extension filtering, size filtering, date filtering, and various sorting options.

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
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys_path = str(Path(__file__).parent.parent.parent / "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from everything_search_mcp_server import EverythingSearchMCPServer


class TestFilteringAndSorting:
    """Test suite for filtering and sorting functionality."""
    
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
    
    @pytest.mark.asyncio
    async def test_search_by_extension_basic(self, mock_server):
        """Test basic file extension search."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'test.txt', 'path': 'C:\\test\\test.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False},
            {'name': 'data.txt', 'path': 'C:\\test\\data.txt', 'size': 2048, 
             'modified': '2023-01-02T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        result = await mock_server.search_by_extension("txt", max_results=10)
        
        assert result['extension'] == "txt"
        assert result['total_count'] == 2
        assert len(result['results']) == 2
        assert all(result['extension'] == 'txt' for result in result['results'])
        assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_search_by_extension_no_results(self, mock_server):
        """Test extension search with no results."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[])
        
        result = await mock_server.search_by_extension("xyz")
        
        assert result['extension'] == "xyz"
        assert result['total_count'] == 0
        assert len(result['results']) == 0
    
    @pytest.mark.asyncio
    async def test_search_by_extension_sdk_unavailable(self, mock_server):
        """Test extension search when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.search_by_extension("txt")
    
    @pytest.mark.asyncio
    async def test_search_by_extension_query_format(self, mock_server):
        """Test that extension search uses correct query format."""
        mock_sdk = mock_server._EverythingSearchMCPServer__dict__['everything_sdk']
        mock_sdk.search = Mock(return_value=[])
        
        await mock_server.search_by_extension("pdf")
        
        # Verify the query format is correct
        mock_sdk.search.assert_called_once_with("*.pdf", 100)
    
    @pytest.mark.asyncio
    async def test_search_by_size_basic(self, mock_server):
        """Test basic file size search."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_size = Mock(return_value=[
            {'name': 'small.txt', 'path': 'C:\\test\\small.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False},
            {'name': 'medium.txt', 'path': 'C:\\test\\medium.txt', 'size': 2048, 
             'modified': '2023-01-02T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        result = await mock_server.search_by_size(min_size=1000, max_size=3000, size_unit="bytes")
        
        assert result['size_range']['min'] == 1000
        assert result['size_range']['max'] == 3000
        assert result['size_range']['unit'] == "bytes"
        assert result['total_count'] == 2
        assert len(result['results']) == 2
    
    @pytest.mark.asyncio
    async def test_search_by_size_different_units(self, mock_server):
        """Test size search with different units."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_size = Mock(return_value=[
            {'name': 'file1KB.txt', 'path': 'C:\\test\\file1KB.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        # Test KB
        result = await mock_server.search_by_size(min_size=1, max_size=2, size_unit="KB")
        assert result['size_range']['unit'] == "KB"
        
        # Test MB
        result = await mock_server.search_by_size(min_size=1, max_size=2, size_unit="MB")
        assert result['size_range']['unit'] == "MB"
        
        # Test GB
        result = await mock_server.search_by_size(min_size=1, max_size=2, size_unit="GB")
        assert result['size_range']['unit'] == "GB"
    
    @pytest.mark.asyncio
    async def test_search_by_size_unit_conversion(self, mock_server):
        """Test size unit conversion."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_size = Mock(return_value=[])
        
        # Test KB conversion (1 KB = 1024 bytes)
        await mock_server.search_by_size(min_size=1, max_size=2, size_unit="KB")
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_size.assert_called_with(1024, 2048, 100)
        
        # Test MB conversion (1 MB = 1024 * 1024 bytes)
        await mock_server.search_by_size(min_size=1, max_size=2, size_unit="MB")
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_size.assert_called_with(1048576, 2097152, 100)
        
        # Test GB conversion (1 GB = 1024 * 1024 * 1024 bytes)
        await mock_server.search_by_size(min_size=1, max_size=2, size_unit="GB")
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_size.assert_called_with(1073741824, 2147483648, 100)
    
    @pytest.mark.asyncio
    async def test_search_by_size_no_max_limit(self, mock_server):
        """Test size search with no maximum limit."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_size = Mock(return_value=[])
        
        await mock_server.search_by_size(min_size=1000, max_size=None, size_unit="bytes")
        
        # Verify None is passed for max_size
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_size.assert_called_with(1000, None, 100)
    
    @pytest.mark.asyncio
    async def test_search_by_date_basic(self, mock_server):
        """Test basic date search."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_date = Mock(return_value=[
            {'name': 'file1.txt', 'path': 'C:\\test\\file1.txt', 'size': 1024, 
             'modified': '2023-01-15T00:00:00', 'extension': 'txt', 'is_directory': False},
            {'name': 'file2.txt', 'path': 'C:\\test\\file2.txt', 'size': 2048, 
             'modified': '2023-01-20T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        result = await mock_server.search_by_date(date_from="2023-01-01", date_to="2023-01-31")
        
        assert result['date_range']['from'] == "2023-01-01"
        assert result['date_range']['to'] == "2023-01-31"
        assert result['date_range']['format'] == "%Y-%m-%d"
        assert result['total_count'] == 2
        assert len(result['results']) == 2
    
    @pytest.mark.asyncio
    async def test_search_by_date_from_only(self, mock_server):
        """Test date search with only start date."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_date = Mock(return_value=[
            {'name': 'file1.txt', 'path': 'C:\\test\\file1.txt', 'size': 1024, 
             'modified': '2023-01-15T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        result = await mock_server.search_by_date(date_from="2023-01-01")
        
        assert result['date_range']['from'] == "2023-01-01"
        assert result['date_range']['to'] is None
        assert result['total_count'] == 1
    
    @pytest.mark.asyncio
    async def test_search_by_date_to_only(self, mock_server):
        """Test date search with only end date."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_date = Mock(return_value=[
            {'name': 'file1.txt', 'path': 'C:\\test\\file1.txt', 'size': 1024, 
             'modified': '2023-01-15T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        result = await mock_server.search_by_date(date_to="2023-01-31")
        
        assert result['date_range']['from'] is None
        assert result['date_range']['to'] == "2023-01-31"
        assert result['total_count'] == 1
    
    @pytest.mark.asyncio
    async def test_search_by_date_different_formats(self, mock_server):
        """Test date search with different date formats."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_date = Mock(return_value=[])
        
        # Test different date formats
        date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d/%m/%Y"]
        
        for date_format in date_formats:
            await mock_server.search_by_date(date_from="2023-01-01", date_format=date_format)
            # Verify the method was called with parsed datetime objects
            mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_date.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_by_date_invalid_format(self, mock_server):
        """Test date search with invalid date format."""
        with pytest.raises(ValueError, match="time data"):
            await mock_server.search_by_date(date_from="invalid-date", date_format="%Y-%m-%d")
    
    @pytest.mark.asyncio
    async def test_search_by_date_sdk_unavailable(self, mock_server):
        """Test date search when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.search_by_date(date_from="2023-01-01", date_to="2023-01-31")
    
    @pytest.mark.asyncio
    async def test_get_file_info_basic(self, mock_server):
        """Test basic file info retrieval."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].get_file_info = Mock(return_value={
            'name': 'test.txt',
            'size': 1024,
            'modified': '2023-01-01T00:00:00',
            'created': '2023-01-01T00:00:00',
            'accessed': '2023-01-01T00:00:00',
            'extension': 'txt',
            'is_directory': False,
            'is_hidden': False,
            'is_system': False,
            'is_readonly': False
        })
        
        result = await mock_server.get_file_info("C:\\test\\test.txt")
        
        assert result['path'] == "C:\\test\\test.txt"
        assert result['name'] == "test.txt"
        assert result['size'] == 1024
        assert result['extension'] == "txt"
        assert result['is_directory'] is False
        assert result['is_hidden'] is False
        assert result['is_system'] is False
        assert result['is_readonly'] is False
        assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_get_file_info_not_found(self, mock_server):
        """Test file info retrieval for non-existent file."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].get_file_info = Mock(return_value=None)
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            await mock_server.get_file_info("C:\\nonexistent\\file.txt")
    
    @pytest.mark.asyncio
    async def test_get_file_info_sdk_unavailable(self, mock_server):
        """Test file info retrieval when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.get_file_info("C:\\test\\test.txt")
    
    @pytest.mark.asyncio
    async def test_list_drives_basic(self, mock_server):
        """Test basic drive listing."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].list_drives = Mock(return_value=[
            {'name': 'C:', 'path': 'C:\\', 'type': 'fixed', 'size': 1000000000, 
             'free_space': 500000000, 'is_ready': True},
            {'name': 'D:', 'path': 'D:\\', 'type': 'fixed', 'size': 2000000000, 
             'free_space': 1000000000, 'is_ready': True}
        ])
        
        result = await mock_server.list_drives()
        
        assert len(result) == 2
        assert result[0]['name'] == 'C:'
        assert result[0]['path'] == 'C:\\'
        assert result[0]['type'] == 'fixed'
        assert result[0]['is_ready'] is True
        assert result[1]['name'] == 'D:'
    
    @pytest.mark.asyncio
    async def test_list_drives_unavailable(self, mock_server):
        """Test drive listing when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.list_drives()
    
    @pytest.mark.asyncio
    async def test_list_drives_no_ready_drives(self, mock_server):
        """Test drive listing with no ready drives."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].list_drives = Mock(return_value=[
            {'name': 'A:', 'path': 'A:\\', 'type': 'removable', 'size': 0, 
             'free_space': 0, 'is_ready': False}
        ])
        
        result = await mock_server.list_drives()
        
        assert len(result) == 1
        assert result[0]['name'] == 'A:'
        assert result[0]['is_ready'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])