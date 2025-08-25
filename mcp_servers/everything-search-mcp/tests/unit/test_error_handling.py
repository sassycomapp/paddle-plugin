#!/usr/bin/env python3
"""
Unit Tests for Error Handling

This module contains unit tests for error handling in the Everything Search MCP Server.
Tests cover various error scenarios including missing SDK, invalid patterns, permission issues, and edge cases.

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
from datetime import datetime

# Add the src directory to the Python path
sys_path = str(Path(__file__).parent.parent.parent / "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from everything_search_mcp_server import EverythingSearchMCPServer


class TestErrorHandling:
    """Test suite for error handling functionality."""
    
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
    async def test_search_files_sdk_unavailable(self, mock_server):
        """Test search when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.search_files("test")
    
    @pytest.mark.asyncio
    async def test_search_files_advanced_sdk_unavailable(self, mock_server):
        """Test advanced search when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.search_files_advanced("test", case_sensitive=True)
    
    @pytest.mark.asyncio
    async def test_get_file_info_sdk_unavailable(self, mock_server):
        """Test file info retrieval when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.get_file_info("C:\\test\\file.txt")
    
    @pytest.mark.asyncio
    async def test_list_drives_sdk_unavailable(self, mock_server):
        """Test drive listing when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.list_drives()
    
    @pytest.mark.asyncio
    async def test_search_by_extension_sdk_unavailable(self, mock_server):
        """Test extension search when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.search_by_extension("txt")
    
    @pytest.mark.asyncio
    async def test_search_by_size_sdk_unavailable(self, mock_server):
        """Test size search when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.search_by_size(min_size=1000, max_size=2000)
    
    @pytest.mark.asyncio
    async def test_search_by_date_sdk_unavailable(self, mock_server):
        """Test date search when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.search_by_date(date_from="2023-01-01", date_to="2023-01-31")
    
    @pytest.mark.asyncio
    async def test_get_file_info_file_not_found(self, mock_server):
        """Test file info retrieval for non-existent file."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].get_file_info = Mock(return_value=None)
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            await mock_server.get_file_info("C:\\nonexistent\\file.txt")
    
    @pytest.mark.asyncio
    async def test_search_files_sdk_exception(self, mock_server):
        """Test search when SDK raises an exception."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(side_effect=Exception("SDK Error"))
        
        with pytest.raises(Exception, match="SDK Error"):
            await mock_server.search_files("test")
    
    @pytest.mark.asyncio
    async def test_search_files_advanced_sdk_exception(self, mock_server):
        """Test advanced search when SDK raises an exception."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(side_effect=Exception("SDK Error"))
        
        with pytest.raises(Exception, match="SDK Error"):
            await mock_server.search_files_advanced("test", case_sensitive=True)
    
    @pytest.mark.asyncio
    async def test_get_file_info_sdk_exception(self, mock_server):
        """Test file info retrieval when SDK raises an exception."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].get_file_info = Mock(side_effect=Exception("SDK Error"))
        
        with pytest.raises(Exception, match="SDK Error"):
            await mock_server.get_file_info("C:\\test\\file.txt")
    
    @pytest.mark.asyncio
    async def test_list_drives_sdk_exception(self, mock_server):
        """Test drive listing when SDK raises an exception."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].list_drives = Mock(side_effect=Exception("SDK Error"))
        
        with pytest.raises(Exception, match="SDK Error"):
            await mock_server.list_drives()
    
    @pytest.mark.asyncio
    async def test_search_by_extension_sdk_exception(self, mock_server):
        """Test extension search when SDK raises an exception."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(side_effect=Exception("SDK Error"))
        
        with pytest.raises(Exception, match="SDK Error"):
            await mock_server.search_by_extension("txt")
    
    @pytest.mark.asyncio
    async def test_search_by_size_sdk_exception(self, mock_server):
        """Test size search when SDK raises an exception."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_size = Mock(side_effect=Exception("SDK Error"))
        
        with pytest.raises(Exception, match="SDK Error"):
            await mock_server.search_by_size(min_size=1000, max_size=2000)
    
    @pytest.mark.asyncio
    async def test_search_by_date_sdk_exception(self, mock_server):
        """Test date search when SDK raises an exception."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search_by_date = Mock(side_effect=Exception("SDK Error"))
        
        with pytest.raises(Exception, match="SDK Error"):
            await mock_server.search_by_date(date_from="2023-01-01", date_to="2023-01-31")
    
    @pytest.mark.asyncio
    async def test_search_files_invalid_max_results(self, mock_server):
        """Test search with invalid max results parameter."""
        # Test with negative max results
        with pytest.raises(ValueError):
            await mock_server.search_files("test", max_results=-1)
        
        # Test with zero max results
        with pytest.raises(ValueError):
            await mock_server.search_files("test", max_results=0)
        
        # Test with very large max results
        with pytest.raises(ValueError):
            await mock_server.search_files("test", max_results=1000000)
    
    @pytest.mark.asyncio
    async def test_search_files_advanced_invalid_parameters(self, mock_server):
        """Test advanced search with invalid parameters."""
        # Test with empty query
        with pytest.raises(ValueError):
            await mock_server.search_files_advanced("", case_sensitive=True)
        
        # Test with None query
        with pytest.raises(ValueError):
            await mock_server.search_files_advanced(None, case_sensitive=True)
        
        # Test with invalid max results
        with pytest.raises(ValueError):
            await mock_server.search_files_advanced("test", max_results=-1)
    
    @pytest.mark.asyncio
    async def test_search_by_extension_invalid_parameters(self, mock_server):
        """Test extension search with invalid parameters."""
        # Test with empty extension
        with pytest.raises(ValueError):
            await mock_server.search_by_extension("")
        
        # Test with None extension
        with pytest.raises(ValueError):
            await mock_server.search_by_extension(None)
        
        # Test with invalid max results
        with pytest.raises(ValueError):
            await mock_server.search_by_extension("txt", max_results=-1)
    
    @pytest.mark.asyncio
    async def test_search_by_size_invalid_parameters(self, mock_server):
        """Test size search with invalid parameters."""
        # Test with negative min size
        with pytest.raises(ValueError):
            await mock_server.search_by_size(min_size=-1, max_size=1000)
        
        # Test with min size > max size
        with pytest.raises(ValueError):
            await mock_server.search_by_size(min_size=2000, max_size=1000)
        
        # Test with invalid size unit
        with pytest.raises(ValueError):
            await mock_server.search_by_size(min_size=1000, max_size=2000, size_unit="invalid")
        
        # Test with invalid max results
        with pytest.raises(ValueError):
            await mock_server.search_by_size(min_size=1000, max_size=2000, max_results=-1)
    
    @pytest.mark.asyncio
    async def test_search_by_date_invalid_parameters(self, mock_server):
        """Test date search with invalid parameters."""
        # Test with invalid date format
        with pytest.raises(ValueError):
            await mock_server.search_by_date(date_from="invalid-date", date_format="%Y-%m-%d")
        
        # Test with invalid date range (from > to)
        with pytest.raises(ValueError):
            await mock_server.search_by_date(date_from="2023-01-02", date_to="2023-01-01")
        
        # Test with invalid max results
        with pytest.raises(ValueError):
            await mock_server.search_by_date(date_from="2023-01-01", date_to="2023-01-31", max_results=-1)
    
    @pytest.mark.asyncio
    async def test_get_file_info_invalid_parameters(self, mock_server):
        """Test file info retrieval with invalid parameters."""
        # Test with empty file path
        with pytest.raises(ValueError):
            await mock_server.get_file_info("")
        
        # Test with None file path
        with pytest.raises(ValueError):
            await mock_server.get_file_info(None)
        
        # Test with invalid file path
        with pytest.raises(ValueError):
            await mock_server.get_file_info("invalid/path")
    
    @pytest.mark.asyncio
    async def test_list_drives_invalid_parameters(self, mock_server):
        """Test drive listing with invalid parameters."""
        # This test is mainly for completeness, as list_drives doesn't take parameters
        # But we can test that it doesn't raise exceptions with valid calls
        try:
            await mock_server.list_drives()
        except Exception as e:
            pytest.fail(f"list_drives should not raise exceptions: {e}")
    
    @pytest.mark.asyncio
    async def test_search_files_timeout_handling(self, mock_server):
        """Test search timeout handling."""
        # Mock a slow search
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(
            side_effect=asyncio.TimeoutError("Search timeout")
        )
        
        with pytest.raises(TimeoutError, match="Search timeout"):
            await mock_server.search_files("test")
    
    @pytest.mark.asyncio
    async def test_search_files_memory_error(self, mock_server):
        """Test search memory error handling."""
        # Mock a memory error
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(
            side_effect=MemoryError("Insufficient memory")
        )
        
        with pytest.raises(MemoryError, match="Insufficient memory"):
            await mock_server.search_files("test")
    
    @pytest.mark.asyncio
    async def test_search_files_io_error(self, mock_server):
        """Test search I/O error handling."""
        # Mock an I/O error
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(
            side_effect=OSError("Disk I/O error")
        )
        
        with pytest.raises(OSError, match="Disk I/O error"):
            await mock_server.search_files("test")
    
    @pytest.mark.asyncio
    async def test_search_files_unicode_error(self, mock_server):
        """Test search Unicode error handling."""
        # Mock a Unicode error
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(
            side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "Invalid UTF-8")
        )
        
        with pytest.raises(UnicodeDecodeError, match="Invalid UTF-8"):
            await mock_server.search_files("test")
    
    @pytest.mark.asyncio
    async def test_search_files_permission_error(self, mock_server):
        """Test search permission error handling."""
        # Mock a permission error
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(
            side_effect=PermissionError("Access denied")
        )
        
        with pytest.raises(PermissionError, match="Access denied"):
            await mock_server.search_files("C:\\restricted\\path")
    
    @pytest.mark.asyncio
    async def test_search_files_keyboard_interrupt(self, mock_server):
        """Test search keyboard interrupt handling."""
        # Mock a keyboard interrupt
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(
            side_effect=KeyboardInterrupt("Search interrupted by user")
        )
        
        with pytest.raises(KeyboardInterrupt, match="Search interrupted by user"):
            await mock_server.search_files("test")
    
    @pytest.mark.asyncio
    async def test_search_files_general_exception(self, mock_server):
        """Test search general exception handling."""
        # Mock a general exception
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(
            side_effect=Exception("Unexpected error")
        )
        
        with pytest.raises(Exception, match="Unexpected error"):
            await mock_server.search_files("test")
    
    @pytest.mark.asyncio
    async def test_search_files_result_processing_error(self, mock_server):
        """Test search result processing error handling."""
        # Mock search returning invalid results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'test.txt', 'path': 'C:\\test\\test.txt', 'size': 'invalid',  # Invalid size type
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        # Should handle invalid result data gracefully
        result = await mock_server.search_files("test")
        
        # Should still return a result, but with error handling
        assert result['query'] == "test"
        assert result['total_count'] == 1
        assert 'results' in result
    
    @pytest.mark.asyncio
    async def test_search_files_empty_result_handling(self, mock_server):
        """Test search with empty result handling."""
        # Mock search returning empty results
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[])
        
        result = await mock_server.search_files("nonexistent")
        
        assert result['query'] == "nonexistent"
        assert result['total_count'] == 0
        assert len(result['results']) == 0
        assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_search_files_partial_result_handling(self, mock_server):
        """Test search with partial result handling."""
        # Mock search returning partial results (missing some fields)
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'test.txt', 'path': 'C:\\test\\test.txt'},  # Missing some fields
        ])
        
        result = await mock_server.search_files("test")
        
        assert result['query'] == "test"
        assert result['total_count'] == 1
        assert len(result['results']) == 1
        assert 'timestamp' in result
        
        # Check that missing fields are handled gracefully
        result_item = result['results'][0]
        assert 'name' in result_item
        assert 'path' in result_item
        # Missing fields should have default values or be None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])