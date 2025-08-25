#!/usr/bin/env python3
"""
Unit Tests for Search Functionality

This module contains unit tests for the search functionality of the Everything Search MCP Server.
Tests cover various search patterns, wildcards, regex, case sensitivity, and edge cases.

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

# Add the src directory to the Python path
sys_path = str(Path(__file__).parent.parent.parent / "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from everything_search_mcp_server import EverythingSearchMCPServer


class TestSearchFunctionality:
    """Test suite for search functionality."""
    
    @pytest.fixture
    def mock_server(self):
        """Create a mock server instance for testing."""
        with patch('everything_search_mcp_server.everything_sdk') as mock_sdk:
            # Mock SDK availability
            mock_sdk.initialize = Mock()
            mock_sdk.search = Mock(return_value=[
                {'name': 'test.txt', 'path': 'C:\\test\\test.txt', 'size': 1024, 
                 'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False},
                {'name': 'test.py', 'path': 'C:\\test\\test.py', 'size': 2048, 
                 'modified': '2023-01-02T00:00:00', 'extension': 'py', 'is_directory': False}
            ])
            
            # Create server instance with mocked SDK
            server = EverythingSearchMCPServer()
            server.sdk_available = True
            server.sdk_path = "C:\\Everything64.dll"
            
            return server
    
    @pytest.mark.asyncio
    async def test_search_files_basic(self, mock_server):
        """Test basic file search functionality."""
        result = await mock_server.search_files("test", max_results=10)
        
        assert result['query'] == "test"
        assert result['total_count'] == 2
        assert len(result['results']) == 2
        assert result['results'][0]['name'] == 'test.txt'
        assert result['results'][1]['name'] == 'test.py'
        assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_search_files_empty_result(self, mock_server):
        """Test search with no results."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[])
        
        result = await mock_server.search_files("nonexistent")
        
        assert result['query'] == "nonexistent"
        assert result['total_count'] == 0
        assert len(result['results']) == 0
    
    @pytest.mark.asyncio
    async def test_search_files_sdk_unavailable(self, mock_server):
        """Test search when SDK is unavailable."""
        mock_server.sdk_available = False
        
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            await mock_server.search_files("test")
    
    @pytest.mark.asyncio
    async def test_search_files_with_wildcards(self, mock_server):
        """Test search with wildcard patterns."""
        # Mock wildcard search
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'test_file.txt', 'path': 'C:\\test\\test_file.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False},
            {'name': 'test_data.csv', 'path': 'C:\\test\\test_data.csv', 'size': 2048, 
             'modified': '2023-01-02T00:00:00', 'extension': 'csv', 'is_directory': False}
        ])
        
        result = await mock_server.search_files("test_*", max_results=10)
        
        assert result['total_count'] == 2
        assert result['results'][0]['name'] == 'test_file.txt'
        assert result['results'][1]['name'] == 'test_data.csv'
    
    @pytest.mark.asyncio
    async def test_search_files_with_regex(self, mock_server):
        """Test search with regex patterns."""
        # Mock regex search
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'file1.txt', 'path': 'C:\\test\\file1.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False},
            {'name': 'file2.txt', 'path': 'C:\\test\\file2.txt', 'size': 2048, 
             'modified': '2023-01-02T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        result = await mock_server.search_files_advanced(
            r"file\d+\.txt", 
            max_results=10, 
            regex=True
        )
        
        assert result['total_count'] == 2
        assert result['options']['regex'] is True
        assert result['results'][0]['name'] == 'file1.txt'
        assert result['results'][1]['name'] == 'file2.txt'
    
    @pytest.mark.asyncio
    async def test_search_files_case_sensitivity(self, mock_server):
        """Test case sensitive search."""
        # Mock case sensitive search
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'TestFile.txt', 'path': 'C:\\test\\TestFile.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        result = await mock_server.search_files_advanced(
            "testfile", 
            max_results=10, 
            case_sensitive=True
        )
        
        assert result['total_count'] == 0  # Should find no results due to case sensitivity
        
        # Test case insensitive
        result = await mock_server.search_files_advanced(
            "testfile", 
            max_results=10, 
            case_sensitive=False
        )
        
        assert result['total_count'] == 1
        assert result['options']['case_sensitive'] is False
    
    @pytest.mark.asyncio
    async def test_search_files_whole_word(self, mock_server):
        """Test whole word search."""
        # Mock whole word search
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'test.txt', 'path': 'C:\\test\\test.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        result = await mock_server.search_files_advanced(
            "test", 
            max_results=10, 
            whole_word=True
        )
        
        assert result['total_count'] == 1
        assert result['options']['whole_word'] is True
    
    @pytest.mark.asyncio
    async def test_search_files_advanced_options_reset(self, mock_server):
        """Test that search options are properly reset after search."""
        # Mock the SDK methods to track calls
        mock_sdk = mock_server._EverythingSearchMCPServer__dict__['everything_sdk']
        mock_sdk.set_case_sensitive = Mock()
        mock_sdk.set_whole_word = Mock()
        mock_sdk.set_regex = Mock()
        
        await mock_server.search_files_advanced(
            "test", 
            max_results=10, 
            case_sensitive=True, 
            whole_word=True, 
            regex=True
        )
        
        # Verify options were set
        mock_sdk.set_case_sensitive.assert_called_with(True)
        mock_sdk.set_whole_word.assert_called_with(True)
        mock_sdk.set_regex.assert_called_with(True)
        
        # Verify options were reset
        mock_sdk.set_case_sensitive.assert_called_with(False)
        mock_sdk.set_whole_word.assert_called_with(False)
        mock_sdk.set_regex.assert_called_with(False)
    
    @pytest.mark.asyncio
    async def test_search_files_max_results_limit(self, mock_server):
        """Test max results limit enforcement."""
        # Mock search returning more results than limit
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': f'file{i}.txt', 'path': f'C:\\test\\file{i}.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
            for i in range(15)  # Return 15 results
        ])
        
        result = await mock_server.search_files("test", max_results=10)
        
        assert result['total_count'] == 10
        assert len(result['results']) == 10
    
    @pytest.mark.asyncio
    async def test_search_files_error_handling(self, mock_server):
        """Test error handling in search functionality."""
        # Mock SDK to raise an exception
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(side_effect=Exception("Search failed"))
        
        with pytest.raises(Exception, match="Search failed"):
            await mock_server.search_files("test")
    
    @pytest.mark.asyncio
    async def test_search_files_result_formatting(self, mock_server):
        """Test result formatting consistency."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'test.txt', 'path': 'C:\\test\\test.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        result = await mock_server.search_files("test")
        
        # Check all required fields are present
        result_item = result['results'][0]
        required_fields = ['name', 'path', 'size', 'modified', 'extension', 'is_directory']
        
        for field in required_fields:
            assert field in result_item
            assert result_item[field] is not None
    
    @pytest.mark.asyncio
    async def test_search_files_directory_results(self, mock_server):
        """Test handling of directory results."""
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'test_dir', 'path': 'C:\\test\\test_dir', 'size': 0, 
             'modified': '2023-01-01T00:00:00', 'extension': '', 'is_directory': True}
        ])
        
        result = await mock_server.search_files("test")
        
        assert result['total_count'] == 1
        assert result['results'][0]['is_directory'] is True
        assert result['results'][0]['extension'] == ''


if __name__ == "__main__":
    pytest.main([__file__, "-v"])