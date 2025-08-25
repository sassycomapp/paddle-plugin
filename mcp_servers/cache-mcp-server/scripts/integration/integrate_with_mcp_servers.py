#!/usr/bin/env python3
"""
Integration Script for Cache MCP Server with Existing MCP Servers

This script handles the integration of the cache MCP server with:
- MCP RAG Server (Global Knowledge Cache)
- Vector Store MCP
- Memory Bank Files
- KiloCode Orchestration

Author: KiloCode
License: Apache 2.0
"""

import os
import sys
import logging
import asyncio
import json
import yaml
import aiohttp
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MCPIntegrationConfig:
    """Configuration for MCP server integration."""
    # MCP RAG Server
    rag_server_enabled: bool = True
    rag_server_endpoint: str = "http://localhost:8001"
    rag_server_timeout: int = 30
    rag_server_retry_attempts: int = 3
    rag_server_fallback_enabled: bool = True
    
    # Vector Store MCP
    vector_store_enabled: bool = True
    vector_store_endpoint: str = "http://localhost:8002"
    vector_store_timeout: int = 30
    vector_store_retry_attempts: int = 3
    vector_store_fallback_enabled: bool = True
    
    # Memory Bank
    memory_bank_enabled: bool = True
    memory_bank_path: str = "./memorybank"
    memory_bank_sync_interval: int = 300
    memory_bank_sync_direction: str = "bidirectional"
    
    # KiloCode Orchestration
    kilocode_enabled: bool = True
    kilocode_endpoint: str = "http://localhost:8080"
    kilocode_timeout: int = 30
    kilocode_retry_attempts: int = 3
    
    # Integration Settings
    integration_enabled: bool = True
    sync_interval: int = 300
    batch_size: int = 100
    retry_attempts: int = 3
    retry_delay: int = 1
    circuit_breaker_threshold: float = 0.2


class MCPIntegrator:
    """Handles integration with external MCP servers."""
    
    def __init__(self, config: MCPIntegrationConfig):
        """Initialize integrator."""
        self.config = config
        self.project_root = Path(__file__).parent.parent.parent
        self.logger = logging.getLogger(__name__)
        self.session = None
        
    async def initialize(self):
        """Initialize the integrator."""
        try:
            self.logger.info("Initializing MCP integrator...")
            
            # Create aiohttp session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=100)
            )
            
            # Test connections
            await self._test_connections()
            
            self.logger.info("MCP integrator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP integrator: {e}")
            raise
    
    async def close(self):
        """Close the integrator."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _test_connections(self):
        """Test connections to external services."""
        try:
            self.logger.info("Testing connections to external services...")
            
            # Test MCP RAG Server
            if self.config.rag_server_enabled:
                try:
                    async with self.session.get(
                        f"{self.config.rag_server_endpoint}/health",
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            self.logger.info("MCP RAG Server connection successful")
                        else:
                            self.logger.warning(f"MCP RAG Server health check failed: {response.status}")
                except Exception as e:
                    self.logger.error(f"MCP RAG Server connection failed: {e}")
            
            # Test Vector Store MCP
            if self.config.vector_store_enabled:
                try:
                    async with self.session.get(
                        f"{self.config.vector_store_endpoint}/health",
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            self.logger.info("Vector Store MCP connection successful")
                        else:
                            self.logger.warning(f"Vector Store MCP health check failed: {response.status}")
                except Exception as e:
                    self.logger.error(f"Vector Store MCP connection failed: {e}")
            
            # Test KiloCode Orchestration
            if self.config.kilocode_enabled:
                try:
                    async with self.session.get(
                        f"{self.config.kilocode_endpoint}/health",
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            self.logger.info("KiloCode Orchestration connection successful")
                        else:
                            self.logger.warning(f"KiloCode Orchestration health check failed: {response.status}")
                except Exception as e:
                    self.logger.error(f"KiloCode Orchestration connection failed: {e}")
            
            # Test Memory Bank
            if self.config.memory_bank_enabled:
                memory_bank_path = Path(self.config.memory_bank_path)
                if memory_bank_path.exists():
                    self.logger.info("Memory Bank path exists")
                else:
                    self.logger.warning(f"Memory Bank path does not exist: {memory_bank_path}")
                    memory_bank_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info("Created Memory Bank path")
            
            self.logger.info("Connection tests completed")
            
        except Exception as e:
            self.logger.error(f"Connection tests failed: {e}")
            raise
    
    async def integrate_with_rag_server(self):
        """Integrate with MCP RAG Server."""
        try:
            self.logger.info("Integrating with MCP RAG Server...")
            
            # Get RAG server capabilities
            async with self.session.get(
                f"{self.config.rag_server_endpoint}/capabilities"
            ) as response:
                if response.status == 200:
                    capabilities = await response.json()
                    self.logger.info(f"RAG Server capabilities: {capabilities}")
                else:
                    self.logger.warning(f"Failed to get RAG Server capabilities: {response.status}")
            
            # Sync global cache with RAG server
            await self._sync_global_cache_with_rag()
            
            # Configure tool mapping
            await self._configure_rag_tool_mapping()
            
            self.logger.info("Integration with MCP RAG Server completed")
            
        except Exception as e:
            self.logger.error(f"Integration with MCP RAG Server failed: {e}")
            raise
    
    async def integrate_with_vector_store(self):
        """Integrate with Vector Store MCP."""
        try:
            self.logger.info("Integrating with Vector Store MCP...")
            
            # Get vector store capabilities
            async with self.session.get(
                f"{self.config.vector_store_endpoint}/capabilities"
            ) as response:
                if response.status == 200:
                    capabilities = await response.json()
                    self.logger.info(f"Vector Store capabilities: {capabilities}")
                else:
                    self.logger.warning(f"Failed to get Vector Store capabilities: {response.status}")
            
            # Sync vector cache with vector store
            await self._sync_vector_cache_with_vector_store()
            
            # Configure tool mapping
            await self._configure_vector_store_tool_mapping()
            
            self.logger.info("Integration with Vector Store MCP completed")
            
        except Exception as e:
            self.logger.error(f"Integration with Vector Store MCP failed: {e}")
            raise
    
    async def integrate_with_memory_bank(self):
        """Integrate with Memory Bank files."""
        try:
            self.logger.info("Integrating with Memory Bank...")
            
            # Check memory bank directory
            memory_bank_path = Path(self.config.memory_bank_path)
            if not memory_bank_path.exists():
                memory_bank_path.mkdir(parents=True, exist_ok=True)
                self.logger.info("Created Memory Bank directory")
            
            # Sync with memory bank
            await self._sync_with_memory_bank()
            
            # Configure memory bank sync
            await self._configure_memory_bank_sync()
            
            self.logger.info("Integration with Memory Bank completed")
            
        except Exception as e:
            self.logger.error(f"Integration with Memory Bank failed: {e}")
            raise
    
    async def integrate_with_kilocode(self):
        """Integrate with KiloCode Orchestration."""
        try:
            self.logger.info("Integrating with KiloCode Orchestration...")
            
            # Get KiloCode capabilities
            async with self.session.get(
                f"{self.config.kilocode_endpoint}/capabilities"
            ) as response:
                if response.status == 200:
                    capabilities = await response.json()
                    self.logger.info(f"KiloCode capabilities: {capabilities}")
                else:
                    self.logger.warning(f"Failed to get KiloCode capabilities: {response.status}")
            
            # Configure cache routing
            await self._configure_kilocode_routing()
            
            # Register cache tools
            await self._register_cache_tools_with_kilocode()
            
            self.logger.info("Integration with KiloCode Orchestration completed")
            
        except Exception as e:
            self.logger.error(f"Integration with KiloCode Orchestration failed: {e}")
            raise
    
    async def _sync_global_cache_with_rag(self):
        """Sync global cache with RAG server."""
        try:
            self.logger.info("Syncing global cache with RAG server...")
            
            # Get knowledge from RAG server
            async with self.session.post(
                f"{self.config.rag_server_endpoint}/search",
                json={"query": "*"},
                timeout=30
            ) as response:
                if response.status == 200:
                    knowledge_items = await response.json()
                    
                    # Store in global cache
                    for item in knowledge_items:
                        await self._store_in_global_cache(item)
                    
                    self.logger.info(f"Synced {len(knowledge_items)} items to global cache")
                else:
                    self.logger.warning(f"Failed to sync with RAG server: {response.status}")
            
        except Exception as e:
            self.logger.error(f"Failed to sync global cache with RAG server: {e}")
            raise
    
    async def _sync_vector_cache_with_vector_store(self):
        """Sync vector cache with vector store."""
        try:
            self.logger.info("Syncing vector cache with vector store...")
            
            # Get vectors from vector store
            async with self.session.post(
                f"{self.config.vector_store_endpoint}/search",
                json={"query": "*", "n_results": 100},
                timeout=30
            ) as response:
                if response.status == 200:
                    vector_items = await response.json()
                    
                    # Store in vector cache
                    for item in vector_items:
                        await self._store_in_vector_cache(item)
                    
                    self.logger.info(f"Synced {len(vector_items)} items to vector cache")
                else:
                    self.logger.warning(f"Failed to sync with vector store: {response.status}")
            
        except Exception as e:
            self.logger.error(f"Failed to sync vector cache with vector store: {e}")
            raise
    
    async def _sync_with_memory_bank(self):
        """Sync with memory bank files."""
        try:
            self.logger.info("Syncing with memory bank...")
            
            memory_bank_path = Path(self.config.memory_bank_path)
            
            # Process memory bank files
            for file_path in memory_bank_path.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        memory_data = json.load(f)
                    
                    # Store in vector diary
                    for memory_item in memory_data.get("memories", []):
                        await self._store_in_vector_diary(memory_item)
                    
                    self.logger.info(f"Processed memory file: {file_path}")
                
                except Exception as e:
                    self.logger.error(f"Failed to process memory file {file_path}: {e}")
            
            self.logger.info("Memory bank sync completed")
            
        except Exception as e:
            self.logger.error(f"Failed to sync with memory bank: {e}")
            raise
    
    async def _configure_rag_tool_mapping(self):
        """Configure tool mapping with RAG server."""
        try:
            self.logger.info("Configuring RAG tool mapping...")
            
            # Define tool mappings
            tool_mappings = [
                {
                    "cache_tool": "global_cache_search_knowledge",
                    "rag_tool": "rag_search",
                    "mapping_type": "direct"
                },
                {
                    "cache_tool": "global_cache_add_knowledge",
                    "rag_tool": "rag_index",
                    "mapping_type": "direct"
                }
            ]
            
            # Store tool mappings
            mappings_file = self.project_root / "config" / "rag_tool_mappings.json"
            with open(mappings_file, 'w') as f:
                json.dump(tool_mappings, f, indent=2)
            
            self.logger.info("RAG tool mappings configured")
            
        except Exception as e:
            self.logger.error(f"Failed to configure RAG tool mapping: {e}")
            raise
    
    async def _configure_vector_store_tool_mapping(self):
        """Configure tool mapping with vector store."""
        try:
            self.logger.info("Configuring vector store tool mapping...")
            
            # Define tool mappings
            tool_mappings = [
                {
                    "cache_tool": "vector_cache_select_context",
                    "vector_tool": "vector_search",
                    "mapping_type": "direct"
                },
                {
                    "cache_tool": "semantic_cache_similar",
                    "vector_tool": "semantic_search",
                    "mapping_type": "direct"
                },
                {
                    "cache_tool": "vector_cache_add_vector",
                    "vector_tool": "vector_index",
                    "mapping_type": "direct"
                }
            ]
            
            # Store tool mappings
            mappings_file = self.project_root / "config" / "vector_store_tool_mappings.json"
            with open(mappings_file, 'w') as f:
                json.dump(tool_mappings, f, indent=2)
            
            self.logger.info("Vector store tool mappings configured")
            
        except Exception as e:
            self.logger.error(f"Failed to configure vector store tool mapping: {e}")
            raise
    
    async def _configure_memory_bank_sync(self):
        """Configure memory bank synchronization."""
        try:
            self.logger.info("Configuring memory bank sync...")
            
            # Create sync configuration
            sync_config = {
                "enabled": True,
                "sync_interval": self.config.memory_bank_sync_interval,
                "sync_direction": self.config.memory_bank_sync_direction,
                "batch_size": self.config.batch_size,
                "retry_attempts": self.config.retry_attempts,
                "retry_delay": self.config.retry_delay
            }
            
            # Store sync configuration
            sync_file = self.project_root / "config" / "memory_bank_sync.json"
            with open(sync_file, 'w') as f:
                json.dump(sync_config, f, indent=2)
            
            self.logger.info("Memory bank sync configured")
            
        except Exception as e:
            self.logger.error(f"Failed to configure memory bank sync: {e}")
            raise
    
    async def _configure_kilocode_routing(self):
        """Configure KiloCode routing."""
        try:
            self.logger.info("Configuring KiloCode routing...")
            
            # Create routing configuration
            routing_config = {
                "enabled": True,
                "routing_logic": "smart",
                "fallback_order": ["predictive", "semantic", "vector", "global"],
                "routing_rules": [
                    {
                        "pattern": "predict.*",
                        "layer": "predictive",
                        "priority": 1,
                        "enabled": True
                    },
                    {
                        "pattern": "semantic.*|similar.*|context.*",
                        "layer": "semantic",
                        "priority": 2,
                        "enabled": True
                    },
                    {
                        "pattern": "vector.*|embedding.*",
                        "layer": "vector",
                        "priority": 3,
                        "enabled": True
                    },
                    {
                        "pattern": "knowledge.*|fact.*|information.*",
                        "layer": "global",
                        "priority": 4,
                        "enabled": True
                    }
                ]
            }
            
            # Store routing configuration
            routing_file = self.project_root / "config" / "kilocode_routing.json"
            with open(routing_file, 'w') as f:
                json.dump(routing_config, f, indent=2)
            
            self.logger.info("KiloCode routing configured")
            
        except Exception as e:
            self.logger.error(f"Failed to configure KiloCode routing: {e}")
            raise
    
    async def _register_cache_tools_with_kilocode(self):
        """Register cache tools with KiloCode."""
        try:
            self.logger.info("Registering cache tools with KiloCode...")
            
            # Define cache tools
            cache_tools = [
                {
                    "name": "cache_get",
                    "description": "Get a value from the cache",
                    "parameters": [
                        {
                            "name": "key",
                            "type": "string",
                            "required": true,
                            "description": "Cache key to retrieve"
                        },
                        {
                            "name": "layer",
                            "type": "string",
                            "required": false,
                            "description": "Specific cache layer to use"
                        }
                    ]
                },
                {
                    "name": "cache_set",
                    "description": "Store a value in the cache",
                    "parameters": [
                        {
                            "name": "key",
                            "type": "string",
                            "required": true,
                            "description": "Cache key"
                        },
                        {
                            "name": "value",
                            "type": "any",
                            "required": true,
                            "description": "Value to store"
                        },
                        {
                            "name": "layer",
                            "type": "string",
                            "required": false,
                            "description": "Specific cache layer to use"
                        }
                    ]
                },
                {
                    "name": "cache_stats",
                    "description": "Get overall cache statistics",
                    "parameters": []
                }
            ]
            
            # Register tools with KiloCode
            for tool in cache_tools:
                async with self.session.post(
                    f"{self.config.kilocode_endpoint}/tools/register",
                    json=tool,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Registered tool: {tool['name']}")
                    else:
                        self.logger.warning(f"Failed to register tool {tool['name']}: {response.status}")
            
            self.logger.info("Cache tools registered with KiloCode")
            
        except Exception as e:
            self.logger.error(f"Failed to register cache tools with KiloCode: {e}")
            raise
    
    async def _store_in_global_cache(self, item: Dict[str, Any]):
        """Store an item in the global cache."""
        try:
            # This would typically call the cache MCP server API
            async with self.session.post(
                f"{self.config.kilocode_endpoint}/cache/set",
                json={
                    "key": f"global_{item['id']}",
                    "value": item,
                    "layer": "global"
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    self.logger.debug(f"Stored item in global cache: {item['id']}")
                else:
                    self.logger.warning(f"Failed to store item in global cache: {response.status}")
        
        except Exception as e:
            self.logger.error(f"Failed to store item in global cache: {e}")
    
    async def _store_in_vector_cache(self, item: Dict[str, Any]):
        """Store an item in the vector cache."""
        try:
            # This would typically call the cache MCP server API
            async with self.session.post(
                f"{self.config.kilocode_endpoint}/cache/set",
                json={
                    "key": f"vector_{item['id']}",
                    "value": item,
                    "layer": "vector"
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    self.logger.debug(f"Stored item in vector cache: {item['id']}")
                else:
                    self.logger.warning(f"Failed to store item in vector cache: {response.status}")
        
        except Exception as e:
            self.logger.error(f"Failed to store item in vector cache: {e}")
    
    async def _store_in_vector_diary(self, item: Dict[str, Any]):
        """Store an item in the vector diary."""
        try:
            # This would typically call the cache MCP server API
            async with self.session.post(
                f"{self.config.kilocode_endpoint}/cache/set",
                json={
                    "key": f"diary_{item['id']}",
                    "value": item,
                    "layer": "vector_diary"
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    self.logger.debug(f"Stored item in vector diary: {item['id']}")
                else:
                    self.logger.warning(f"Failed to store item in vector diary: {response.status}")
        
        except Exception as e:
            self.logger.error(f"Failed to store item in vector diary: {e}")
    
    async def run_integration(self):
        """Run the complete integration process."""
        try:
            self.logger.info("Starting MCP server integration...")
            
            # Initialize
            await self.initialize()
            
            # Run integrations
            if self.config.rag_server_enabled:
                await self.integrate_with_rag_server()
            
            if self.config.vector_store_enabled:
                await self.integrate_with_vector_store()
            
            if self.config.memory_bank_enabled:
                await self.integrate_with_memory_bank()
            
            if self.config.kilocode_enabled:
                await self.integrate_with_kilocode()
            
            self.logger.info("MCP server integration completed successfully!")
            
        except Exception as e:
            self.logger.error(f"MCP server integration failed: {e}")
            raise
        finally:
            await self.close()


async def main():
    """Main entry point for integration."""
    try:
        # Create integration configuration
        config = MCPIntegrationConfig(
            rag_server_enabled=True,
            rag_server_endpoint="http://localhost:8001",
            vector_store_enabled=True,
            vector_store_endpoint="http://localhost:8002",
            memory_bank_enabled=True,
            memory_bank_path="./memorybank",
            kilocode_enabled=True,
            kilocode_endpoint="http://localhost:8080"
        )
        
        # Initialize integrator
        integrator = MCPIntegrator(config)
        
        # Run integration
        await integrator.run_integration()
        
        print("\nMCP server integration completed successfully!")
        print("The cache MCP server is now integrated with all external services.")
        
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        print(f"Integration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())