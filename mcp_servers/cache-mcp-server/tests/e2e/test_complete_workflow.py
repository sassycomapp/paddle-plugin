"""
End-to-End Tests for Complete Cache Workflow.

This module contains comprehensive end-to-end tests for the complete cache workflow,
testing the entire user request → cache routing → cache layer processing → response flow.
"""

import pytest
import asyncio
import time
import json
import tempfile
import os
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import logging

from src.core.base_cache import CacheLayer, CacheStatus, CacheResult
from src.cache_layers.predictive_cache import PredictiveCache
from src.cache_layers.semantic_cache import SemanticCache
from src.cache_layers.vector_cache import VectorCache
from src.cache_layers.global_cache import GlobalCache
from src.cache_layers.vector_diary import VectorDiary
from src.core.config import PredictiveCacheConfig, SemanticCacheConfig, VectorCacheConfig, GlobalCacheConfig, VectorDiaryConfig
from src.mcp.tools import CacheMCPTools
from src.mcp.server import mcp_server_lifespan, MCPServerContext


class CacheWorkflowTester:
    """Main class for testing complete cache workflow."""
    
    def __init__(self):
        self.workflow_results = []
        self.logger = logging.getLogger(__name__)
        self.test_data = {
            "prompts": [
                "What is the capital of France?",
                "Explain machine learning in simple terms",
                "How do I implement a binary search?",
                "What are the benefits of caching?",
                "Describe the architecture of microservices",
                "What is the difference between SQL and NoSQL?",
                "How do I optimize database queries?",
                "What is the purpose of load balancing?",
                "Explain the concept of microservices",
                "How do I implement RESTful APIs?"
            ],
            "responses": [
                "The capital of France is Paris.",
                "Machine learning is a subset of AI that enables systems to learn from data.",
                "Binary search is an efficient algorithm for finding an item in a sorted array.",
                "Caching improves performance by storing frequently accessed data in memory.",
                "Microservices architecture breaks applications into small, independent services.",
                "SQL uses structured query language and relational databases, while NoSQL uses flexible schemas and various database models.",
                "Database queries can be optimized by using proper indexing, avoiding SELECT *, and writing efficient JOIN statements.",
                "Load balancing distributes incoming network traffic across multiple servers to ensure high availability and reliability.",
                "Microservices are an architectural approach where applications are built as a collection of small, independent services.",
                "RESTful APIs use HTTP methods to perform CRUD operations on resources with stateless communication."
            ]
        }
    
    async def simulate_complete_workflow(self, user_request: str, 
                                       cache_tools: CacheMCPTools,
                                       expected_cache_layer: CacheLayer = None) -> Dict[str, Any]:
        """Simulate the complete cache workflow."""
        workflow_result = {
            "user_request": user_request,
            "timestamp": time.time(),
            "cache_layer_expected": expected_cache_layer.value if expected_cache_layer else None,
            "cache_layer_actual": None,
            "workflow_steps": [],
            "total_time_ms": None,
            "cache_hit": False,
            "cache_miss": False,
            "error_occurred": False,
            "error_message": None,
            "response_data": None,
            "performance_metrics": {}
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Request Analysis and Cache Layer Determination
            step_start = time.time()
            cache_layers = cache_tools._determine_cache_layers(user_request)
            step_end = time.time()
            
            workflow_result["workflow_steps"].append({
                "step": "request_analysis",
                "duration_ms": (step_end - step_start) * 1000,
                "cache_layers_determined": [layer.value for layer in cache_layers],
                "success": True
            })
            
            # Step 2: Cache Routing and Query
            step_start = time.time()
            cache_hit = False
            cache_miss = False
            response_data = None
            actual_cache_layer = None
            
            # Try each cache layer in order
            for layer in cache_layers:
                if layer in cache_tools.caches:
                    cache = cache_tools.caches[layer]
                    
                    # Generate cache key from user request
                    cache_key = self._generate_cache_key(user_request, layer)
                    
                    # Query cache
                    query_start = time.time()
                    cache_result = await cache.get(cache_key)
                    query_end = time.time()
                    
                    workflow_result["workflow_steps"].append({
                        "step": "cache_query",
                        "cache_layer": layer.value,
                        "cache_key": cache_key,
                        "duration_ms": (query_end - query_start) * 1000,
                        "cache_status": cache_result.status.value if cache_result else None,
                        "success": True
                    })
                    
                    if cache_result and cache_result.status == CacheStatus.HIT:
                        cache_hit = True
                        actual_cache_layer = layer
                        response_data = cache_result.entry.value if cache_result.entry else None
                        break
                    else:
                        cache_miss = True
            
            workflow_result["cache_hit"] = cache_hit
            workflow_result["cache_miss"] = cache_miss
            workflow_result["cache_layer_actual"] = actual_cache_layer.value if actual_cache_layer else None
            
            # Step 3: Cache Miss Handling (if needed)
            if not cache_hit:
                step_start = time.time()
                
                # Generate response (simulated)
                response_data = self._generate_response(user_request)
                
                # Store in cache layers
                for layer in cache_layers:
                    if layer in cache_tools.caches:
                        cache = cache_tools.caches[layer]
                        cache_key = self._generate_cache_key(user_request, layer)
                        
                        store_start = time.time()
                        store_result = await cache.set(cache_key, response_data)
                        store_end = time.time()
                        
                        workflow_result["workflow_steps"].append({
                            "step": "cache_store",
                            "cache_layer": layer.value,
                            "cache_key": cache_key,
                            "duration_ms": (store_end - store_start) * 1000,
                            "success": store_result
                        })
                
                step_end = time.time()
                workflow_result["workflow_steps"].append({
                    "step": "cache_miss_handling",
                    "duration_ms": (step_end - step_start) * 1000,
                    "success": True
                })
            
            # Step 4: Response Generation
            step_start = time.time()
            final_response = self._generate_final_response(response_data, cache_hit)
            step_end = time.time()
            
            workflow_result["workflow_steps"].append({
                "step": "response_generation",
                "duration_ms": (step_end - step_start) * 1000,
                "success": True
            })
            
            workflow_result["response_data"] = final_response
            
        except Exception as e:
            workflow_result["error_occurred"] = True
            workflow_result["error_message"] = str(e)
            self.logger.error(f"Workflow error: {e}")
        
        # Calculate total time
        end_time = time.time()
        workflow_result["total_time_ms"] = (end_time - start_time) * 1000
        
        # Calculate performance metrics
        workflow_result["performance_metrics"] = self._calculate_performance_metrics(workflow_result)
        
        self.workflow_results.append(workflow_result)
        return workflow_result
    
    def _generate_cache_key(self, user_request: str, cache_layer: CacheLayer) -> str:
        """Generate cache key based on user request and cache layer."""
        import hashlib
        key_string = f"{user_request}_{cache_layer.value}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def _generate_response(self, user_request: str) -> str:
        """Generate a simulated response for user request."""
        # Simple keyword-based response generation
        if "capital" in user_request.lower() and "france" in user_request.lower():
            return "The capital of France is Paris."
        elif "machine learning" in user_request.lower():
            return "Machine learning is a subset of AI that enables systems to learn from data."
        elif "binary search" in user_request.lower():
            return "Binary search is an efficient algorithm for finding an item in a sorted array."
        elif "caching" in user_request.lower():
            return "Caching improves performance by storing frequently accessed data in memory."
        elif "microservices" in user_request.lower():
            return "Microservices architecture breaks applications into small, independent services."
        else:
            return f"This is a response to: {user_request}"
    
    def _generate_final_response(self, response_data: str, cache_hit: bool) -> Dict[str, Any]:
        """Generate final response with metadata."""
        return {
            "response": response_data,
            "cache_hit": cache_hit,
            "timestamp": time.time(),
            "metadata": {
                "source": "cache" if cache_hit else "generated",
                "processing_time_ms": len(response_data) * 2  # Simulated processing time
            }
        }
    
    def _calculate_performance_metrics(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for the workflow."""
        steps = workflow_result["workflow_steps"]
        
        total_time = workflow_result["total_time_ms"]
        request_analysis_time = next((s["duration_ms"] for s in steps if s["step"] == "request_analysis"), 0)
        cache_query_time = sum(s["duration_ms"] for s in steps if s["step"] == "cache_query")
        cache_store_time = sum(s["duration_ms"] for s in steps if s["step"] == "cache_store")
        response_generation_time = next((s["duration_ms"] for s in steps if s["step"] == "response_generation"), 0)
        
        return {
            "total_time_ms": total_time,
            "request_analysis_time_ms": request_analysis_time,
            "cache_query_time_ms": cache_query_time,
            "cache_store_time_ms": cache_store_time,
            "response_generation_time_ms": response_generation_time,
            "cache_efficiency": 1.0 if workflow_result["cache_hit"] else 0.0,
            "step_breakdown": {
                "request_analysis": request_analysis_time,
                "cache_query": cache_query_time,
                "cache_store": cache_store_time,
                "response_generation": response_generation_time
            }
        }
    
    def generate_workflow_report(self) -> Dict[str, Any]:
        """Generate comprehensive workflow test report."""
        if not self.workflow_results:
            return {"error": "No workflow results available"}
        
        report = {
            "test_summary": {
                "total_workflows": len(self.workflow_results),
                "cache_hits": sum(1 for w in self.workflow_results if w["cache_hit"]),
                "cache_misses": sum(1 for w in self.workflow_results if w["cache_miss"]),
                "errors": sum(1 for w in self.workflow_results if w["error_occurred"])
            },
            "performance_summary": {
                "avg_total_time_ms": sum(w["total_time_ms"] for w in self.workflow_results) / len(self.workflow_results),
                "avg_cache_query_time_ms": sum(sum(s["duration_ms"] for s in w["workflow_steps"] if s["step"] == "cache_query") for w in self.workflow_results) / len(self.workflow_results),
                "avg_cache_store_time_ms": sum(sum(s["duration_ms"] for s in w["workflow_steps"] if s["step"] == "cache_store") for w in self.workflow_results) / len(self.workflow_results),
                "avg_response_generation_time_ms": sum(sum(s["duration_ms"] for s in w["workflow_steps"] if s["step"] == "response_generation") for w in self.workflow_results) / len(self.workflow_results),
                "cache_hit_rate": sum(1 for w in self.workflow_results if w["cache_hit"]) / len(self.workflow_results)
            },
            "cache_layer_analysis": {
                "expected_vs_actual": {},
                "cache_layer_usage": {}
            },
            "error_analysis": {
                "total_errors": sum(1 for w in self.workflow_results if w["error_occurred"]),
                "error_messages": list(set(w["error_message"] for w in self.workflow_results if w["error_occurred"]))
            },
            "workflow_details": []
        }
        
        # Analyze cache layer expectations vs actual
        for workflow in self.workflow_results:
            expected = workflow["cache_layer_expected"]
            actual = workflow["cache_layer_actual"]
            
            if expected not in report["cache_layer_analysis"]["expected_vs_actual"]:
                report["cache_layer_analysis"]["expected_vs_actual"][expected] = {"correct": 0, "incorrect": 0, "total": 0}
            
            report["cache_layer_analysis"]["expected_vs_actual"][expected]["total"] += 1
            if expected == actual:
                report["cache_layer_analysis"]["expected_vs_actual"][expected]["correct"] += 1
            else:
                report["cache_layer_analysis"]["expected_vs_actual"][expected]["incorrect"] += 1
        
        # Analyze cache layer usage
        for workflow in self.workflow_results:
            actual = workflow["cache_layer_actual"]
            if actual not in report["cache_layer_analysis"]["cache_layer_usage"]:
                report["cache_layer_analysis"]["cache_layer_usage"][actual] = 0
            report["cache_layer_analysis"]["cache_layer_usage"][actual] += 1
        
        # Add workflow details
        for workflow in self.workflow_results:
            report["workflow_details"].append({
                "user_request": workflow["user_request"],
                "cache_layer_expected": workflow["cache_layer_expected"],
                "cache_layer_actual": workflow["cache_layer_actual"],
                "cache_hit": workflow["cache_hit"],
                "cache_miss": workflow["cache_miss"],
                "total_time_ms": workflow["total_time_ms"],
                "error_occurred": workflow["error_occurred"],
                "error_message": workflow["error_message"],
                "performance_metrics": workflow["performance_metrics"]
            })
        
        return report


class TestCompleteWorkflow:
    """Test complete cache workflow scenarios."""
    
    @pytest.fixture
    def cache_tools(self):
        """Create cache tools instance with all cache layers."""
        cache_tools = CacheMCPTools()
        
        # Create cache instances
        predictive_config = PredictiveCacheConfig(cache_ttl_seconds=60, prediction_window_seconds=300)
        semantic_config = SemanticCacheConfig(cache_ttl_seconds=300, similarity_threshold=0.8)
        vector_config = VectorCacheConfig(cache_ttl_seconds=180, similarity_threshold=0.75)
        global_config = GlobalCacheConfig(cache_ttl_seconds=600, rag_server_url="http://localhost:8000")
        vector_diary_config = VectorDiaryConfig(cache_ttl_seconds=86400, max_entries=1000)
        
        predictive_cache = PredictiveCache("test_predictive", predictive_config)
        semantic_cache = SemanticCache("test_semantic", semantic_config)
        vector_cache = VectorCache("test_vector", vector_config)
        global_cache = GlobalCache("test_global", global_config)
        vector_diary = VectorDiary("test_vector_diary", vector_diary_config)
        
        # Initialize all caches
        for cache in [predictive_cache, semantic_cache, vector_cache, global_cache, vector_diary]:
            cache._cache = {}
            asyncio.run(cache.initialize())
        
        # Register caches
        cache_tools.register_cache(predictive_cache)
        cache_tools.register_cache(semantic_cache)
        cache_tools.register_cache(vector_cache)
        cache_tools.register_cache(global_cache)
        cache_tools.register_cache(vector_diary)
        
        return cache_tools
    
    @pytest.mark.asyncio
    async def test_predictive_cache_workflow(self, cache_tools):
        """Test complete workflow with predictive cache."""
        tester = CacheWorkflowTester()
        
        # Test predictive cache request
        user_request = "I'm going to ask about the weather tomorrow"
        expected_layer = CacheLayer.PREDICTIVE
        
        # First request (cache miss)
        result1 = await tester.simulate_complete_workflow(
            user_request, cache_tools, expected_layer
        )
        
        # Second request (cache hit)
        result2 = await tester.simulate_complete_workflow(
            user_request, cache_tools, expected_layer
        )
        
        # Assert workflow results
        assert result1["cache_hit"] is False
        assert result1["cache_miss"] is True
        assert result1["cache_layer_actual"] == expected_layer.value
        assert result1["error_occurred"] is False
        
        assert result2["cache_hit"] is True
        assert result2["cache_miss"] is False
        assert result2["cache_layer_actual"] == expected_layer.value
        assert result2["error_occurred"] is False
        
        # Assert performance improvements
        assert result2["total_time_ms"] < result1["total_time_ms"]
        
        # Generate report
        report = tester.generate_workflow_report()
        
        # Assert report summary
        assert report["test_summary"]["total_workflows"] == 2
        assert report["test_summary"]["cache_hits"] == 1
        assert report["test_summary"]["cache_misses"] == 1
        assert report["test_summary"]["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_semantic_cache_workflow(self, cache_tools):
        """Test complete workflow with semantic cache."""
        tester = CacheWorkflowTester()
        
        # Test semantic cache request
        user_request = "What is the meaning of life in philosophical terms?"
        expected_layer = CacheLayer.SEMANTIC
        
        # First request (cache miss)
        result1 = await tester.simulate_complete_workflow(
            user_request, cache_tools, expected_layer
        )
        
        # Second request with similar meaning (cache hit)
        result2 = await tester.simulate_complete_workflow(
            "Explain the philosophical concept of existence and purpose",
            cache_tools, expected_layer
        )
        
        # Assert workflow results
        assert result1["cache_hit"] is False
        assert result1["cache_miss"] is True
        assert result1["cache_layer_actual"] == expected_layer.value
        assert result1["error_occurred"] is False
        
        assert result2["cache_hit"] is True  # Should hit due to semantic similarity
        assert result2["cache_miss"] is False
        assert result2["cache_layer_actual"] == expected_layer.value
        assert result2["error_occurred"] is False
        
        # Generate report
        report = tester.generate_workflow_report()
        
        # Assert report summary
        assert report["test_summary"]["total_workflows"] == 2
        assert report["test_summary"]["cache_hits"] == 1
        assert report["test_summary"]["cache_misses"] == 1
        assert report["test_summary"]["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_vector_cache_workflow(self, cache_tools):
        """Test complete workflow with vector cache."""
        tester = CacheWorkflowTester()
        
        # Test vector cache request
        user_request = "Find documents similar to machine learning algorithms"
        expected_layer = CacheLayer.VECTOR
        
        # First request (cache miss)
        result1 = await tester.simulate_complete_workflow(
            user_request, cache_tools, expected_layer
        )
        
        # Second request with similar intent (cache hit)
        result2 = await tester.simulate_complete_workflow(
            "Search for content about neural networks and deep learning",
            cache_tools, expected_layer
        )
        
        # Assert workflow results
        assert result1["cache_hit"] is False
        assert result1["cache_miss"] is True
        assert result1["cache_layer_actual"] == expected_layer.value
        assert result1["error_occurred"] is False
        
        assert result2["cache_hit"] is True  # Should hit due to vector similarity
        assert result2["cache_miss"] is False
        assert result2["cache_layer_actual"] == expected_layer.value
        assert result2["error_occurred"] is False
        
        # Generate report
        report = tester.generate_workflow_report()
        
        # Assert report summary
        assert report["test_summary"]["total_workflows"] == 2
        assert report["test_summary"]["cache_hits"] == 1
        assert report["test_summary"]["cache_misses"] == 1
        assert report["test_summary"]["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_global_cache_workflow(self, cache_tools):
        """Test complete workflow with global cache."""
        tester = CacheWorkflowTester()
        
        # Test global cache request
        user_request = "What are the main principles of object-oriented programming?"
        expected_layer = CacheLayer.GLOBAL
        
        # First request (cache miss)
        result1 = await tester.simulate_complete_workflow(
            user_request, cache_tools, expected_layer
        )
        
        # Second request (cache hit)
        result2 = await tester.simulate_complete_workflow(
            user_request, cache_tools, expected_layer
        )
        
        # Assert workflow results
        assert result1["cache_hit"] is False
        assert result1["cache_miss"] is True
        assert result1["cache_layer_actual"] == expected_layer.value
        assert result1["error_occurred"] is False
        
        assert result2["cache_hit"] is True
        assert result2["cache_miss"] is False
        assert result2["cache_layer_actual"] == expected_layer.value
        assert result2["error_occurred"] is False
        
        # Generate report
        report = tester.generate_workflow_report()
        
        # Assert report summary
        assert report["test_summary"]["total_workflows"] == 2
        assert report["test_summary"]["cache_hits"] == 1
        assert report["test_summary"]["cache_misses"] == 1
        assert report["test_summary"]["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_vector_diary_workflow(self, cache_tools):
        """Test complete workflow with vector diary."""
        tester = CacheWorkflowTester()
        
        # Test vector diary request
        user_request = "Remember our conversation about yesterday's meeting"
        expected_layer = CacheLayer.VECTOR_DIARY
        
        # First request (cache miss)
        result1 = await tester.simulate_complete_workflow(
            user_request, cache_tools, expected_layer
        )
        
        # Second request (cache hit)
        result2 = await tester.simulate_complete_workflow(
            user_request, cache_tools, expected_layer
        )
        
        # Assert workflow results
        assert result1["cache_hit"] is False
        assert result1["cache_miss"] is True
        assert result1["cache_layer_actual"] == expected_layer.value
        assert result1["error_occurred"] is False
        
        assert result2["cache_hit"] is True
        assert result2["cache_miss"] is False
        assert result2["cache_layer_actual"] == expected_layer.value
        assert result2["error_occurred"] is False
        
        # Generate report
        report = tester.generate_workflow_report()
        
        # Assert report summary
        assert report["test_summary"]["total_workflows"] == 2
        assert report["test_summary"]["cache_hits"] == 1
        assert report["test_summary"]["cache_misses"] == 1
        assert report["test_summary"]["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_cross_cache_workflow(self, cache_tools):
        """Test complete workflow with cross-cache routing."""
        tester = CacheWorkflowTester()
        
        # Test requests that should route to multiple cache layers
        test_requests = [
            ("What will the weather be like tomorrow?", CacheLayer.PREDICTIVE),
            ("Explain the concept of artificial intelligence", CacheLayer.SEMANTIC),
            ("Find similar documents about climate change", CacheLayer.VECTOR),
            ("What are the SOLID principles in software design?", CacheLayer.GLOBAL),
            ("Remember what we discussed about project deadlines", CacheLayer.VECTOR_DIARY)
        ]
        
        results = []
        for user_request, expected_layer in test_requests:
            result = await tester.simulate_complete_workflow(
                user_request, cache_tools, expected_layer
            )
            results.append(result)
        
        # Assert all workflows completed successfully
        for result in results:
            assert result["error_occurred"] is False
            assert result["cache_layer_actual"] == expected_layer.value
        
        # Generate report
        report = tester.generate_workflow_report()
        
        # Assert report summary
        assert report["test_summary"]["total_workflows"] == len(test_requests)
        assert report["test_summary"]["errors"] == 0
        
        # Assert all cache layers were used
        assert len(report["cache_layer_analysis"]["cache_layer_usage"]) == len(test_requests)
    
    @pytest.mark.asyncio
    async def test_fallback_workflow(self, cache_tools):
        """Test complete workflow with fallback mechanisms."""
        tester = CacheWorkflowTester()
        
        # Test request that should fallback through multiple cache layers
        user_request = "What is the meaning of life?"
        
        # Simulate primary cache failure
        with patch.object(cache_tools.caches[CacheLayer.SEMANTIC], 'get', side_effect=Exception("Semantic cache failed")):
            result = await tester.simulate_complete_workflow(
                user_request, cache_tools, CacheLayer.SEMANTIC
            )
        
        # Assert fallback behavior
        assert result["error_occurred"] is False  # Should handle fallback gracefully
        assert result["cache_layer_actual"] is not None  # Should use fallback cache
        
        # Generate report
        report = tester.generate_workflow_report()
        
        # Assert report summary
        assert report["test_summary"]["total_workflows"] == 1
        assert report["test_summary"]["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow(self, cache_tools):
        """Test complete workflow with concurrent requests."""
        tester = CacheWorkflowTester()
        
        # Test concurrent requests
        concurrent_requests = [
            "What is the capital of France?",
            "Explain machine learning",
            "How do I implement binary search?",
            "What are the benefits of caching?",
            "Describe microservices architecture"
        ]
        
        async def process_request(request):
            expected_layer = CacheLayer.SEMANTIC  # All requests should go to semantic cache
            return await tester.simulate_complete_workflow(request, cache_tools, expected_layer)
        
        # Process requests concurrently
        start_time = time.time()
        results = await asyncio.gather(*[process_request(req) for req in concurrent_requests])
        end_time = time.time()
        
        # Assert all workflows completed successfully
        for result in results:
            assert result["error_occurred"] is False
        
        # Assert reasonable concurrent performance
        total_time = (end_time - start_time) * 1000
        avg_time_per_request = total_time / len(concurrent_requests)
        assert avg_time_per_request < 100  # Should be fast under concurrent load
        
        # Generate report
        report = tester.generate_workflow_report()
        
        # Assert report summary
        assert report["test_summary"]["total_workflows"] == len(concurrent_requests)
        assert report["test_summary"]["errors"] == 0
        assert report["performance_summary"]["avg_total_time_ms"] < 100


class TestMCPIntegrationWorkflow:
    """Test MCP integration with complete workflow."""
    
    @pytest.mark.asyncio
    async def test_mcp_server_workflow(self):
        """Test complete workflow through MCP server."""
        # Create mock cache tools
        cache_tools = Mock()
        cache_tools.caches = {
            CacheLayer.PREDICTIVE: Mock(),
            CacheLayer.SEMANTIC: Mock(),
            CacheLayer.VECTOR: Mock(),
            CacheLayer.GLOBAL: Mock(),
            CacheLayer.VECTOR_DIARY: Mock()
        }
        
        # Mock cache operations
        for cache in cache_tools.caches.values():
            cache.get_layer.return_value = CacheLayer.SEMANTIC  # Default to semantic
            cache.get = AsyncMock(return_value=CacheResult(
                status=CacheStatus.HIT,
                entry=Mock(value="Mock response")
            ))
            cache.set = AsyncMock(return_value=True)
        
        # Mock cache layer determination
        cache_tools._determine_cache_layers = Mock(return_value=[CacheLayer.SEMANTIC])
        
        # Create mock context
        mock_context = Mock()
        mock_context.request_context = Mock()
        mock_context.request_context.lifespan_context = Mock()
        mock_context.request_context.lifespan_context.cache_tools = cache_tools
        
        # Test MCP server workflow
        from src.mcp.server import cache_get
        
        user_request = "test_key"
        result = await cache_get(user_request, mock_context)
        
        # Assert MCP workflow
        assert result["success"] is True
        assert result["status"] == "hit"
        assert result["data"] == "Mock response"
        
        # Verify cache tools were called
        cache_tools._determine_cache_layers.assert_called_once_with(user_request)
        cache_tools.caches[CacheLayer.SEMANTIC].get.assert_called_once()


class TestRealWorldWorkflow:
    """Test real-world workflow scenarios."""
    
    @pytest.mark.asyncio
    async def test_conversation_workflow(self, cache_tools):
        """Test real-world conversation workflow."""
        tester = CacheWorkflowTester()
        
        # Simulate a conversation
        conversation = [
            "Hello, I need help with my programming assignment",
            "Can you explain what a binary search is?",
            "How do I implement it in Python?",
            "What are the time and space complexities?",
            "Thanks for the explanation!"
        ]
        
        results = []
        for i, message in enumerate(conversation):
            # Determine expected cache layer based on message type
            if "help" in message.lower() or "hello" in message.lower():
                expected_layer = CacheLayer.SEMANTIC
            elif "explain" in message.lower() or "implement" in message.lower():
                expected_layer = CacheLayer.VECTOR
            elif "complexities" in message.lower():
                expected_layer = CacheLayer.GLOBAL
            else:
                expected_layer = CacheLayer.SEMANTIC
            
            result = await tester.simulate_complete_workflow(
                message, cache_tools, expected_layer
            )
            results.append(result)
        
        # Assert conversation workflow
        assert len(results) == len(conversation)
        for result in results:
            assert result["error_occurred"] is False
        
        # Generate report
        report = tester.generate_workflow_report()
        
        # Assert report summary
        assert report["test_summary"]["total_workflows"] == len(conversation)
        assert report["test_summary"]["errors"] == 0
        
        # Assert cache hit rate improvement over time
        cache_hits = sum(1 for r in results if r["cache_hit"])
        cache_hit_rate = cache_hits / len(results)
        assert cache_hit_rate > 0.3  # Should have some cache hits in conversation
    
    @pytest.mark.asyncio
    async def test_multi_session_workflow(self, cache_tools):
        """Test multi-session workflow."""
        tester = CacheWorkflowTester()
        
        # Simulate multiple user sessions
        sessions = [
            ["What is machine learning?", "Explain supervised learning"],
            ["How does neural network work?", "What are activation functions?"],
            ["What is deep learning?", "Explain convolutional neural networks"]
        ]
        
        all_results = []
        for session_id, session in enumerate(sessions):
            session_results = []
            for message in session:
                # Add session context to message
                contextual_message = f"[Session {session_id}] {message}"
                
                expected_layer = CacheLayer.SEMANTIC if "explain" in message.lower() else CacheLayer.VECTOR
                
                result = await tester.simulate_complete_workflow(
                    contextual_message, cache_tools, expected_layer
                )
                session_results.append(result)
            
            all_results.extend(session_results)
        
        # Assert multi-session workflow
        assert len(all_results) == sum(len(session) for session in sessions)
        for result in all_results:
            assert result["error_occurred"] is False
        
        # Generate report
        report = tester.generate_workflow_report()
        
        # Assert report summary
        assert report["test_summary"]["total_workflows"] == len(all_results)
        assert report["test_summary"]["errors"] == 0
        
        # Assert session isolation
        session_cache_hits = {}
        for result in all_results:
            session_id = result["user_request"].split("]")[0].replace("[Session ", "")
            if session_id not in session_cache_hits:
                session_cache_hits[session_id] = {"hits": 0, "total": 0}
            
            session_cache_hits[session_id]["total"] += 1
            if result["cache_hit"]:
                session_cache_hits[session_id]["hits"] += 1
        
        # Each session should have independent cache behavior
        assert len(session_cache_hits) == len(sessions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])