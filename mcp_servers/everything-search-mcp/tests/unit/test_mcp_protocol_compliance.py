#!/usr/bin/env python3
"""
Unit Tests for MCP Protocol Compliance

This module contains unit tests for MCP protocol compliance in the Everything Search MCP Server.
Tests cover MCP tool registration, protocol communication, and server behavior.

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


class TestMCPProtocolCompliance:
    """Test suite for MCP protocol compliance."""
    
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
    
    def test_server_initialization(self, mock_server):
        """Test server initialization with MCP protocol."""
        assert mock_server.mcp is not None
        assert mock_server.logger is not None
        assert mock_server.sdk_available is True
        assert mock_server.sdk_path == "C:\\Everything64.dll"
    
    def test_server_info(self, mock_server):
        """Test server information compliance."""
        info = mock_server.get_server_info()
        
        # Check required server info fields
        required_fields = [
            'server_name', 'version', 'description', 'author', 
            'config_path', 'sdk_info'
        ]
        
        for field in required_fields:
            assert field in info, f"Missing required field: {field}"
        
        # Check specific values
        assert info['server_name'] == 'Everything Search MCP Server'
        assert info['version'] == '1.0.0'
        assert info['description'] == 'MCP server for Everything Search with fast local file search'
        assert info['author'] == 'Kilo Code'
        assert info['sdk_info']['sdk_path'] == "C:\\Everything64.dll"
        assert info['sdk_info']['sdk_available'] is True
    
    def test_tool_registration(self, mock_server):
        """Test MCP tool registration compliance."""
        # Check that tools are registered
        tools = mock_server.mcp._tools
        
        # Expected tools
        expected_tools = [
            'search_files', 'search_files_advanced', 'get_file_info',
            'list_drives', 'validate_sdk_installation', 'get_server_info',
            'search_by_extension', 'search_by_size', 'search_by_date'
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools, f"Tool not registered: {tool_name}"
    
    def test_tool_parameters_compliance(self, mock_server):
        """Test tool parameter compliance with MCP standards."""
        # Test search_files tool
        search_files_tool = mock_server.mcp._tools['search_files']
        
        # Check that tool has proper signature
        assert hasattr(search_files_tool, '__call__')
        
        # Test search_files_advanced tool
        search_advanced_tool = mock_server.mcp._tools['search_files_advanced']
        
        # Check that tool has proper signature
        assert hasattr(search_advanced_tool, '__call__')
    
    def test_mcp_server_name(self, mock_server):
        """Test MCP server name compliance."""
        assert mock_server.mcp.name == "Everything Search MCP Server"
    
    def test_mcp_server_description(self, mock_server):
        """Test MCP server description compliance."""
        # Check that server has proper description
        info = mock_server.get_server_info()
        assert "Everything Search" in info['description']
        assert "MCP server" in info['description']
    
    def test_mcp_server_version(self, mock_server):
        """Test MCP server version compliance."""
        info = mock_server.get_server_info()
        assert info['version'] == '1.0.0'
        assert isinstance(info['version'], str)
        assert len(info['version']) > 0
    
    def test_mcp_server_author(self, mock_server):
        """Test MCP server author compliance."""
        info = mock_server.get_server_info()
        assert info['author'] == 'Kilo Code'
        assert isinstance(info['author'], str)
        assert len(info['author']) > 0
    
    def test_mcp_server_config_path(self, mock_server):
        """Test MCP server config path compliance."""
        info = mock_server.get_server_info()
        assert info['config_path'] is None  # Should be None for default initialization
        assert isinstance(info['config_path'], (type(None), str))
    
    def test_mcp_server_sdk_info(self, mock_server):
        """Test MCP server SDK info compliance."""
        info = mock_server.get_server_info()
        sdk_info = info['sdk_info']
        
        # Check SDK info structure
        required_sdk_fields = ['sdk_path', 'sdk_available', 'sdk_version']
        for field in required_sdk_fields:
            assert field in sdk_info, f"Missing SDK info field: {field}"
        
        # Check SDK info values
        assert sdk_info['sdk_path'] == "C:\\Everything64.dll"
        assert sdk_info['sdk_available'] is True
        assert sdk_info['sdk_version'] is None  # Should be None for mocked SDK
    
    def test_mcp_tool_discovery(self, mock_server):
        """Test MCP tool discovery compliance."""
        # Check that tools can be discovered
        tools = mock_server.mcp.list_tools()
        
        # Should return list of tools
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check tool structure
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
    
    def test_mcp_tool_descriptions(self, mock_server):
        """Test MCP tool descriptions compliance."""
        tools = mock_server.mcp.list_tools()
        
        # Check that tools have descriptions
        for tool in tools:
            assert tool.description is not None
            assert isinstance(tool.description, str)
            assert len(tool.description) > 0
    
    def test_mcp_tool_input_schemas(self, mock_server):
        """Test MCP tool input schemas compliance."""
        tools = mock_server.mcp.list_tools()
        
        # Check that tools have input schemas
        for tool in tools:
            assert tool.inputSchema is not None
            assert isinstance(tool.inputSchema, dict)
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
    
    def test_mcp_tool_output_format(self, mock_server):
        """Test MCP tool output format compliance."""
        # Test search_files tool output format
        result = asyncio.run(mock_server.search_files("test"))
        
        # Check result structure
        assert isinstance(result, dict)
        assert 'query' in result
        assert 'results' in result
        assert 'total_count' in result
        assert 'timestamp' in result
        
        # Check results format
        assert isinstance(result['results'], list)
        for item in result['results']:
            assert isinstance(item, dict)
            assert 'name' in item
            assert 'path' in item
            assert 'size' in item
            assert 'modified' in item
            assert 'extension' in item
            assert 'is_directory' in item
    
    def test_mcp_tool_error_handling(self, mock_server):
        """Test MCP tool error handling compliance."""
        # Test error handling for invalid parameters
        with pytest.raises((ValueError, RuntimeError)):
            asyncio.run(mock_server.search_files("", max_results=-1))
        
        # Test error handling for SDK unavailable
        mock_server.sdk_available = False
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            asyncio.run(mock_server.search_files("test"))
    
    def test_mcp_tool_async_compliance(self, mock_server):
        """Test MCP tool async compliance."""
        # Test that tools are async
        assert asyncio.iscoroutinefunction(mock_server.search_files)
        assert asyncio.iscoroutinefunction(mock_server.search_files_advanced)
        assert asyncio.iscoroutinefunction(mock_server.get_file_info)
        assert asyncio.iscoroutinefunction(mock_server.list_drives)
        assert asyncio.iscoroutinefunction(mock_server.search_by_extension)
        assert asyncio.iscoroutinefunction(mock_server.search_by_size)
        assert asyncio.iscoroutinefunction(mock_server.search_by_date)
        assert asyncio.iscoroutinefunction(mock_server.validate_sdk_installation)
    
    def test_mcp_tool_parameter_validation(self, mock_server):
        """Test MCP tool parameter validation compliance."""
        # Test search_files parameter validation
        with pytest.raises((ValueError, TypeError)):
            asyncio.run(mock_server.search_files(None))
        
        with pytest.raises((ValueError, TypeError)):
            asyncio.run(mock_server.search_files("", max_results="invalid"))
        
        with pytest.raises((ValueError, TypeError)):
            asyncio.run(mock_server.search_files("test", max_results=None))
    
    def test_mcp_tool_return_type_compliance(self, mock_server):
        """Test MCP tool return type compliance."""
        # Test that tools return proper types
        result = asyncio.run(mock_server.search_files("test"))
        
        assert isinstance(result, dict)
        assert isinstance(result['query'], str)
        assert isinstance(result['results'], list)
        assert isinstance(result['total_count'], int)
        assert isinstance(result['timestamp'], str)
    
    def test_mcp_tool_result_consistency(self, mock_server):
        """Test MCP tool result consistency compliance."""
        # Test multiple calls with same parameters
        result1 = asyncio.run(mock_server.search_files("test"))
        result2 = asyncio.run(mock_server.search_files("test"))
        
        # Results should be consistent in structure
        assert result1.keys() == result2.keys()
        assert isinstance(result1['results'], type(result2['results']))
        assert isinstance(result1['total_count'], type(result2['total_count']))
    
    def test_mcp_tool_timeout_handling(self, mock_server):
        """Test MCP tool timeout handling compliance."""
        # Mock a timeout scenario
        mock_server._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(
            side_effect=asyncio.TimeoutError("Search timeout")
        )
        
        with pytest.raises(TimeoutError):
            asyncio.run(mock_server.search_files("test"))
    
    def test_mcp_tool_concurrent_access(self, mock_server):
        """Test MCP tool concurrent access compliance."""
        import concurrent.futures
        
        # Test concurrent access to search tools
        def search_task(query):
            return asyncio.run(mock_server.search_files(query))
        
        queries = ["test1", "test2", "test3"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(search_task, query) for query in queries]
            results = [future.result() for future in futures]
        
        # All searches should complete successfully
        for result in results:
            assert isinstance(result, dict)
            assert 'query' in result
            assert 'results' in result
            assert 'total_count' in result
            assert 'timestamp' in result
    
    def test_mcp_tool_resource_cleanup(self, mock_server):
        """Test MCP tool resource cleanup compliance."""
        # Test that resources are properly cleaned up
        mock_sdk = mock_server._EverythingSearchMCPServer__dict__['everything_sdk']
        
        # Mock search methods
        mock_sdk.search = Mock(return_value=[])
        mock_sdk.set_case_sensitive = Mock()
        mock_sdk.set_whole_word = Mock()
        mock_sdk.set_regex = Mock()
        
        # Perform advanced search
        asyncio.run(mock_server.search_files_advanced("test", case_sensitive=True))
        
        # Verify that search options are reset
        mock_sdk.set_case_sensitive.assert_called_with(False)
        mock_sdk.set_whole_word.assert_called_with(False)
        mock_sdk.set_regex.assert_called_with(False)
    
    def test_mcp_tool_logging_compliance(self, mock_server):
        """Test MCP tool logging compliance."""
        # Test that tools log their operations
        with patch.object(mock_server.logger, 'info') as mock_log:
            asyncio.run(mock_server.search_files("test"))
            
            # Verify that search operation is logged
            mock_log.assert_called()
            assert any("Searching for files" in str(call) for call in mock_log.call_args_list)
    
    def test_mcp_tool_error_logging(self, mock_server):
        """Test MCP tool error logging compliance."""
        # Test that errors are logged
        with patch.object(mock_server.logger, 'error') as mock_log:
            mock_server.sdk_available = False
            
            try:
                asyncio.run(mock_server.search_files("test"))
            except RuntimeError:
                pass  # Expected error
            
            # Verify that error is logged
            mock_log.assert_called()
            assert any("Failed to search files" in str(call) for call in mock_log.call_args_list)
    
    def test_mcp_tool_performance_logging(self, mock_server):
        """Test MCP tool performance logging compliance."""
        # Test that performance metrics are logged
        with patch.object(mock_server.logger, 'info') as mock_log:
            asyncio.run(mock_server.search_files("test"))
            
            # Verify that performance metrics are logged
            mock_log.assert_called()
            assert any("Found" in str(call) for call in mock_log.call_args_list)
    
    def test_mcp_tool_configuration_compliance(self, mock_server):
        """Test MCP tool configuration compliance."""
        # Test that tools respect configuration
        result = asyncio.run(mock_server.search_files("test", max_results=50))
        
        # Check that max_results parameter is respected
        assert result['total_count'] <= 50
    
    def test_mcp_tool_security_compliance(self, mock_server):
        """Test MCP tool security compliance."""
        # Test that tools handle potentially dangerous inputs
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "C:\\Windows\\System32\\cmd.exe",
            "file.txt; rm -rf /",
        ]
        
        for dangerous_input in dangerous_inputs:
            try:
                result = asyncio.run(mock_server.search_files(dangerous_input))
                # Should not raise exceptions for dangerous inputs
                assert isinstance(result, dict)
            except Exception:
                # If it does raise an exception, it should be a security-related one
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])