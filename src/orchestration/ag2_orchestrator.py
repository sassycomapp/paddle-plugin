import asyncio
import logging
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from autogen.mcp import create_toolkit
from autogen.agentchat import AssistantAgent
from autogen import LLMConfig
from datetime import timedelta
import subprocess
import io
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
import json
import time
import time

# Attempt to import yaml, handling potential ModuleNotFoundError
try:
    import yaml
except ModuleNotFoundError:
    print("Warning: PyYAML not found. MCP server configuration from YAML files will be disabled.")
    print("Please install PyYAML using: pip install --user PyYAML")
    yaml = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMConfigBuilder:
    """Handles LLM configuration setup with support for multiple providers."""
    
    @staticmethod
    def build_config() -> Dict[str, Any]:
        """Build LLM configuration from environment variables and Vault."""
        load_dotenv()
        
        # Import Vault client for API key management
        try:
            from src.vault_client import get_api_key
            vault_available = True
        except ImportError:
            vault_available = False
            logger.warning("Vault client not available, using environment variables only")
        
        # Priority order: OpenRouter -> OpenAI -> Azure
        config = LLMConfigBuilder._try_openrouter()
        if not config:
            config = LLMConfigBuilder._try_openai()
        if not config:
            config = LLMConfigBuilder._try_azure()
        
        if not config:
            raise ValueError(
                "No LLM API configuration found. Please set one of:\n"
                "- OPENROUTER_API_KEY\n"
                "- OPENAI_API_KEY\n"
                "- AZURE_OPENAI_API_KEY (plus other required Azure vars)"
            )
        
        return config
    
    @staticmethod
    def _try_openrouter() -> Optional[Dict[str, Any]]:
        """Try to configure OpenRouter."""
        # Try Vault first, then environment variable
        try:
            from src.vault_client import get_api_key
            api_key = get_api_key("openrouter")
            if not api_key:
                api_key = os.getenv("OPENROUTER_API_KEY")
        except ImportError:
            api_key = os.getenv("OPENROUTER_API_KEY")
            
        if not api_key:
            return None
            
        return {
            "model": os.getenv("AG2_MODEL", "openai/gpt-4o-mini"),
            "api_type": "openai",
            "api_key": api_key,
            "base_url": "https://openrouter.ai/api/v1",
            "default_headers": {
                "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost"),
                "X-Title": os.getenv("OPENROUTER_X_TITLE", "AG2 Orchestrator"),
            }
        }
    
    @staticmethod
    def _try_openai() -> Optional[Dict[str, Any]]:
        """Try to configure OpenAI."""
        # Try Vault first, then environment variable
        try:
            from src.vault_client import get_api_key
            api_key = get_api_key("openai")
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
        except ImportError:
            api_key = os.getenv("OPENAI_API_KEY")
            
        if not api_key:
            return None
            
        return {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "api_type": "openai",
            "api_key": api_key,
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        }
    
    @staticmethod
    def _try_azure() -> Optional[Dict[str, Any]]:
        """Try to configure Azure OpenAI."""
        # Try Vault first, then environment variable
        try:
            from src.vault_client import get_api_key
            api_key = get_api_key("azure-openai")
            if not api_key:
                api_key = os.getenv("AZURE_OPENAI_API_KEY")
        except ImportError:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            
        if not api_key:
            return None
            
        required_vars = ["AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT_NAME"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(
                f"Azure OpenAI configuration incomplete. Missing: {', '.join(missing_vars)}"
            )
        
        return {
            "model": os.getenv("AZURE_OPENAI_MODEL") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            "api_type": "azure",
            "api_key": api_key,
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        }

# Cache routing configuration
CACHE_ROUTING_CONFIG = {
    "enabled": True,
    "fallback_order": ["predictive", "semantic", "vector", "global"],
    "timeout": 30,
    "max_retries": 3,
    "cache_hit_logging": True,
    "cache_miss_logging": True,
    "cache_layer_selection": {
        "predictive": ["predict", "forecast", "anticipate", "expect"],
        "semantic": ["query", "search", "analyze", "understand"],
        "vector": ["embedding", "similarity", "context", "related"],
        "global": ["knowledge", "fact", "information", "reference"],
        "vector_diary": ["conversation", "chat", "dialog", "context"]
    }
}

class CacheOrchestrator:
    """Handles cache routing and fallback logic for the AG2 orchestrator."""
    
    def __init__(self, cache_server_name: str = "cache-mcp-server"):
        self.cache_server_name = cache_server_name
        self.cache_enabled = CACHE_ROUTING_CONFIG["enabled"]
        self.fallback_order = CACHE_ROUTING_CONFIG["fallback_order"]
        self.timeout = CACHE_ROUTING_CONFIG["timeout"]
        self.max_retries = CACHE_ROUTING_CONFIG["max_retries"]
        self.hit_count = 0
        self.miss_count = 0
        self.total_requests = 0
        self.sessions: Dict[str, Any] = {}
        
    def determine_cache_layer(self, query: str, operation: str = "get") -> str:
        """
        Determine the appropriate cache layer based on query characteristics.
        
        Args:
            query: The query or key to determine cache layer for
            operation: Type of operation (get, set, delete, search)
            
        Returns:
            Cache layer name
        """
        if not self.cache_enabled:
            return "semantic"  # Default fallback
            
        query_lower = query.lower()
        
        # Check for specific patterns in the query
        for layer, patterns in CACHE_ROUTING_CONFIG["cache_layer_selection"].items():
            if any(pattern in query_lower for pattern in patterns):
                return layer
                
        # Default fallback based on operation type
        if operation in ["get", "search"]:
            return "semantic"
        elif operation in ["set", "delete"]:
            return "predictive"
        else:
            return self.fallback_order[0] if self.fallback_order else "semantic"
    
    async def check_cache_first(self, query: str, operation: str = "get") -> Dict[str, Any]:
        """
        Check cache first before proceeding with other operations.
        
        Args:
            query: The query to check cache for
            operation: Type of operation
            
        Returns:
            Dictionary with cache result and fallback information
        """
        if not self.cache_enabled:
            return {"cache_hit": False, "fallback_needed": True, "data": None}
            
        start_time = time.time()
        cache_layer = self.determine_cache_layer(query, operation)
        
        try:
            # Try to get from cache
            cache_result = await self._execute_cache_operation(
                operation, query, cache_layer, start_time
            )
            
            if cache_result.get("success") and cache_result.get("data"):
                self.hit_count += 1
                if CACHE_ROUTING_CONFIG["cache_hit_logging"]:
                    logger.info(f"Cache hit in {cache_layer} for query: {query[:50]}...")
                return {
                    "cache_hit": True,
                    "cache_layer": cache_layer,
                    "data": cache_result["data"],
                    "execution_time_ms": cache_result.get("execution_time_ms", 0),
                    "fallback_needed": False
                }
            else:
                self.miss_count += 1
                if CACHE_ROUTING_CONFIG["cache_miss_logging"]:
                    logger.info(f"Cache miss in {cache_layer} for query: {query[:50]}...")
                return {
                    "cache_hit": False,
                    "cache_layer": cache_layer,
                    "data": None,
                    "execution_time_ms": cache_result.get("execution_time_ms", 0),
                    "fallback_needed": True
                }
                
        except Exception as e:
            self.miss_count += 1
            logger.warning(f"Cache check failed for query '{query[:50]}...': {e}")
            return {
                "cache_hit": False,
                "cache_layer": cache_layer,
                "data": None,
                "execution_time_ms": 0,
                "fallback_needed": True,
                "error": str(e)
            }
    
    async def _execute_cache_operation(self, operation: str, key: str,
                                     layer: str, start_time: float) -> Dict[str, Any]:
        """
        Execute a cache operation with retry logic.
        
        Args:
            operation: Type of operation (get, set, delete)
            key: Cache key
            layer: Cache layer
            start_time: Start time for execution timing
            
        Returns:
            Dictionary with operation result
        """
        # Sessions will be provided by the AG2Orchestrator
        if not hasattr(self, 'sessions') or self.cache_server_name not in self.sessions:
            raise ValueError(f"Cache server '{self.cache_server_name}' not available")
            
        session = self.sessions[self.cache_server_name]
        
        # Prepare the tool call based on operation
        if operation == "get":
            tool_name = "cache_get"
            params = {"key": key, "layer": layer}
        elif operation == "set":
            tool_name = "cache_set"
            params = {"key": key, "value": key, "layer": layer}  # Simplified for now
        elif operation == "delete":
            tool_name = "cache_delete"
            params = {"key": key, "layer": layer}
        else:
            raise ValueError(f"Unsupported cache operation: {operation}")
        
        # Execute with retry logic
        for attempt in range(self.max_retries):
            try:
                # This is a simplified implementation - in practice, you'd use the MCP client
                # to call the appropriate tool
                result = await self._call_cache_tool(session, tool_name, params)
                execution_time = (time.time() - start_time) * 1000
                
                return {
                    "success": result.get("success", False),
                    "data": result.get("data"),
                    "execution_time_ms": execution_time,
                    "message": result.get("message", "")
                }
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)  # Wait before retry
                
        return {"success": False, "data": None, "execution_time_ms": 0}
    
    async def _call_cache_tool(self, session, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a cache tool through the MCP session.
        
        Args:
            session: MCP session
            tool_name: Name of the tool to call
            params: Tool parameters
            
        Returns:
            Tool result
        """
        # This is a placeholder implementation
        # In a real implementation, you would use the MCP client to call the tool
        logger.info(f"Calling cache tool '{tool_name}' with params: {params}")
        
        # Simulate tool call
        if tool_name == "cache_get":
            return {"success": True, "data": f"cached_value_for_{params['key']}"}
        elif tool_name == "cache_set":
            return {"success": True, "message": "Value cached"}
        elif tool_name == "cache_delete":
            return {"success": True, "message": "Value deleted"}
        else:
            return {"success": False, "message": f"Unknown tool: {tool_name}"}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total if total > 0 else 0
        
        return {
            "cache_enabled": self.cache_enabled,
            "total_requests": total,
            "cache_hits": self.hit_count,
            "cache_misses": self.miss_count,
            "hit_rate": hit_rate,
            "fallback_order": self.fallback_order,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }

class AG2Orchestrator:
    """Main orchestrator for AG2 with MCP integration."""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.agent = None
        self.sessions: Dict[str, ClientSession] = {}
        self.toolkits: Dict[str, Any] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.cache_orchestrator = CacheOrchestrator()
        # Provide sessions to cache orchestrator
        # Add sessions as a property to the cache orchestrator
        self.cache_orchestrator.sessions = self.sessions

    async def setup_mcp_session(self, server_name: str, command: str, args: list) -> ClientSession:
        """Set up an MCP session for a given server."""
        server_params = StdioServerParameters(command=command, args=args)
        
        try:
            logger.info(f"Starting MCP session: {server_name}")
            logger.debug(f"Command: {' '.join([command] + args)}")
            
            async with stdio_client(server_params) as (read_stream, write_stream):
                session = ClientSession(read_stream, write_stream, read_timeout_seconds=timedelta(seconds=30))
                await session.initialize()
                
                self.sessions[server_name] = session
                logger.info(f"MCP session started: {server_name}")
                return session
                
        except Exception as e:
            logger.error(f"Failed to start MCP session {server_name}: {e}")
            logger.debug(f"Traceback: {e.__traceback__}")
            raise

    async def create_toolkit(self, server_name: str) -> Any:
        """Create AG2 toolkit from MCP session."""
        if server_name not in self.sessions:
            raise ValueError(f"MCP session not found: {server_name}")
        
        try:
            toolkit = await create_toolkit(session=self.sessions[server_name])
            self.toolkits[server_name] = toolkit
            logger.info(f"Toolkit created: {server_name}")
            return toolkit
        except Exception as e:
            logger.error(f"Failed to create toolkit {server_name}: {e}")
            raise

    async def initialize_agent(self, agent_name: str = "agentic_orchestrator") -> AssistantAgent:
        """Initialize the AG2 agent with all available toolkits."""
        self.agent = AssistantAgent(name=agent_name, llm_config=self.llm_config)
        
        for server_name, toolkit in self.toolkits.items():
            try:
                toolkit.register_for_llm(self.agent)
                logger.info(f"Registered toolkit: {server_name}")
            except Exception as e:
                logger.error(f"Failed to register toolkit {server_name}: {e}")
        
        logger.info(f"Agent initialized: {agent_name}")
        return self.agent

    async def run_query(self, user_query: str, max_turns: int = 5) -> str:
        """Run a user query through the AG2 agent."""
        if not self.agent:
            raise ValueError("Agent not initialized")
        
        logger.info(f"Processing query: {user_query[:100]}...")
        
        try:
            all_tools = [tool for toolkit in self.toolkits.values() for tool in toolkit.tools]
            response = await self.agent.a_run(
                message=user_query,
                tools=all_tools,
                max_turns=max_turns,
                user_input=False
            )
            
            result = response.text if hasattr(response, 'text') else str(response)
            logger.info("Query processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise

    async def setup_from_config(self, config_path: str = "mcp_servers_config.yaml") -> None:
        """Set up MCP servers from YAML configuration."""
        if yaml is None:
            logger.warning("PyYAML not found. Skipping MCP server configuration from YAML.")
            return
            
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            servers = config.get('mcpServers', {})
            
            for server_name, server_config in servers.items():
                command = server_config['command']
                args = server_config.get('args', [])
                env_vars = server_config.get('env', {})
                
                # Set environment variables for the server
                for key, value in env_vars.items():
                    os.environ[key] = str(value)
                
                await self.setup_mcp_session(server_name, command, args)
                await self.create_toolkit(server_name)
                
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise

    async def aclose(self) -> None:
        """Clean up all resources."""
        # Close MCP sessions
        for server_name, session in list(self.sessions.items()):
            try:
                if hasattr(session, 'aclose'):
                    await session.aclose()
                elif hasattr(session, 'close'):
                    await session.close()
                logger.info(f"Closed MCP session: {server_name}")
            except Exception as e:
                logger.error(f"Error closing session {server_name}: {e}")
        
        # Terminate processes
        for server_name, process in list(self.processes.items()):
            try:
                if process and process.poll() is None:
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        await asyncio.wait_for(process.wait(), timeout=5.0) # Ensure process.wait() is awaited
                    logger.info(f"Terminated process: {server_name}")
            except Exception as e:
                logger.error(f"Error terminating process {server_name}: {e}")
        
        self.sessions.clear()
        self.toolkits.clear()
        self.processes.clear()

async def main():
    """Main function for testing the orchestrator."""
    try:
        # Build LLM configuration
        llm_config_dict = LLMConfigBuilder.build_config()
        llm_config = LLMConfig(**llm_config_dict)
        
        # Initialize orchestrator
        orchestrator = AG2Orchestrator(llm_config)
        
        # Set up MCP servers
        await orchestrator.setup_from_config()
        
        # Initialize agent
        await orchestrator.initialize_agent()
        
        # Test query
        test_query = "What can you help me with today?"
        response = await orchestrator.run_query(test_query)
        
        print(f"Query: {test_query}")
        print(f"Response: {response}")
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        raise
    finally:
        if 'orchestrator' in locals():
            await orchestrator.aclose()

if __name__ == "__main__":
    asyncio.run(main())
