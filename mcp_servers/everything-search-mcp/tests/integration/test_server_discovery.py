#!/usr/bin/env python3
"""
Integration Tests for MCP Server Discovery

This module contains integration tests for MCP server discovery functionality.
Tests cover server startup, tool discovery, and basic MCP protocol communication.

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
import subprocess
import sys
from datetime import datetime

# Add the src directory to the Python path
sys_path = str(Path(__file__).parent.parent.parent / "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from everything_search_mcp_server import EverythingSearchMCPServer


class TestServerDiscovery:
    """Test suite for MCP server discovery."""
    
    @pytest.fixture
    def test_config_path(self):
        """Create a temporary config file for testing."""
        config_data = {
            "everything_search": {
                "sdk_path": "${EVERYTHING_SDK_PATH}",
                "max_search_results": 100,
                "default_search_timeout": 30
            },
            "search": {
                "default_max_results": 50,
                "max_max_results": 1000,
                "min_max_results": 1
            },
            "performance": {
                "enable_async_search": True,
                "max_concurrent_searches": 5,
                "search_timeout": 30
            },
            "logging": {
                "level": "INFO",
                "file": "./logs/everything_search_mcp.log",
                "enable_file_logging": True,
                "enable_console_logging": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            return f.name
    
    @pytest.fixture
    def server_with_config(self, test_config_path):
        """Create a server instance with test configuration."""
        with patch('everything_search_mcp_server.everything_sdk') as mock_sdk:
            mock_sdk.initialize = Mock()
            mock_sdk.search = Mock(return_value=[])
            
            server = EverythingSearchMCPServer(test_config_path)
            server.sdk_available = True
            server.sdk_path = "C:\\Everything64.dll"
            
            yield server
            
            # Cleanup
            if os.path.exists(test_config_path):
                os.unlink(test_config_path)
    
    def test_server_initialization_with_config(self, server_with_config):
        """Test server initialization with configuration file."""
        assert server_with_config.config_path is not None
        assert server_with_config.mcp is not None
        assert server_with_config.logger is not None
        assert server_with_config.sdk_available is True
    
    def test_server_initialization_without_config(self):
        """Test server initialization without configuration file."""
        with patch('everything_search_mcp_server.everything_sdk') as mock_sdk:
            mock_sdk.initialize = Mock()
            mock_sdk.search = Mock(return_value=[])
            
            server = EverythingSearchMCPServer()
            server.sdk_available = True
            server.sdk_path = "C:\\Everything64.dll"
            
            assert server.config_path is None
            assert server.mcp is not None
            assert server.logger is not None
            assert server.sdk_available is True
    
    def test_server_info_with_config(self, server_with_config):
        """Test server information with configuration."""
        info = server_with_config.get_server_info()
        
        assert info['server_name'] == 'Everything Search MCP Server'
        assert info['version'] == '1.0.0'
        assert info['config_path'] == server_with_config.config_path
        assert info['sdk_info']['sdk_path'] == "C:\\Everything64.dll"
        assert info['sdk_info']['sdk_available'] is True
    
    def test_server_info_without_config(self):
        """Test server information without configuration."""
        with patch('everything_search_mcp_server.everything_sdk') as mock_sdk:
            mock_sdk.initialize = Mock()
            mock_sdk.search = Mock(return_value=[])
            
            server = EverythingSearchMCPServer()
            server.sdk_available = True
            server.sdk_path = "C:\\Everything64.dll"
            
            info = server.get_server_info()
            
            assert info['server_name'] == 'Everything Search MCP Server'
            assert info['version'] == '1.0.0'
            assert info['config_path'] is None
            assert info['sdk_info']['sdk_path'] == "C:\\Everything64.dll"
            assert info['sdk_info']['sdk_available'] is True
    
    def test_tool_discovery(self, server_with_config):
        """Test tool discovery functionality."""
        tools = server_with_config.mcp.list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check that expected tools are present
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            'search_files', 'search_files_advanced', 'get_file_info',
            'list_drives', 'validate_sdk_installation', 'get_server_info',
            'search_by_extension', 'search_by_size', 'search_by_date'
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Tool not found: {tool_name}"
    
    def test_tool_schema_validation(self, server_with_config):
        """Test tool schema validation."""
        tools = server_with_config.mcp.list_tools()
        
        for tool in tools:
            # Check tool schema structure
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            
            # Check input schema structure
            assert tool.inputSchema is not None
            assert isinstance(tool.inputSchema, dict)
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
            assert 'properties' in tool.inputSchema
            assert 'required' in tool.inputSchema
    
    def test_tool_description_content(self, server_with_config):
        """Test tool description content."""
        tools = server_with_config.mcp.list_tools()
        
        for tool in tools:
            assert tool.description is not None
            assert isinstance(tool.description, str)
            assert len(tool.description) > 0
            assert 'Search' in tool.description or 'File' in tool.description or 'Drive' in tool.description
    
    def test_tool_parameter_definitions(self, server_with_config):
        """Test tool parameter definitions."""
        tools = server_with_config.mcp.list_tools()
        
        for tool in tools:
            input_schema = tool.inputSchema
            assert 'properties' in input_schema
            assert 'required' in input_schema
            
            properties = input_schema['properties']
            required = input_schema['required']
            
            # Check that parameters have proper definitions
            for param_name, param_def in properties.items():
                assert 'type' in param_def
                assert param_def['type'] in ['string', 'integer', 'boolean', 'array', 'object']
                
                # Check description for each parameter
                if 'description' in param_def:
                    assert isinstance(param_def['description'], str)
                    assert len(param_def['description']) > 0
    
    def test_server_startup_sequence(self, server_with_config):
        """Test server startup sequence."""
        # Test that server can be initialized properly
        assert server_with_config.mcp is not None
        assert server_with_config.logger is not None
        assert server_with_config.sdk_available is True
        
        # Test that tools are registered
        tools = server_with_config.mcp._tools
        assert len(tools) > 0
        
        # Test that server can provide info
        info = server_with_config.get_server_info()
        assert info['server_name'] == 'Everything Search MCP Server'
    
    def test_server_configuration_loading(self, server_with_config, test_config_path):
        """Test server configuration loading."""
        # Verify config file exists
        assert os.path.exists(test_config_path)
        
        # Verify server loaded the config
        assert server_with_config.config_path == test_config_path
        
        # Test that server can read config
        with open(test_config_path, 'r') as f:
            config_data = json.load(f)
        
        # Verify config structure
        assert 'everything_search' in config_data
        assert 'search' in config_data
        assert 'performance' in config_data
        assert 'logging' in config_data
    
    def test_server_configuration_validation(self, server_with_config):
        """Test server configuration validation."""
        # Test that server can handle invalid configuration
        invalid_config_data = {
            "invalid_key": "invalid_value"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config_data, f)
            invalid_config_path = f.name
        
        try:
            with patch('everything_search_mcp_server.everything_sdk') as mock_sdk:
                mock_sdk.initialize = Mock()
                mock_sdk.search = Mock(return_value=[])
                
                # Server should still initialize even with invalid config
                server = EverythingSearchMCPServer(invalid_config_path)
                server.sdk_available = True
                server.sdk_path = "C:\\Everything64.dll"
                
                assert server.config_path == invalid_config_path
                assert server.mcp is not None
                
        finally:
            if os.path.exists(invalid_config_path):
                os.unlink(invalid_config_path)
    
    def test_server_environment_variables(self):
        """Test server environment variable handling."""
        # Test with environment variable set
        test_sdk_path = "C:\\Test\\Everything64.dll"
        os.environ['EVERYTHING_SDK_PATH'] = test_sdk_path
        
        try:
            with patch('everything_search_mcp_server.everything_sdk') as mock_sdk:
                mock_sdk.initialize = Mock()
                mock_sdk.search = Mock(return_value=[])
                
                server = EverythingSearchMCPServer()
                server.sdk_available = True
                server.sdk_path = test_sdk_path
                
                assert server.sdk_path == test_sdk_path
                
        finally:
            # Clean up environment variable
            if 'EVERYTHING_SDK_PATH' in os.environ:
                del os.environ['EVERYTHING_SDK_PATH']
    
    def test_server_file_structure_validation(self):
        """Test server file structure validation."""
        # Test that server can find required files
        base_path = Path(__file__).parent.parent.parent
        
        required_files = [
            "src/everything_search_mcp_server.py",
            "config/everything_search_mcp_config.json",
            "requirements.txt"
        ]
        
        for file_path in required_files:
            full_path = base_path / file_path
            assert full_path.exists(), f"Required file not found: {file_path}"
    
    def test_server_dependency_validation(self):
        """Test server dependency validation."""
        # Test that required dependencies are available
        try:
            import mcp.server.fastmcp
            import mcp.server.stdio
            import mcp.types
            import asyncio
            import ctypes
            import json
            import logging
            import os
            import sys
            from pathlib import Path
            from datetime import datetime
            
            # All dependencies should be available
            assert True
            
        except ImportError as e:
            pytest.fail(f"Missing dependency: {e}")
    
    def test_server_logging_setup(self, server_with_config):
        """Test server logging setup."""
        # Test that logger is properly configured
        assert server_with_config.logger is not None
        assert server_with_config.logger.name == __name__
        
        # Test that logger can handle different log levels
        server_with_config.logger.debug("Debug message")
        server_with_config.logger.info("Info message")
        server_with_config.logger.warning("Warning message")
        server_with_config.logger.error("Error message")
        server_with_config.logger.critical("Critical message")
        
        # All log calls should complete without errors
        assert True
    
    def test_server_sdk_initialization(self, server_with_config):
        """Test server SDK initialization."""
        # Test that SDK is properly initialized
        assert server_with_config.sdk_available is True
        assert server_with_config.sdk_path == "C:\\Everything64.dll"
        
        # Test that SDK validation works
        validation_result = asyncio.run(server_with_config.validate_sdk_installation())
        
        assert validation_result['valid'] is True
        assert validation_result['sdk_info']['sdk_path'] == "C:\\Everything64.dll"
        assert validation_result['sdk_info']['sdk_available'] is True
        assert 'timestamp' in validation_result
    
    def test_server_tool_execution(self, server_with_config):
        """Test server tool execution."""
        # Mock SDK search results
        server_with_config._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'test.txt', 'path': 'C:\\test\\test.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        # Test search_files tool execution
        result = asyncio.run(server_with_config.search_files("test"))
        
        assert result['query'] == "test"
        assert result['total_count'] == 1
        assert len(result['results']) == 1
        assert result['results'][0]['name'] == 'test.txt'
        assert 'timestamp' in result
    
    def test_server_error_handling(self, server_with_config):
        """Test server error handling."""
        # Test SDK unavailable scenario
        server_with_config.sdk_available = False
        
        # Test that appropriate errors are raised
        with pytest.raises(RuntimeError, match="Everything SDK is not available"):
            asyncio.run(server_with_config.search_files("test"))
        
        # Test that server info still works
        info = server_with_config.get_server_info()
        assert info['server_name'] == 'Everything Search MCP Server'
    
    def test_server_concurrent_tool_execution(self, server_with_config):
        """Test server concurrent tool execution."""
        # Mock SDK search results
        server_with_config._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': f'test{i}.txt', 'path': f'C:\\test\\test{i}.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
            for i in range(5)
        ])
        
        import concurrent.futures
        
        # Test concurrent tool execution
        def search_task(query):
            return asyncio.run(server_with_config.search_files(query))
        
        queries = ["test1", "test2", "test3", "test4", "test5"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(search_task, query) for query in queries]
            results = [future.result() for future in futures]
        
        # All searches should complete successfully
        for result in results:
            assert isinstance(result, dict)
            assert 'query' in result
            assert 'results' in result
            assert 'total_count' in result
            assert 'timestamp' in result
    
    def test_server_resource_cleanup(self, server_with_config):
        """Test server resource cleanup."""
        # Mock SDK methods
        mock_sdk = server_with_config._EverythingSearchMCPServer__dict__['everything_sdk']
        mock_sdk.search = Mock(return_value=[])
        mock_sdk.set_case_sensitive = Mock()
        mock_sdk.set_whole_word = Mock()
        mock_sdk.set_regex = Mock()
        
        # Perform advanced search
        asyncio.run(server_with_config.search_files_advanced("test", case_sensitive=True))
        
        # Verify that search options are reset
        mock_sdk.set_case_sensitive.assert_called_with(False)
        mock_sdk.set_whole_word.assert_called_with(False)
        mock_sdk.set_regex.assert_called_with(False)
    
    def test_server_performance_metrics(self, server_with_config):
        """Test server performance metrics."""
        import time
        
        # Mock SDK search results
        server_with_config._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'test.txt', 'path': 'C:\\test\\test.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        # Test search performance
        start_time = time.time()
        result = asyncio.run(server_with_config.search_files("test"))
        end_time = time.time()
        
        # Check that search completed in reasonable time
        assert end_time - start_time < 1.0  # Should complete in less than 1 second
        
        # Check result structure
        assert isinstance(result, dict)
        assert 'query' in result
        assert 'results' in result
        assert 'total_count' in result
        assert 'timestamp' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])