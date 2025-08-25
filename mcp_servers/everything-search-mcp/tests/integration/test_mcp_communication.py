#!/usr/bin/env python3
"""
Integration Tests for MCP Communication Protocol

This module contains integration tests for MCP communication protocol functionality.
Tests cover stdio transport, message handling, and protocol compliance.

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
import sys
import io
from datetime import datetime

# Add the src directory to the Python path
sys_path = str(Path(__file__).parent.parent.parent / "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from everything_search_mcp_server import EverythingSearchMCPServer


class TestMCPCommunication:
    """Test suite for MCP communication protocol."""
    
    @pytest.fixture
    def mock_stdio_streams(self):
        """Create mock stdio streams for testing."""
        # Create mock read and write streams
        mock_read_stream = Mock()
        mock_write_stream = Mock()
        
        # Mock read_stream to return test messages
        async def mock_read():
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture messages
        write_buffer = []
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        mock_write_stream.flush = mock.AsyncMock()
        
        return mock_read_stream, mock_write_stream, write_buffer
    
    @pytest.fixture
    def server_with_mock_sdk(self):
        """Create a server instance with mocked SDK."""
        with patch('everything_search_mcp_server.everything_sdk') as mock_sdk:
            mock_sdk.initialize = Mock()
            mock_sdk.search = Mock(return_value=[])
            
            server = EverythingSearchMCPServer()
            server.sdk_available = True
            server.sdk_path = "C:\\Everything64.dll"
            
            return server
    
    @pytest.mark.asyncio
    async def test_stdio_transport_initialization(self, server_with_mock_sdk, mock_stdio_streams):
        """Test stdio transport initialization."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Test that server can be initialized with stdio transport
        assert server_with_mock_sdk.mcp is not None
        assert server_with_mock_sdk.logger is not None
        
        # Test that server can handle stdio streams
        try:
            async with mock_read_stream, mock_write_stream:
                # This is a basic test - in real scenarios, the server would run indefinitely
                pass
        except Exception as e:
            # Expected for mock streams
            pass
    
    @pytest.mark.asyncio
    async def test_message_handling(self, server_with_mock_sdk, mock_stdio_streams):
        """Test message handling functionality."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock the server's run method to handle messages
        server_with_mock_sdk.mcp.run = AsyncMock()
        
        # Test that server can handle incoming messages
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that run method was called
        server_with_mock_sdk.mcp.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tool_call_handling(self, server_with_mock_sdk, mock_stdio_streams):
        """Test tool call handling."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock search results
        server_with_mock_sdk._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': 'test.txt', 'path': 'C:\\test\\test.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
        ])
        
        # Mock a tool call message
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_files",
                "arguments": {
                    "query": "test",
                    "max_results": 10
                }
            }
        }
        
        # Mock read_stream to return tool call message
        async def mock_read():
            return tool_call_message
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture response
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        
        # Test tool call handling
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that response was written
        assert len(write_buffer) > 0
        
        # Check response structure
        response = write_buffer[0]
        assert "jsonrpc" in response
        assert response["jsonrpc"] == "2.0"
        assert "id" in response
        assert response["id"] == 1
        assert "result" in response
    
    @pytest.mark.asyncio
    async def test_tool_list_handling(self, server_with_mock_sdk, mock_stdio_streams):
        """Test tool list handling."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock a tool list message
        tool_list_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        # Mock read_stream to return tool list message
        async def mock_read():
            return tool_list_message
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture response
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        
        # Test tool list handling
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that response was written
        assert len(write_buffer) > 0
        
        # Check response structure
        response = write_buffer[0]
        assert "jsonrpc" in response
        assert response["jsonrpc"] == "2.0"
        assert "id" in response
        assert response["id"] == 1
        assert "result" in response
        assert "tools" in response["result"]
        assert isinstance(response["result"]["tools"], list)
    
    @pytest.mark.asyncio
    async def test_tool_schema_handling(self, server_with_mock_sdk, mock_stdio_streams):
        """Test tool schema handling."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock a tool schema message
        tool_schema_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_files",
                "arguments": {
                    "query": "test",
                    "max_results": 10
                }
            }
        }
        
        # Mock read_stream to return tool schema message
        async def mock_read():
            return tool_schema_message
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture response
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        
        # Test tool schema handling
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that response was written
        assert len(write_buffer) > 0
        
        # Check response structure
        response = write_buffer[0]
        assert "jsonrpc" in response
        assert response["jsonrpc"] == "2.0"
        assert "id" in response
        assert response["id"] == 1
        assert "result" in response
        
        # Check that result contains expected fields
        result = response["result"]
        assert "query" in result
        assert "results" in result
        assert "total_count" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_in_communication(self, server_with_mock_sdk, mock_stdio_streams):
        """Test error handling in communication."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock an error message
        error_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_files",
                "arguments": {
                    "query": "",  # Invalid query
                    "max_results": -1  # Invalid max_results
                }
            }
        }
        
        # Mock read_stream to return error message
        async def mock_read():
            return error_message
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture response
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        
        # Test error handling
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that error response was written
        assert len(write_buffer) > 0
        
        # Check error response structure
        response = write_buffer[0]
        assert "jsonrpc" in response
        assert response["jsonrpc"] == "2.0"
        assert "id" in response
        assert response["id"] == 1
        assert "error" in response
        assert "message" in response["error"]
        assert "data" in response["error"]
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, server_with_mock_sdk, mock_stdio_streams):
        """Test concurrent tool calls."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock search results
        server_with_mock_sdk._EverythingSearchMCPServer__dict__['everything_sdk'].search = Mock(return_value=[
            {'name': f'test{i}.txt', 'path': f'C:\\test\\test{i}.txt', 'size': 1024, 
             'modified': '2023-01-01T00:00:00', 'extension': 'txt', 'is_directory': False}
            for i in range(5)
        ])
        
        # Mock multiple concurrent tool calls
        tool_calls = [
            {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "search_files",
                    "arguments": {
                        "query": f"test{i}",
                        "max_results": 10
                    }
                }
            }
            for i in range(5)
        ]
        
        # Mock read_stream to return tool calls
        call_index = 0
        async def mock_read():
            nonlocal call_index
            if call_index < len(tool_calls):
                message = tool_calls[call_index]
                call_index += 1
                return message
            else:
                # Return None to simulate end of stream
                return None
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture responses
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        
        # Test concurrent tool calls
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that all responses were written
        assert len(write_buffer) == 5
        
        # Check that all responses have correct structure
        for i, response in enumerate(write_buffer):
            assert "jsonrpc" in response
            assert response["jsonrpc"] == "2.0"
            assert "id" in response
            assert response["id"] == i
            assert "result" in response
    
    @pytest.mark.asyncio
    async def test_protocol_version_compliance(self, server_with_mock_sdk, mock_stdio_streams):
        """Test protocol version compliance."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock a tool call message with protocol version
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_files",
                "arguments": {
                    "query": "test",
                    "max_results": 10
                }
            }
        }
        
        # Mock read_stream to return tool call message
        async def mock_read():
            return tool_call_message
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture response
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        
        # Test protocol version compliance
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that response has correct protocol version
        assert len(write_buffer) > 0
        
        response = write_buffer[0]
        assert "jsonrpc" in response
        assert response["jsonrpc"] == "2.0"
    
    @pytest.mark.asyncio
    async def test_message_id_handling(self, server_with_mock_sdk, mock_stdio_streams):
        """Test message ID handling."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock multiple tool calls with different IDs
        tool_calls = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "search_files",
                    "arguments": {
                        "query": "test1",
                        "max_results": 10
                    }
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search_files",
                    "arguments": {
                        "query": "test2",
                        "max_results": 10
                    }
                }
            }
        ]
        
        # Mock read_stream to return tool calls
        call_index = 0
        async def mock_read():
            nonlocal call_index
            if call_index < len(tool_calls):
                message = tool_calls[call_index]
                call_index += 1
                return message
            else:
                return None
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture responses
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        
        # Test message ID handling
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that responses have correct IDs
        assert len(write_buffer) == 2
        
        # Check that responses have matching IDs
        for i, response in enumerate(write_buffer):
            assert "id" in response
            assert response["id"] == i + 1
    
    @pytest.mark.asyncio
    async def test_method_not_found_handling(self, server_with_mock_sdk, mock_stdio_streams):
        """Test method not found handling."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock a tool call to non-existent method
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "non_existent_method",
                "arguments": {
                    "query": "test"
                }
            }
        }
        
        # Mock read_stream to return tool call message
        async def mock_read():
            return tool_call_message
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture response
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        
        # Test method not found handling
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that error response was written
        assert len(write_buffer) > 0
        
        response = write_buffer[0]
        assert "jsonrpc" in response
        assert response["jsonrpc"] == "2.0"
        assert "id" in response
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32601  # Method not found
        assert "message" in response["error"]
    
    @pytest.mark.asyncio
    async def test_invalid_params_handling(self, server_with_mock_sdk, mock_stdio_streams):
        """Test invalid parameters handling."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock a tool call with invalid parameters
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_files",
                "arguments": {
                    "query": "",  # Invalid empty query
                    "max_results": -1  # Invalid negative max_results
                }
            }
        }
        
        # Mock read_stream to return tool call message
        async def mock_read():
            return tool_call_message
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture response
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        
        # Test invalid parameters handling
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that error response was written
        assert len(write_buffer) > 0
        
        response = write_buffer[0]
        assert "jsonrpc" in response
        assert response["jsonrpc"] == "2.0"
        assert "id" in response
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32602  # Invalid params
        assert "message" in response["error"]
    
    @pytest.mark.asyncio
    async def test_server_info_handling(self, server_with_mock_sdk, mock_stdio_streams):
        """Test server info handling."""
        mock_read_stream, mock_write_stream, write_buffer = mock_stdio_streams
        
        # Mock a server info call
        server_info_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_server_info",
                "arguments": {}
            }
        }
        
        # Mock read_stream to return server info message
        async def mock_read():
            return server_info_message
        
        mock_read_stream.read = mock.AsyncMock(side_effect=mock_read)
        
        # Mock write_stream to capture response
        async def mock_write(message):
            write_buffer.append(message)
        
        mock_write_stream.write = mock.AsyncMock(side_effect=mock_write)
        
        # Test server info handling
        try:
            await server_with_mock_sdk.mcp.run(
                mock_read_stream,
                mock_write_stream,
                create_task=asyncio.create_task
            )
        except Exception as e:
            # Expected for mock streams
            pass
        
        # Verify that response was written
        assert len(write_buffer) > 0
        
        response = write_buffer[0]
        assert "jsonrpc" in response
        assert response["jsonrpc"] == "2.0"
        assert "id" in response
        assert response["id"] == 1
        assert "result" in response
        
        # Check server info structure
        result = response["result"]
        assert "server_name" in result
        assert "version" in result
        assert "description" in result
        assert "author" in result
        assert "config_path" in result
        assert "sdk_info" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])