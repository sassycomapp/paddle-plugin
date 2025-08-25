#!/usr/bin/env python3
"""
Integration Script for EasyOCR MCP Server with Existing MCP Servers

This script handles the integration of the EasyOCR MCP server with:
- Cache MCP Server
- Memory Bank Files
- KiloCode Orchestration
- Core OCR System

Author: Kilo Code
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
    # Cache MCP Server
    cache_server_enabled: bool = True
    cache_server_endpoint: str = "http://localhost:8001"
    cache_server_timeout: int = 30
    cache_server_retry_attempts: int = 3
    cache_server_fallback_enabled: bool = True
    
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
    
    # Core OCR System
    ocr_system_enabled: bool = True
    ocr_system_endpoint: str = "http://localhost:9000"
    ocr_system_timeout: int = 30
    ocr_system_retry_attempts: int = 3
    
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
            self.logger.info("Initializing EasyOCR MCP integrator...")
            
            # Create aiohttp session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=100)
            )
            
            # Test connections
            await self._test_connections()
            
            self.logger.info("EasyOCR MCP integrator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize EasyOCR MCP integrator: {e}")
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
            
            # Test Cache MCP Server
            if self.config.cache_server_enabled:
                try:
                    async with self.session.get(
                        f"{self.config.cache_server_endpoint}/health",
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            self.logger.info("Cache MCP Server connection successful")
                        else:
                            self.logger.warning(f"Cache MCP Server health check failed: {response.status}")
                except Exception as e:
                    self.logger.error(f"Cache MCP Server connection failed: {e}")
            
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
            
            # Test Core OCR System
            if self.config.ocr_system_enabled:
                try:
                    async with self.session.get(
                        f"{self.config.ocr_system_endpoint}/health",
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            self.logger.info("Core OCR System connection successful")
                        else:
                            self.logger.warning(f"Core OCR System health check failed: {response.status}")
                except Exception as e:
                    self.logger.error(f"Core OCR System connection failed: {e}")
            
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
    
    async def integrate_with_cache_server(self):
        """Integrate with Cache MCP Server."""
        try:
            self.logger.info("Integrating with Cache MCP Server...")
            
            # Get cache server capabilities
            async with self.session.get(
                f"{self.config.cache_server_endpoint}/capabilities"
            ) as response:
                if response.status == 200:
                    capabilities = await response.json()
                    self.logger.info(f"Cache Server capabilities: {capabilities}")
                else:
                    self.logger.warning(f"Failed to get Cache Server capabilities: {response.status}")
            
            # Configure OCR caching
            await self._configure_ocr_caching()
            
            # Register OCR tools with cache
            await self._register_ocr_tools_with_cache()
            
            self.logger.info("Integration with Cache MCP Server completed")
            
        except Exception as e:
            self.logger.error(f"Integration with Cache MCP Server failed: {e}")
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
            
            # Configure OCR routing
            await self._configure_ocr_routing()
            
            # Register OCR tools
            await self._register_ocr_tools_with_kilocode()
            
            self.logger.info("Integration with KiloCode Orchestration completed")
            
        except Exception as e:
            self.logger.error(f"Integration with KiloCode Orchestration failed: {e}")
            raise
    
    async def integrate_with_ocr_system(self):
        """Integrate with Core OCR System."""
        try:
            self.logger.info("Integrating with Core OCR System...")
            
            # Get OCR system capabilities
            async with self.session.get(
                f"{self.config.ocr_system_endpoint}/capabilities"
            ) as response:
                if response.status == 200:
                    capabilities = await response.json()
                    self.logger.info(f"Core OCR System capabilities: {capabilities}")
                else:
                    self.logger.warning(f"Failed to get Core OCR System capabilities: {response.status}")
            
            # Configure OCR processing pipeline
            await self._configure_ocr_processing_pipeline()
            
            # Register OCR tools
            await self._register_ocr_tools_with_core_system()
            
            self.logger.info("Integration with Core OCR System completed")
            
        except Exception as e:
            self.logger.error(f"Integration with Core OCR System failed: {e}")
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
    
    async def _configure_ocr_caching(self):
        """Configure OCR caching with cache server."""
        try:
            self.logger.info("Configuring OCR caching...")
            
            # Define OCR cache configuration
            ocr_cache_config = {
                "enabled": True,
                "cache_ttl": 3600,  # 1 hour
                "max_cache_size": 1000,
                "cache_key_prefix": "easyocr_",
                "cache_layers": ["predictive", "semantic", "vector"],
                "fallback_enabled": True,
                "consolidation_enabled": True
            }
            
            # Store cache configuration
            cache_config_file = self.project_root / "config" / "ocr_cache_config.json"
            with open(cache_config_file, 'w') as f:
                json.dump(ocr_cache_config, f, indent=2)
            
            self.logger.info("OCR caching configured")
            
        except Exception as e:
            self.logger.error(f"Failed to configure OCR caching: {e}")
            raise
    
    async def _register_ocr_tools_with_cache(self):
        """Register OCR tools with cache server."""
        try:
            self.logger.info("Registering OCR tools with cache server...")
            
            # Define OCR tools
            ocr_tools = [
                {
                    "name": "easyocr_extract_text",
                    "description": "Extract text from image using EasyOCR",
                    "parameters": [
                        {
                            "name": "image_path",
                            "type": "string",
                            "required": true,
                            "description": "Path to the image file"
                        },
                        {
                            "name": "languages",
                            "type": "array",
                            "required": false,
                            "description": "List of languages to use for OCR"
                        },
                        {
                            "name": "confidence_threshold",
                            "type": "number",
                            "required": false,
                            "description": "Confidence threshold for text detection"
                        }
                    ]
                },
                {
                    "name": "easyocr_extract_batch",
                    "description": "Extract text from multiple images in batch",
                    "parameters": [
                        {
                            "name": "image_paths",
                            "type": "array",
                            "required": true,
                            "description": "List of image file paths"
                        },
                        {
                            "name": "batch_size",
                            "type": "number",
                            "required": false,
                            "description": "Batch size for processing"
                        }
                    ]
                },
                {
                    "name": "easyocr_validate_installation",
                    "description": "Validate EasyOCR installation and dependencies",
                    "parameters": []
                }
            ]
            
            # Register tools with cache server
            for tool in ocr_tools:
                async with self.session.post(
                    f"{self.config.cache_server_endpoint}/tools/register",
                    json=tool,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Registered OCR tool: {tool['name']}")
                    else:
                        self.logger.warning(f"Failed to register OCR tool {tool['name']}: {response.status}")
            
            self.logger.info("OCR tools registered with cache server")
            
        except Exception as e:
            self.logger.error(f"Failed to register OCR tools with cache server: {e}")
            raise
    
    async def _configure_ocr_routing(self):
        """Configure OCR routing with KiloCode."""
        try:
            self.logger.info("Configuring OCR routing...")
            
            # Create routing configuration
            routing_config = {
                "enabled": True,
                "routing_logic": "smart",
                "fallback_order": ["easyocr", "core_ocr", "cache_fallback"],
                "routing_rules": [
                    {
                        "pattern": "extract.*|ocr.*|text.*",
                        "service": "easyocr",
                        "priority": 1,
                        "enabled": True
                    },
                    {
                        "pattern": "batch.*|multiple.*",
                        "service": "easyocr_batch",
                        "priority": 2,
                        "enabled": True
                    },
                    {
                        "pattern": "validate.*|check.*|test.*",
                        "service": "easyocr_validate",
                        "priority": 3,
                        "enabled": True
                    }
                ]
            }
            
            # Store routing configuration
            routing_file = self.project_root / "config" / "ocr_routing.json"
            with open(routing_file, 'w') as f:
                json.dump(routing_config, f, indent=2)
            
            self.logger.info("OCR routing configured")
            
        except Exception as e:
            self.logger.error(f"Failed to configure OCR routing: {e}")
            raise
    
    async def _register_ocr_tools_with_kilocode(self):
        """Register OCR tools with KiloCode."""
        try:
            self.logger.info("Registering OCR tools with KiloCode...")
            
            # Define OCR tools
            ocr_tools = [
                {
                    "name": "easyocr_extract_text",
                    "description": "Extract text from image using EasyOCR",
                    "parameters": [
                        {
                            "name": "image_path",
                            "type": "string",
                            "required": true,
                            "description": "Path to the image file"
                        },
                        {
                            "name": "languages",
                            "type": "array",
                            "required": false,
                            "description": "List of languages to use for OCR"
                        },
                        {
                            "name": "confidence_threshold",
                            "type": "number",
                            "required": false,
                            "description": "Confidence threshold for text detection"
                        }
                    ]
                },
                {
                    "name": "easyocr_extract_batch",
                    "description": "Extract text from multiple images in batch",
                    "parameters": [
                        {
                            "name": "image_paths",
                            "type": "array",
                            "required": true,
                            "description": "List of image file paths"
                        },
                        {
                            "name": "batch_size",
                            "type": "number",
                            "required": false,
                            "description": "Batch size for processing"
                        }
                    ]
                },
                {
                    "name": "easyocr_validate_installation",
                    "description": "Validate EasyOCR installation and dependencies",
                    "parameters": []
                }
            ]
            
            # Register tools with KiloCode
            for tool in ocr_tools:
                async with self.session.post(
                    f"{self.config.kilocode_endpoint}/tools/register",
                    json=tool,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Registered OCR tool: {tool['name']}")
                    else:
                        self.logger.warning(f"Failed to register OCR tool {tool['name']}: {response.status}")
            
            self.logger.info("OCR tools registered with KiloCode")
            
        except Exception as e:
            self.logger.error(f"Failed to register OCR tools with KiloCode: {e}")
            raise
    
    async def _configure_ocr_processing_pipeline(self):
        """Configure OCR processing pipeline with core system."""
        try:
            self.logger.info("Configuring OCR processing pipeline...")
            
            # Create pipeline configuration
            pipeline_config = {
                "enabled": True,
                "pipeline_name": "easyocr_processing",
                "stages": [
                    {
                        "name": "preprocessing",
                        "enabled": True,
                        "max_image_size": 1024,
                        "use_grayscale": True,
                        "use_binarization": True
                    },
                    {
                        "name": "ocr_extraction",
                        "enabled": True,
                        "engine": "easyocr",
                        "languages": ["en"],
                        "confidence_threshold": 30
                    },
                    {
                        "name": "postprocessing",
                        "enabled": True,
                        "format_output": True,
                        "include_metadata": True
                    }
                ],
                "error_handling": {
                    "enabled": True,
                    "retry_attempts": 3,
                    "fallback_enabled": True
                }
            }
            
            # Store pipeline configuration
            pipeline_file = self.project_root / "config" / "ocr_pipeline_config.json"
            with open(pipeline_file, 'w') as f:
                json.dump(pipeline_config, f, indent=2)
            
            self.logger.info("OCR processing pipeline configured")
            
        except Exception as e:
            self.logger.error(f"Failed to configure OCR processing pipeline: {e}")
            raise
    
    async def _register_ocr_tools_with_core_system(self):
        """Register OCR tools with core system."""
        try:
            self.logger.info("Registering OCR tools with core system...")
            
            # Define OCR tools
            ocr_tools = [
                {
                    "name": "easyocr_extract_text",
                    "description": "Extract text from image using EasyOCR",
                    "parameters": [
                        {
                            "name": "image_path",
                            "type": "string",
                            "required": true,
                            "description": "Path to the image file"
                        },
                        {
                            "name": "languages",
                            "type": "array",
                            "required": false,
                            "description": "List of languages to use for OCR"
                        },
                        {
                            "name": "confidence_threshold",
                            "type": "number",
                            "required": false,
                            "description": "Confidence threshold for text detection"
                        }
                    ]
                },
                {
                    "name": "easyocr_extract_batch",
                    "description": "Extract text from multiple images in batch",
                    "parameters": [
                        {
                            "name": "image_paths",
                            "type": "array",
                            "required": true,
                            "description": "List of image file paths"
                        },
                        {
                            "name": "batch_size",
                            "type": "number",
                            "required": false,
                            "description": "Batch size for processing"
                        }
                    ]
                },
                {
                    "name": "easyocr_validate_installation",
                    "description": "Validate EasyOCR installation and dependencies",
                    "parameters": []
                }
            ]
            
            # Register tools with core system
            for tool in ocr_tools:
                async with self.session.post(
                    f"{self.config.ocr_system_endpoint}/tools/register",
                    json=tool,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Registered OCR tool: {tool['name']}")
                    else:
                        self.logger.warning(f"Failed to register OCR tool {tool['name']}: {response.status}")
            
            self.logger.info("OCR tools registered with core system")
            
        except Exception as e:
            self.logger.error(f"Failed to register OCR tools with core system: {e}")
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
                    
                    # Store OCR results in memory bank
                    for memory_item in memory_data.get("memories", []):
                        await self._store_ocr_result_in_memory_bank(memory_item)
                    
                    self.logger.info(f"Processed memory file: {file_path}")
                
                except Exception as e:
                    self.logger.error(f"Failed to process memory file {file_path}: {e}")
            
            self.logger.info("Memory bank sync completed")
            
        except Exception as e:
            self.logger.error(f"Failed to sync with memory bank: {e}")
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
    
    async def _store_ocr_result_in_memory_bank(self, item: Dict[str, Any]):
        """Store OCR result in memory bank."""
        try:
            # This would typically call the memory bank API
            async with self.session.post(
                f"{self.config.kilocode_endpoint}/memory/store",
                json={
                    "type": "ocr_result",
                    "data": item,
                    "timestamp": datetime.now().isoformat()
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    self.logger.debug(f"Stored OCR result in memory bank: {item.get('id', 'unknown')}")
                else:
                    self.logger.warning(f"Failed to store OCR result in memory bank: {response.status}")
        
        except Exception as e:
            self.logger.error(f"Failed to store OCR result in memory bank: {e}")
    
    async def run_integration(self):
        """Run the complete integration process."""
        try:
            self.logger.info("Starting EasyOCR MCP server integration...")
            
            # Initialize
            await self.initialize()
            
            # Run integrations
            if self.config.cache_server_enabled:
                await self.integrate_with_cache_server()
            
            if self.config.kilocode_enabled:
                await self.integrate_with_kilocode()
            
            if self.config.ocr_system_enabled:
                await self.integrate_with_ocr_system()
            
            if self.config.memory_bank_enabled:
                await self.integrate_with_memory_bank()
            
            self.logger.info("EasyOCR MCP server integration completed successfully!")
            
        except Exception as e:
            self.logger.error(f"EasyOCR MCP server integration failed: {e}")
            raise
        finally:
            await self.close()


async def main():
    """Main entry point for integration."""
    try:
        # Create integration configuration
        config = MCPIntegrationConfig(
            cache_server_enabled=True,
            cache_server_endpoint="http://localhost:8001",
            kilocode_enabled=True,
            kilocode_endpoint="http://localhost:8080",
            ocr_system_enabled=True,
            ocr_system_endpoint="http://localhost:9000",
            memory_bank_enabled=True,
            memory_bank_path="./memorybank"
        )
        
        # Initialize integrator
        integrator = MCPIntegrator(config)
        
        # Run integration
        await integrator.run_integration()
        
        print("\nEasyOCR MCP server integration completed successfully!")
        print("The EasyOCR MCP server is now integrated with all external services.")
        
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        print(f"Integration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())