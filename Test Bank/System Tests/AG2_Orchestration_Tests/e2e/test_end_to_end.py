"""
End-to-end tests for AG2 orchestration system
"""
import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

class TestEndToEndWorkflows:
    """End-to-end tests for complete AG2 workflows."""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_ag2_workflow(self):
        """Test complete AG2 workflow from setup to response."""
        from orchestration.ag2_pure import AG2PureOrchestrator
        
        # Initialize orchestrator
        orchestrator = AG2PureOrchestrator()
        
        # Test query processing
        query = "What is AG2 and how does it work?"
        
        with patch.object(orchestrator.researcher, 'search_knowledge_base') as mock_search:
            mock_search.return_value = [
                {
                    "content": "AG2 is a multi-agent orchestration system that coordinates specialized agents including researchers, analysts, and coordinators to provide comprehensive responses to user queries.",
                    "metadata": {"source": "ag2_guide.md", "type": "documentation"}
                }
            ]
            
            result = await orchestrator.process_query(query)
            
            assert result is not None
            assert "AG2" in result
            assert "multi-agent" in result.lower()
            assert "orchestration" in result.lower()
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_memory_persistence(self):
        """Test memory persistence across sessions."""
        from orchestration.ag2_pure import AG2PureOrchestrator
        
        # Create temporary directory for memory storage
        temp_dir = tempfile.mkdtemp()
        
        try:
            # First session
            orchestrator1 = AG2PureOrchestrator(memory_path=temp_dir)
            
            # Store some memories
            await orchestrator1.store_memory("user preference", "prefers concise answers")
            await orchestrator1.store_memory("project context", "working on AG2 system")
            
            # Second session
            orchestrator2 = AG2PureOrchestrator(memory_path=temp_dir)
            
            # Retrieve memories
            preference = await orchestrator2.retrieve_memory("user preference")
            context = await orchestrator2.retrieve_memory("project context")
            
            assert preference == "prefers concise answers"
            assert context == "working on AG2 system"
            
        finally:
            shutil.rmtree(temp_dir)
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test system recovery from errors."""
        from orchestration.ag2_pure import AG2PureOrchestrator
        
        orchestrator = AG2PureOrchestrator()
        
        # Test with failing search
        with patch.object(orchestrator.researcher, 'search_knowledge_base') as mock_search:
            mock_search.side_effect = Exception("Search service unavailable")
            
            result = await orchestrator.process_query("test query")
            
            # Should handle gracefully
            assert result is not None
            assert any(phrase in result.lower() for phrase in ["error", "failed", "unavailable"])
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_performance_benchmark(self):
        """Test system performance under load."""
        from orchestration.ag2_pure import AG2PureOrchestrator
        
        orchestrator = AG2PureOrchestrator()
        
        # Test with multiple queries
        queries = [
            "What is AG2?",
            "How do agents collaborate?",
            "What are the deployment options?",
            "How does memory work?",
            "What is the difference between lite and full modes?"
        ]
        
        with patch.object(orchestrator.researcher, 'search_knowledge_base') as mock_search:
            mock_search.return_value = [{"content": "Mock response for testing performance"}]
            
            start_time = asyncio.get_event_loop().time()
            
            # Process all queries
            tasks = [orchestrator.process_query(q) for q in queries]
            results = await asyncio.gather(*tasks)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # All queries should complete
            assert len(results) == len(queries)
            assert all(result is not None for result in results)
            
            # Should complete within reasonable time (5 seconds for 5 queries)
            assert duration < 5.0
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_cross_mode_compatibility(self):
        """Test compatibility between different deployment modes."""
        from orchestration.ag2_pure import AG2PureOrchestrator
        from orchestration.ag2_orchestrator import AG2Orchestrator
        
        query = "What is AG2?"
        
        # Test pure mode
        pure_orchestrator = AG2PureOrchestrator()
        with patch.object(pure_orchestrator.researcher, 'search_knowledge_base') as mock_search:
            mock_search.return_value = [{"content": "AG2 is a multi-agent system"}]
            pure_result = await pure_orchestrator.process_query(query)
        
        # Test lite mode
        lite_orchestrator = AG2Orchestrator(mode="lite")
        with patch('orchestration.ag2_orchestrator.call_mcp_tool') as mock_call:
            mock_call.return_value = {"result": "AG2 is a multi-agent system"}
            lite_result = await lite_orchestrator.process_query(query)
        
        # Both should provide meaningful responses
        assert pure_result is not None
        assert lite_result is not None
        assert "AG2" in pure_result
        assert "AG2" in lite_result

class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_research_scenario(self):
        """Test research-heavy scenario."""
        from orchestration.ag2_pure import AG2PureOrchestrator
        
        orchestrator = AG2PureOrchestrator()
        
        # Complex research query
        query = "Compare AG2 with other multi-agent systems like AutoGen and CrewAI"
        
        with patch.object(orchestrator.researcher, 'search_knowledge_base') as mock_search:
            mock_search.return_value = [
                {
                    "content": "AG2 provides specialized agents for research, analysis, and coordination with built-in memory and orchestration capabilities.",
                    "metadata": {"source": "comparison.md"}
                },
                {
                    "content": "AutoGen focuses on conversation patterns between agents, while AG2 emphasizes specialized roles and orchestration.",
                    "metadata": {"source": "autogen_comparison.md"}
                }
            ]
            
            result = await orchestrator.process_query(query)
            
            assert result is not None
            assert "AG2" in result
            assert any(system in result for system in ["AutoGen", "CrewAI"])
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_analysis_scenario(self):
        """Test analysis-heavy scenario."""
        from orchestration.ag2_pure import AG2PureOrchestrator
        
        orchestrator = AG2PureOrchestrator()
        
        # Analysis query
        query = "Analyze the benefits and trade-offs of using AG2 in production"
        
        with patch.object(orchestrator.researcher, 'search_knowledge_base') as mock_search:
            mock_search.return_value = [
                {
                    "content": "AG2 benefits include specialized agents, memory persistence, and flexible deployment modes. Trade-offs include complexity and resource requirements.",
                    "metadata": {"source": "production_analysis.md"}
                }
            ]
            
            result = await orchestrator.process_query(query)
            
            assert result is not None
            assert any(term in result.lower() for term in ["benefit", "advantage", "pro"])
            assert any(term in result.lower() for term in ["trade-off", "drawback", "con"])
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_coordination_scenario(self):
        """Test coordination-heavy scenario."""
        from orchestration.ag2_pure import AG2PureOrchestrator
        
        orchestrator = AG2PureOrchestrator()
        
        # Coordination query
        query = "How do the researcher, analyst, and coordinator agents work together?"
        
        with patch.object(orchestrator.researcher, 'search_knowledge_base') as mock_search:
            mock_search.return_value = [
                {
                    "content": "The researcher gathers information, the analyst processes and synthesizes findings, and the coordinator manages task distribution and workflow orchestration.",
                    "metadata": {"source": "agent_coordination.md"}
                }
            ]
            
            result = await orchestrator.process_query(query)
            
            assert result is not None
            assert "researcher" in result.lower()
            assert "analyst" in result.lower()
            assert "coordinator" in result.lower()

class TestDeploymentScenarios:
    """Test different deployment scenarios."""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_development_deployment(self):
        """Test development deployment scenario."""
        from orchestration.ag2_pure import AG2PureOrchestrator
        
        # Development mode with debug logging
        orchestrator = AG2PureOrchestrator(debug=True)
        
        query = "What is AG2?"
        
        with patch.object(orchestrator.researcher, 'search_knowledge_base') as mock_search:
            mock_search.return_value = [{"content": "AG2 development mode response"}]
            
            result = await orchestrator.process_query(query)
            
            assert result is not None
            assert "AG2" in result
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_production_deployment(self):
        """Test production deployment scenario."""
        from orchestration.ag2_pure import AG2PureOrchestrator
        
        # Production mode with performance optimizations
        orchestrator = AG2PureOrchestrator(
            cache_size=1000,
            max_concurrent_queries=10
        )
        
        query = "What is AG2?"
        
        with patch.object(orchestrator.researcher, 'search_knowledge_base') as mock_search:
            mock_search.return_value = [{"content": "AG2 production mode response"}]
            
            result = await orchestrator.process_query(query)
            
            assert result is not None
            assert "AG2" in result
    
    @pytest.mark.e2e
    def test_setup_scripts(self):
        """Test setup scripts functionality."""
        import subprocess
        import os
        
        # Test setup script exists
        setup_script = Path(__file__).parent.parent.parent / "src" / "orchestration" / "setup_and_test.sh"
        assert setup_script.exists()
        
        # Test lite setup script exists
        lite_setup_script = Path(__file__).parent.parent.parent / "src" / "orchestration" / "setup_lite.py"
        assert lite_setup_script.exists()
        
        # Test pure mode script exists
        pure_script = Path(__file__).parent.parent.parent / "src" / "orchestration" / "run_pure.py"
        assert pure_script.exists()
