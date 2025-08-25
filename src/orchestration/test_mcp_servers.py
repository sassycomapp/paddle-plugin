import asyncio
import logging
import os
import yaml
from ag2_orchestrator import AG2Orchestrator
from autogen import LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_mcp_servers():
    """Test MCP server connections."""
    logger.info("Starting MCP Server Tests...")
    
    # Use dummy LLM config for testing MCP servers
    llm_config = LLMConfig(
        model="dummy-model-for-testing",
        api_type="openai",
        api_key="dummy-key-for-testing",
        base_url=None
    )
    
    orchestrator = AG2Orchestrator(llm_config=llm_config)
    
    # Test RAG server
    logger.info("Testing RAG MCP server...")
    try:
        await orchestrator.setup_mcp_session(
            "rag", 
            "node", 
            ["../../mcp_servers/rag-mcp-server.js"]
        )
        await orchestrator.create_toolkit("rag")
        logger.info("✓ RAG server connected")
        
        # Test RAG functionality
        rag_tools = orchestrator.get_tools("rag")
        logger.info(f"RAG tools available: {list(rag_tools.keys())}")
        
    except Exception as e:
        logger.error(f"✗ RAG server failed: {e}")
    
    # Test Agent Memory server
    logger.info("Testing Agent Memory MCP server...")
    try:
        await orchestrator.setup_mcp_session(
            "agent-memory", 
            "node", 
            ["../../mcp_servers/agent-memory/index.js"]
        )
        await orchestrator.create_toolkit("agent-memory")
        logger.info("✓ Agent Memory server connected")
        
        # Test Agent Memory functionality
        memory_tools = orchestrator.get_tools("agent-memory")
        logger.info(f"Agent Memory tools available: {list(memory_tools.keys())}")
        
    except Exception as e:
        logger.error(f"✗ Agent Memory server failed: {e}")
    
    # Test Brave Search server
    logger.info("Testing Brave Search MCP server...")
    try:
        await orchestrator.setup_mcp_session(
            "brave-search", 
            "node", 
            ["../../mcp_servers/brave-search-mcp-server.js"]
        )
        await orchestrator.create_toolkit("brave-search")
        logger.info("✓ Brave Search server connected")
        
        # Test Brave Search functionality
        brave_tools = orchestrator.get_tools("brave-search")
        logger.info(f"Brave Search tools available: {list(brave_tools.keys())}")
        
    except Exception as e:
        logger.error(f"✗ Brave Search server failed: {e}")
    
    # Cleanup
    await orchestrator.aclose()
    logger.info("MCP Server Tests completed")

if __name__ == "__main__":
    asyncio.run(test_mcp_servers())
