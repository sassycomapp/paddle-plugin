#!/usr/bin/env python3
"""
Simple test script to verify AG2 orchestration system functionality
"""
import sys
import os
import asyncio
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import AG2 modules
from ag2_pure import AG2Orchestrator, AG2Agent, MockMemory, MockRAG, MockSearch

async def test_basic_functionality():
    """Test basic AG2 functionality"""
    print("Testing basic AG2 functionality...")
    
    # Test memory
    memory = MockMemory()
    memory.store_conversation("test_agent", "user", "Hello, what is AG2?")
    memory.store_conversation("test_agent", "assistant", "AG2 is a multi-agent orchestration system.")
    
    results = memory.search_conversations("AG2")
    assert len(results) > 0, "Memory search should return results"
    print("✓ Memory system works")
    
    # Test RAG
    rag = MockRAG()
    rag.documents = {
        "doc1": {"content": "AG2 is an advanced orchestration system", "metadata": {}},
        "doc2": {"content": "It coordinates multiple AI agents", "metadata": {}}
    }
    
    results = rag.search("AG2")
    assert len(results) > 0, "RAG search should return results"
    print("✓ RAG system works")
    
    # Test search
    search = MockSearch()
    results = search.search("AG2")
    assert len(results) > 0, "Search should return results"
    print("✓ Search system works")
    
    # Test agent
    agent = AG2Agent("test_agent", "test_role", ["rag", "search"])
    result = await agent.process_task("What is AG2?")
    assert result is not None, "Agent should process task"
    assert "test_agent" in result["agent"], "Agent should be identified"
    print("✓ Agent system works")
    
    # Test orchestrator
    orchestrator = AG2Orchestrator()
    result = await orchestrator.run_query("What is AG2?")
    assert result is not None, "Orchestrator should process query"
    assert "researcher" in result.lower(), "Should use researcher agent"
    print("✓ Orchestrator system works")

async def test_agent_selection():
    """Test agent selection logic"""
    print("\nTesting agent selection...")
    
    orchestrator = AG2Orchestrator()
    
    # Test researcher selection
    query1 = "What is AG2?"
    agent1 = orchestrator.select_agent(query1)
    assert agent1 == "researcher", f"Should select researcher, got {agent1}"
    print("✓ Researcher selection works")
    
    # Test coordinator selection
    query2 = "Coordinate the workflow"
    agent2 = orchestrator.select_agent(query2)
    assert agent2 == "coordinator", f"Should select coordinator, got {agent2}"
    print("✓ Coordinator selection works")
    
    # Test analyst selection
    query3 = "Analyze the data"
    agent3 = orchestrator.select_agent(query3)
    assert agent3 == "analyst", f"Should select analyst, got {agent3}"
    print("✓ Analyst selection works")

async def test_error_handling():
    """Test error handling"""
    print("\nTesting error handling...")
    
    orchestrator = AG2Orchestrator()
    
    # Test with empty query
    result = await orchestrator.run_query("")
    assert result is not None, "Should handle empty query"
    print("✓ Empty query handling works")
    
    # Test with special characters
    result = await orchestrator.run_query("!!! @#$")
    assert result is not None, "Should handle special characters"
    print("✓ Special character handling works")

async def test_concurrent_queries():
    """Test concurrent query processing"""
    print("\nTesting concurrent queries...")
    
    orchestrator = AG2Orchestrator()
    
    queries = [
        "What is AG2?",
        "How does it work?",
        "What are the benefits?"
    ]
    
    tasks = [orchestrator.run_query(q) for q in queries]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == len(queries), "Should process all queries"
    assert all(result is not None for result in results), "All results should be valid"
    print("✓ Concurrent query processing works")

async def main():
    """Main test function"""
    print("=" * 60)
    print("  AG2 Orchestration System - Test Suite")
    print("=" * 60)
    
    try:
        await test_basic_functionality()
        await test_agent_selection()
        await test_error_handling()
        await test_concurrent_queries()
        
        print("\n" + "=" * 60)
        print("  ✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
