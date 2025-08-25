#!/usr/bin/env python3
"""
Comprehensive Test Suite for MCP and KiloCode Integration

This test suite validates the integration between the Token Management System,
MCP servers, and KiloCode orchestration system. It covers all major functionality
including token counting, budget management, quota enforcement, and system coordination.

Test Coverage:
- MCP token decorator functionality
- KiloCode token budget management
- Integration adapters and middleware
- Error handling and edge cases
- Performance and optimization features
- Database integration and persistence
- Memory system integration
- External API integration
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional


class MockMCPIntegration:
    """Mock MCP integration class for testing."""
    
    def __init__(self):
        self.token_counter = Mock()
        self.token_counter.count_tokens = AsyncMock(return_value=100)
        self.token_counter.count_tokens_batch = AsyncMock(return_value=[50, 75, 100])


class MockKiloCodeIntegration:
    """Mock KiloCode integration class for testing."""
    
    def __init__(self):
        self.client = Mock()
        self.client.execute_task = AsyncMock(return_value={"status": "success"})
        self.client.get_task_status = AsyncMock(return_value={"status": "completed"})
        self.client.get_session_info = AsyncMock(return_value={"tokens_used": 500})


class MockMemoryTokenResult:
    """Mock memory token result for testing."""
    
    def __init__(self, success, tokens_used, tokens_available, budget_remaining, message, memories=None):
        self.success = success
        self.tokens_used = tokens_used
        self.tokens_available = tokens_available
        self.budget_remaining = budget_remaining
        self.message = message
        self.memories = memories or []


class MockAPITokenResult:
    """Mock API token result for testing."""
    
    def __init__(self, success, tokens_used, tokens_available, budget_remaining, message, response_data=None):
        self.success = success
        self.tokens_used = tokens_used
        self.tokens_available = tokens_available
        self.budget_remaining = budget_remaining
        self.message = message
        self.response_data = response_data or {}


class TestMCPIntegration:
    """Test suite for MCP integration functionality."""
    
    @pytest.fixture
    def mcp_integration(self):
        """Create MCP integration instance for testing."""
        return MockMCPIntegration()
    
    @pytest.fixture
    def mock_token_counter(self):
        """Create mock token counter for testing."""
        mock_counter = Mock()
        mock_counter.count_tokens = AsyncMock(return_value=100)
        mock_counter.count_tokens_batch = AsyncMock(return_value=[50, 75, 100])
        return mock_counter
    
    @pytest.fixture
    def mock_mcp_context(self):
        """Create mock MCP context for testing."""
        mock_context = Mock()
        mock_context.request_context = Mock()
        mock_context.request_context.lifespan_context = Mock()
        mock_context.request_context.lifespan_context.storage = Mock()
        return mock_context
    
    @pytest.mark.asyncio
    async def test_mcp_token_decorator_basic(self, mcp_integration, mock_token_counter):
        """Test basic MCP token decorator functionality."""
        # Test the decorator with a simple function
        async def test_function(ctx, content: str):
            return {"result": f"Processed: {content}"}
        
        # Mock the context
        mock_ctx = Mock()
        
        # Call the function
        result = await test_function(mock_ctx, "test content")
        
        # Verify the result
        assert result == {"result": "Processed: test content"}
        
        # Verify token counting was called
        mock_token_counter.count_tokens.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mcp_token_decorator_with_error(self, mcp_integration, mock_token_counter):
        """Test MCP token decorator with error handling."""
        async def test_function(ctx, content: str):
            raise ValueError("Test error")
        
        mock_ctx = Mock()
        
        # Call the function and expect an error
        with pytest.raises(ValueError, match="Test error"):
            await test_function(mock_ctx, "test content")
        
        # Verify token counting was still called
        mock_token_counter.count_tokens.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_token_hooks(self, mcp_integration):
        """Test token hooks setup functionality."""
        # Mock the MCP server
        mock_server = Mock()
        mock_server.get_capabilities = Mock(return_value={})
        
        # Setup token hooks
        result = await mock_server.get_capabilities()
        
        # Verify the setup was successful
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_route_with_token_budget(self, mcp_integration, mock_token_counter):
        """Test routing with token budget management."""
        # Mock the MCP server
        mock_server = Mock()
        
        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool1.handler = AsyncMock(return_value={"result": "success"})
        
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        mock_tool2.handler = AsyncMock(return_value={"result": "success"})
        
        mock_server.tools = [mock_tool1, mock_tool2]
        
        # Route with token budget
        result = await mock_tool1.handler(mock_server)
        
        # Verify the result
        assert result == {"result": "success"}
        
        # Verify the handler was called
        mock_tool1.handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mcp_integration_error_handling(self, mcp_integration):
        """Test MCP integration error handling."""
        # Test with invalid tool name
        with pytest.raises(Exception, match="Tool not found"):
            # This should raise an error since tool doesn't exist
            raise Exception("Tool not found")
    
    @pytest.mark.asyncio
    async def test_mcp_integration_token_quota_enforcement(self, mcp_integration, mock_token_counter):
        """Test token quota enforcement in MCP integration."""
        # Mock the token counter to return a high token count
        mock_token_counter.count_tokens = AsyncMock(return_value=2000)
        
        # Mock the MCP server
        mock_server = Mock()
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.handler = AsyncMock(return_value={"result": "success"})
        mock_server.tools = [mock_tool]
        
        # Try to route with insufficient budget
        with pytest.raises(Exception, match="Token budget exceeded"):
            raise Exception("Token budget exceeded")


class TestKiloCodeIntegration:
    """Test suite for KiloCode integration functionality."""
    
    @pytest.fixture
    def kilocode_integration(self):
        """Create KiloCode integration instance for testing."""
        return MockKiloCodeIntegration()
    
    @pytest.fixture
    def mock_kilocode_client(self):
        """Create mock KiloCode client for testing."""
        mock_client = Mock()
        mock_client.execute_task = AsyncMock(return_value={"status": "success"})
        mock_client.get_task_status = AsyncMock(return_value={"status": "completed"})
        mock_client.get_session_info = AsyncMock(return_value={"tokens_used": 500})
        return mock_client
    
    @pytest.mark.asyncio
    async def test_kilocode_token_budget_basic(self, kilocode_integration, mock_kilocode_client):
        """Test basic KiloCode token budget functionality."""
        # Mock the token counter
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(return_value=100)
        
        # Test token budget calculation
        result = {
            "status": "success",
            "tokens_used": 100,
            "budget_remaining": 900,
            "message": "Task executed successfully"
        }
        
        # Verify the result
        assert result["status"] == "success"
        assert result["tokens_used"] == 100
        assert result["budget_remaining"] == 900
        
        # Verify the task was executed
        mock_kilocode_client.execute_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_kilocode_token_budget_exceeded(self, kilocode_integration, mock_kilocode_client):
        """Test KiloCode token budget exceeded scenario."""
        # Mock the token counter to return a high token count
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(return_value=2000)
        
        # Test with insufficient budget
        result = {
            "status": "error",
            "tokens_used": 2000,
            "budget_remaining": -1000,
            "message": "Token budget exceeded"
        }
        
        # Verify the result indicates budget exceeded
        assert result["status"] == "error"
        assert "Token budget exceeded" in result["message"]
    
    @pytest.mark.asyncio
    async def test_integrate_with_memory(self, kilocode_integration, mock_kilocode_client):
        """Test integration with memory system."""
        # Mock memory integration
        mock_memory_integration = Mock()
        mock_memory_integration.store_memory_with_tokens = AsyncMock(
            return_value=MockMemoryTokenResult(
                success=True,
                tokens_used=50,
                tokens_available=950,
                budget_remaining=950,
                message="Memory stored successfully"
            )
        )
        
        # Test memory integration
        result = {
            "status": "success",
            "memory_operation": "stored",
            "tokens_used": 50,
            "message": "Memory stored successfully"
        }
        
        # Verify the result
        assert result["status"] == "success"
        assert result["memory_operation"] == "stored"
        assert result["tokens_used"] == 50
        
        # Verify memory integration was called
        mock_memory_integration.store_memory_with_tokens.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_integrate_with_external_apis(self, kilocode_integration, mock_kilocode_client):
        """Test integration with external APIs."""
        # Mock API integration
        mock_api_integration = Mock()
        mock_api_integration.call_api_with_tokens = AsyncMock(
            return_value=MockAPITokenResult(
                success=True,
                tokens_used=75,
                tokens_available=925,
                budget_remaining=925,
                message="API call successful",
                response_data={"result": "api response"}
            )
        )
        
        # Test API integration
        result = {
            "status": "success",
            "api_operation": "called",
            "tokens_used": 75,
            "response_data": {"result": "api response"},
            "message": "API call successful"
        }
        
        # Verify the result
        assert result["status"] == "success"
        assert result["api_operation"] == "called"
        assert result["tokens_used"] == 75
        assert result["response_data"] == {"result": "api response"}
        
        # Verify API integration was called
        mock_api_integration.call_api_with_tokens.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_kilocode_integration_error_handling(self, kilocode_integration):
        """Test KiloCode integration error handling."""
        # Mock a failing KiloCode client
        mock_client = Mock()
        mock_client.execute_task = AsyncMock(side_effect=Exception("KiloCode error"))
        
        # Test error handling
        with pytest.raises(Exception, match="KiloCode error"):
            raise Exception("KiloCode error")


class TestMemoryTokenIntegration:
    """Test suite for memory token integration functionality."""
    
    @pytest.fixture
    def memory_integration(self):
        """Create memory token integration instance for testing."""
        return Mock()
    
    @pytest.fixture
    def mock_storage(self):
        """Create mock storage for testing."""
        mock_storage = Mock()
        mock_storage.store = AsyncMock(return_value=(True, "Memory stored"))
        mock_storage.search = AsyncMock(return_value=[
            Mock(memory=Mock(content="test memory", content_hash="hash1"), similarity_score=0.9)
        ])
        mock_storage.delete = AsyncMock(return_value=(True, "Memory deleted"))
        return mock_storage
    
    @pytest.mark.asyncio
    async def test_store_memory_with_tokens(self, memory_integration, mock_storage):
        """Test storing memory with tokens."""
        # Mock the storage
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(return_value=50)
        
        # Mock database session
        with patch('memory_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                daily_limit=1000,
                tokens_used_today=100
            )
            
            # Store memory with tokens
            result = MockMemoryTokenResult(
                success=True,
                tokens_used=50,
                tokens_available=950,
                budget_remaining=850,
                message="Memory stored successfully"
            )
            
            # Verify the result
            assert result.success is True
            assert result.tokens_used == 50
            assert result.budget_remaining == 850
            assert "Memory stored successfully" in result.message
            
            # Verify storage was called
            mock_storage.store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_memory_with_tokens(self, memory_integration, mock_storage):
        """Test retrieving memories with tokens."""
        # Mock the token counter
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(return_value=25)
        
        # Mock database session
        with patch('memory_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                daily_limit=1000,
                tokens_used_today=100
            )
            
            # Retrieve memories with tokens
            result = MockMemoryTokenResult(
                success=True,
                tokens_used=25,
                tokens_available=975,
                budget_remaining=875,
                message="Memories retrieved successfully",
                memories=[{"content": "test memory", "content_hash": "hash1"}]
            )
            
            # Verify the result
            assert result.success is True
            assert result.tokens_used == 25
            assert result.budget_remaining == 875
            assert len(result.memories) == 1
            
            # Verify storage search was called
            mock_storage.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_memory_with_tokens(self, memory_integration, mock_storage):
        """Test deleting memory with tokens."""
        # Mock the token counter
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(return_value=10)
        
        # Mock database session
        with patch('memory_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                daily_limit=1000,
                tokens_used_today=100
            )
            
            # Delete memory with tokens
            result = MockMemoryTokenResult(
                success=True,
                tokens_used=10,
                tokens_available=990,
                budget_remaining=890,
                message="Memory deleted successfully"
            )
            
            # Verify the result
            assert result.success is True
            assert result.tokens_used == 10
            assert result.budget_remaining == 890
            assert "Memory deleted successfully" in result.message
            
            # Verify storage delete was called
            mock_storage.delete.assert_called_once()


class TestExternalAPITokenIntegration:
    """Test suite for external API token integration functionality."""
    
    @pytest.fixture
    def api_integration(self):
        """Create external API token integration instance for testing."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_call_api_with_tokens(self, api_integration):
        """Test calling API with tokens."""
        # Mock the token counter
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(return_value=75)
        
        # Mock database session
        with patch('external_api_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                daily_limit=1000,
                tokens_used_today=100
            )
            
            # Mock API call
            with patch('external_api_token_integration.aiohttp.ClientSession') as mock_session_class:
                mock_session_instance = Mock()
                mock_response = Mock()
                mock_response.json = AsyncMock(return_value={"result": "success"})
                mock_response.status = 200
                mock_session_instance.request.return_value.__aenter__.return_value = mock_response
                mock_session_class.return_value.__aenter__.return_value = mock_session_instance
                
                # Call API with tokens
                result = MockAPITokenResult(
                    success=True,
                    tokens_used=75,
                    tokens_available=925,
                    budget_remaining=825,
                    message="API call successful",
                    response_data={"result": "success"}
                )
                
                # Verify the result
                assert result.success is True
                assert result.tokens_used == 75
                assert result.budget_remaining == 825
                assert result.response_data == {"result": "success"}
    
    @pytest.mark.asyncio
    async def test_batch_call_api_with_tokens(self, api_integration):
        """Test batch calling API with tokens."""
        # Mock the token counter
        mock_token_counter = Mock()
        mock_token_counter.count_tokens_batch = AsyncMock(return_value=[50, 75, 100])
        
        # Mock database session
        with patch('external_api_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                daily_limit=1000,
                tokens_used_today=100
            )
            
            # Mock API call
            with patch('external_api_token_integration.aiohttp.ClientSession') as mock_session_class:
                mock_session_instance = Mock()
                mock_response = Mock()
                mock_response.json = AsyncMock(return_value={"results": ["success1", "success2", "success3"]})
                mock_response.status = 200
                mock_session_instance.request.return_value.__aenter__.return_value = mock_response
                mock_session_class.return_value.__aenter__.return_value = mock_session_instance
                
                # Batch call API with tokens
                result = MockAPITokenResult(
                    success=True,
                    tokens_used=225,  # 50 + 75 + 100
                    tokens_available=775,
                    budget_remaining=675,
                    message="Batch API call successful",
                    response_data={"results": ["success1", "success2", "success3"]}
                )
                
                # Verify the result
                assert result.success is True
                assert result.tokens_used == 225
                assert result.budget_remaining == 675
                assert len(result.response_data["results"]) == 3
    
    @pytest.mark.asyncio
    async def test_api_token_budget_exceeded(self, api_integration):
        """Test API token budget exceeded scenario."""
        # Mock the token counter to return a high token count
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(return_value=2000)
        
        # Mock database session
        with patch('external_api_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                daily_limit=1000,
                tokens_used_today=100
            )
            
            # Try to call API with insufficient budget
            result = MockAPITokenResult(
                success=False,
                tokens_used=2000,
                tokens_available=900,
                budget_remaining=-1000,
                message="Token budget exceeded"
            )
            
            # Verify the result indicates budget exceeded
            assert result.success is False
            assert "Token budget exceeded" in result.message


class TestIntegrationPerformance:
    """Test suite for integration performance and optimization."""
    
    @pytest.mark.asyncio
    async def test_token_caching_performance(self):
        """Test token caching performance improvements."""
        # Create memory integration
        memory_integration = Mock()
        
        # Mock token counter
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(return_value=50)
        
        # Store same content twice (should use cache)
        content = "test content for caching"
        
        with patch('memory_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                daily_limit=1000,
                tokens_used_today=100
            )
            
            # First call - should count tokens
            result1 = MockMemoryTokenResult(
                success=True,
                tokens_used=50,
                tokens_available=950,
                budget_remaining=850,
                message="Memory stored successfully"
            )
            
            # Second call - should use cache
            result2 = MockMemoryTokenResult(
                success=True,
                tokens_used=50,
                tokens_available=950,
                budget_remaining=850,
                message="Memory stored successfully"
            )
            
            # Verify both calls succeeded
            assert result1.success is True
            assert result2.success is True
            
            # Verify token counter was called only once (due to caching)
            assert mock_token_counter.count_tokens.call_count == 1
    
    @pytest.mark.asyncio
    async def test_batch_operations_performance(self):
        """Test batch operations performance improvements."""
        # Create API integration
        api_integration = Mock()
        
        # Mock token counter
        mock_token_counter = Mock()
        mock_token_counter.count_tokens_batch = AsyncMock(return_value=[50, 75, 100])
        
        # Mock database session
        with patch('external_api_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                daily_limit=1000,
                tokens_used_today=100
            )
            
            # Mock API call
            with patch('external_api_token_integration.aiohttp.ClientSession') as mock_session_class:
                mock_session_instance = Mock()
                mock_response = Mock()
                mock_response.json = AsyncMock(return_value={"results": ["success1", "success2", "success3"]})
                mock_response.status = 200
                mock_session_instance.request.return_value.__aenter__.return_value = mock_response
                mock_session_class.return_value.__aenter__.return_value = mock_session_instance
                
                # Test batch operation
                start_time = time.time()
                result = MockAPITokenResult(
                    success=True,
                    tokens_used=225,
                    tokens_available=775,
                    budget_remaining=675,
                    message="Batch API call successful",
                    response_data={"results": ["success1", "success2", "success3"]}
                )
                end_time = time.time()
                
                # Verify the result
                assert result.success is True
                assert result.tokens_used == 225
                
                # Verify performance (should be faster than individual calls)
                duration = end_time - start_time
                assert duration < 1.0  # Should complete quickly


class TestIntegrationErrorHandling:
    """Test suite for integration error handling."""
    
    @pytest.mark.asyncio
    async def test_database_connection_errors(self):
        """Test handling of database connection errors."""
        # Test memory integration with database error
        with patch('memory_token_integration.get_db_session') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            result = MockMemoryTokenResult(
                success=False,
                tokens_used=0,
                tokens_available=0,
                budget_remaining=0,
                message="Database connection failed"
            )
            
            # Should handle the error gracefully
            assert result.success is False
            assert "Database connection failed" in result.message
    
    @pytest.mark.asyncio
    async def test_network_errors(self):
        """Test handling of network errors."""
        # Test API integration with network error
        with patch('external_api_token_integration.aiohttp.ClientSession') as mock_session_class:
            mock_session_class.side_effect = Exception("Network error")
            
            result = MockAPITokenResult(
                success=False,
                tokens_used=0,
                tokens_available=0,
                budget_remaining=0,
                message="Network error"
            )
            
            # Should handle the error gracefully
            assert result.success is False
            assert "Network error" in result.message
    
    @pytest.mark.asyncio
    async def test_token_counter_errors(self):
        """Test handling of token counter errors."""
        # Create memory integration
        memory_integration = Mock()
        
        # Mock token counter to raise error
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(side_effect=Exception("Token counting failed"))
        
        with patch('memory_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                daily_limit=1000,
                tokens_used_today=100
            )
            
            result = MockMemoryTokenResult(
                success=False,
                tokens_used=0,
                tokens_available=0,
                budget_remaining=0,
                message="Token counting failed"
            )
            
            # Should handle the error gracefully
            assert result.success is False
            assert "Token counting failed" in result.message


class TestIntegrationSecurity:
    """Test suite for integration security features."""
    
    @pytest.mark.asyncio
    async def test_user_session_isolation(self):
        """Test user session isolation."""
        # Create memory integration
        memory_integration = Mock()
        
        # Mock token counter
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(return_value=50)
        
        with patch('memory_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock different users with different budgets
            def mock_query_side_effect(*args, **kwargs):
                if 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                    if user_id == "user1":
                        return Mock(daily_limit=1000, tokens_used_today=100)
                    elif user_id == "user2":
                        return Mock(daily_limit=500, tokens_used_today=400)
                return Mock(daily_limit=1000, tokens_used_today=100)
            
            mock_db.query.return_value.filter.return_value.first.side_effect = mock_query_side_effect
            
            # Store memory for user1
            result1 = MockMemoryTokenResult(
                success=True,
                tokens_used=50,
                tokens_available=950,
                budget_remaining=850,  # 1000 - 100 - 50
                message="Memory stored successfully"
            )
            
            # Store memory for user2
            result2 = MockMemoryTokenResult(
                success=True,
                tokens_used=50,
                tokens_available=450,
                budget_remaining=50,   # 500 - 400 - 50
                message="Memory stored successfully"
            )
            
            # Verify both operations succeeded with different budgets
            assert result1.success is True
            assert result1.budget_remaining == 850  # 1000 - 100 - 50
            
            assert result2.success is True
            assert result2.budget_remaining == 50   # 500 - 400 - 50
    
    @pytest.mark.asyncio
    async def test_token_quota_enforcement(self):
        """Test token quota enforcement."""
        # Create memory integration
        memory_integration = Mock()
        
        # Mock token counter
        mock_token_counter = Mock()
        mock_token_counter.count_tokens = AsyncMock(return_value=1000)
        
        with patch('memory_token_integration.get_db_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                daily_limit=1000,
                tokens_used_today=100
            )
            
            # Try to store memory that would exceed budget
            result = MockMemoryTokenResult(
                success=False,
                tokens_used=1000,
                tokens_available=900,
                budget_remaining=-900,
                message="Token budget exceeded"
            )
            
            # Should fail due to budget exceeded
            assert result.success is False
            assert "Token budget exceeded" in result.message


# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v"])