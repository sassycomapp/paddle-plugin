"""
Integration tests for AG2 orchestrator
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src" / "orchestration"
sys.path.insert(0, str(src_path))

class TestAG2PureOrchestrator:
    """Test AG2 Pure Orchestrator implementation."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        from ag2_pure import AG2Orchestrator
        
        orchestrator = AG2Orchestrator()
        
        assert orchestrator.agents is not None
        assert len(orchestrator.agents) == 3
        assert "researcher" in orchestrator.agents
        assert "coordinator" in orchestrator.agents
        assert "analyst" in orchestrator.agents
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test full workflow with mocked agents."""
        from ag2_pure import AG2Orchestrator
        
        orchestrator = AG2Orchestrator()
        
        # Mock the researcher agent
        with patch.object(orchestrator.agents['researcher'], 'process_task') as mock_researcher:
            mock_researcher.return_value = {
                "agent": "researcher",
                "task": "What is AG2?",
                "tools_used": ["rag"],
                "results": {"rag": [{"content": "AG2 is a multi-agent system"}]},
                "summary": "AG2 is a multi-agent system"
            }
            
            result = await orchestrator.run_query("What is AG2?")
            
            assert result is not None
            assert "researcher" in result.lower()
            assert "ag2" in result.lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in orchestrator."""
        from ag2_pure import AG2Orchestrator
        
        orchestrator = AG2Orchestrator()
        
        # Mock an error in the researcher
        with patch.object(orchestrator.agents['researcher'], 'process_task') as mock_process:
            mock_process.side_effect = Exception("Processing failed")
            
            query = "test query"
            
            # The orchestrator should handle the error gracefully
            try:
                result = await orchestrator.run_query(query)
                # If we get here, the error was handled gracefully
                assert result is not None
                assert "error" in result.lower() or "failed" in result.lower()
            except Exception as e:
                # If the exception wasn't caught, fail the test with a clear message
                pytest.fail(f"Error was not handled gracefully: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_selection(self):
        """Test agent selection logic."""
        from ag2_pure import AG2Orchestrator
        
        orchestrator = AG2Orchestrator()
        
        # Test different queries
        queries = [
            ("What is AG2?", "researcher"),
            ("Coordinate the workflow", "coordinator"),
            ("Analyze the data", "analyst")
        ]
        
        for query, expected_agent in queries:
            with patch.object(orchestrator.agents[expected_agent], 'process_task') as mock_process:
                mock_process.return_value = {
                    "agent": expected_agent,
                    "task": query,
                    "tools_used": ["memory"],
                    "results": {"memory": [{"content": f"Response from {expected_agent}"}]},
                    "summary": f"Response from {expected_agent}"
                }
                
                result = await orchestrator.run_query(query)
                
                assert result is not None
                assert expected_agent in result.lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_queries(self):
        """Test handling of concurrent queries."""
        from ag2_pure import AG2Orchestrator
        
        orchestrator = AG2Orchestrator()
        
        # Mock all agents
        with patch.object(orchestrator.agents['researcher'], 'process_task') as mock_researcher, \
             patch.object(orchestrator.agents['coordinator'], 'process_task') as mock_coordinator, \
             patch.object(orchestrator.agents['analyst'], 'process_task') as mock_analyst:
            
            mock_researcher.return_value = {
                "agent": "researcher",
                "task": "What is AG2?",
                "tools_used": ["rag"],
                "results": {"rag": [{"content": "AG2 is a multi-agent system"}]},
                "summary": "AG2 is a multi-agent system"
            }
            
            mock_coordinator.return_value = {
                "agent": "coordinator",
                "task": "Coordinate the workflow",
                "tools_used": ["memory"],
                "results": {"memory": [{"content": "Workflow coordinated"}]},
                "summary": "Workflow coordinated"
            }
            
            mock_analyst.return_value = {
                "agent": "analyst",
                "task": "Analyze the data",
                "tools_used": ["rag"],
                "results": {"rag": [{"content": "Data analyzed"}]},
                "summary": "Data analyzed"
            }
            
            # Run concurrent queries
            tasks = [
                orchestrator.run_query("What is AG2?"),
                orchestrator.run_query("Coordinate the workflow"),
                orchestrator.run_query("Analyze the data")
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(result is not None for result in results)
            assert any("researcher" in result.lower() for result in results)
            assert any("coordinator" in result.lower() for result in results)
            assert any("analyst" in result.lower() for result in results)

class TestAG2Orchestrator:
    """Test AG2 Orchestrator implementation."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        try:
            from ag2_orchestrator import AG2Orchestrator
            
            orchestrator = AG2Orchestrator()
            
            assert orchestrator.agents is not None
            assert len(orchestrator.agents) == 3
            assert "researcher" in orchestrator.agents
            assert "coordinator" in orchestrator.agents
            assert "analyst" in orchestrator.agents
        except ImportError:
            pytest.skip("Could not import ag2_orchestrator: No module named 'ag2_orchestrator'")
    
    @pytest.mark.integration
    def test_mcp_session_setup(self):
        """Test MCP session setup."""
        try:
            from ag2_orchestrator import AG2Orchestrator
            
            orchestrator = AG2Orchestrator()
            
            # Test MCP session setup
            assert hasattr(orchestrator, 'mcp_session')
            assert orchestrator.mcp_session is not None
        except ImportError:
            pytest.skip("Could not import ag2_orchestrator: No module named 'ag2_orchestrator'")
    
    @pytest.mark.integration
    def test_toolkit_creation(self):
        """Test toolkit creation."""
        try:
            from ag2_orchestrator import AG2Orchestrator
            
            orchestrator = AG2Orchestrator()
            
            # Test toolkit creation
            assert hasattr(orchestrator, 'toolkit')
            assert orchestrator.toolkit is not None
        except ImportError:
            pytest.skip("Could not import ag2_orchestrator: No module named 'ag2_orchestrator'")
    
    @pytest.mark.integration
    def test_agent_initialization(self):
        """Test agent initialization."""
        try:
            from ag2_orchestrator import AG2Orchestrator
            
            orchestrator = AG2Orchestrator()
            
            # Test agent initialization
            assert hasattr(orchestrator, 'agents')
            assert len(orchestrator.agents) == 3
            assert "researcher" in orchestrator.agents
            assert "coordinator" in orchestrator.agents
            assert "analyst" in orchestrator.agents
        except ImportError:
            pytest.skip("Could not import ag2_orchestrator: No module named 'ag2_orchestrator'")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_query_processing(self):
        """Test query processing."""
        try:
            from ag2_orchestrator import AG2Orchestrator
            
            orchestrator = AG2Orchestrator()
            
            # Mock the researcher agent
            with patch.object(orchestrator.agents['researcher'], 'process_task') as mock_researcher:
                mock_researcher.return_value = {
                    "agent": "researcher",
                    "task": "What is AG2?",
                    "tools_used": ["rag"],
                    "results": {"rag": [{"content": "AG2 is a multi-agent system"}]},
                    "summary": "AG2 is a multi-agent system"
                }
                
                result = await orchestrator.run_query("What is AG2?")
                
                assert result is not None
                assert "researcher" in result.lower()
                assert "ag2" in result.lower()
        except ImportError:
            pytest.skip("Could not import ag2_orchestrator: No module named 'ag2_orchestrator'")

class TestModeCompatibility:
    """Test mode compatibility between different implementations."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mode_switching(self):
        """Test switching between different modes."""
        from ag2_pure import AG2Orchestrator
        
        orchestrator = AG2Orchestrator()
        
        # Test different modes - use the actual agent names
        modes = ["researcher", "coordinator", "analyst"]
        
        for mode in modes:
            with patch.object(orchestrator.agents[mode], 'process_task') as mock_process:
                mock_process.return_value = {
                    "agent": mode,
                    "task": f"Test {mode} mode",
                    "tools_used": ["memory"],
                    "results": {"memory": [{"content": f"Response from {mode} mode"}]},
                    "summary": f"Response from {mode} mode"
                }
                
                result = await orchestrator.run_query(f"Test {mode} mode")
                
                assert result is not None
                assert mode in result.lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_consistent_behavior(self):
        """Test consistent behavior across different queries."""
        from ag2_pure import AG2Orchestrator
        
        orchestrator = AG2Orchestrator()
        
        # Test multiple queries
        queries = [
            "What is AG2?",
            "How does it work?",
            "What are the benefits?"
        ]
        
        for query in queries:
            with patch.object(orchestrator.agents['researcher'], 'process_task') as mock_process:
                mock_process.return_value = {
                    "agent": "researcher",
                    "task": query,
                    "tools_used": ["rag"],
                    "results": {"rag": [{"content": f"Response to {query}"}]},
                    "summary": f"Response to {query}"
                }
                
                result = await orchestrator.run_query(query)
                
                assert result is not None
                assert "researcher" in result.lower()
