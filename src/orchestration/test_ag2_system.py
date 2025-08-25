import asyncio
import logging
import os
import yaml
import argparse
from ag2_orchestrator import AG2Orchestrator
from autogen import LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ag2_system(skip_llm=False):
    """
    Tests the AG2 orchestrator with MCP servers and sample queries.
    """
    # 1. Load LLM Configuration (from environment variables)
    llm_config = None
    if skip_llm:
        logger.info("Test: Skipping LLM initialization as per --skip-llm flag.")
        llm_config = LLMConfig(
            model="dummy-model-for-testing",
            api_type="openai",
            api_key="dummy-key-for-testing",
            base_url=None
        )
    else:
        try:
            # Priority: OPENROUTER -> OPENAI -> AZURE
            api_key = os.environ.get("OPENROUTER_API_KEY")
            model = os.environ.get("AG2_MODEL", "openai/gpt-4o-mini") # Default to a common OpenRouter model
            base_url = "https://openrouter.ai/api/v1" # Default base URL for OpenRouter
            extra_headers = {
                "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost"),
                "X-Title": os.getenv("OPENROUTER_X_TITLE", "AG2 Orchestrator Test"),
            }

            if not api_key:
                api_key = os.environ.get("OPENAI_API_KEY")
                if api_key:
                    model = os.environ.get("OPENAI_MODEL", model) # Use OpenAI model if specified
                    base_url = os.environ.get("OPENAI_BASE_URL", base_url) # Use OpenAI base URL if specified
                    extra_headers = {} # No extra headers needed for standard OpenAI
                    logger.info(f"Test: Configuring LLM for OpenAI. Model: {model}")
                else:
                    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
                    if api_key:
                        api_type = "azure" # Ensure api_type is set for Azure
                        api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
                        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
                        deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
                        azure_model = os.environ.get("AZURE_OPENAI_MODEL")
                        if not all([api_version, endpoint, deployment_name]):
                            raise ValueError("Incomplete Azure OpenAI config for test.")
                        model = azure_model if azure_model else deployment_name
                        logger.info(f"Test: Configuring LLM for Azure OpenAI. Model: {model}")
                        base_url = None # Azure uses endpoint, not base_url in the same way
                        extra_headers = {}
                    else:
                        raise ValueError(
                            "No LLM API key found for testing. "
                            "Please set OPENROUTER_API_KEY, OPENAI_API_KEY, or AZURE_OPENAI_API_KEY."
                        )
            else:
                api_type = "openai" # OpenRouter uses OpenAI-compatible API type
                logger.info(f"Test: Configuring LLM for OpenRouter. Model: {model}, Base URL: {base_url}")
            
            # Determine api_type if not already set (e.g. for OpenAI)
            if 'api_type' not in locals():
                api_type = "openai"
            
            logger.info(f"Test: Initializing LLM with Type: {api_type}, Model: {model}")
            
            # Prepare LLMConfig arguments
            llm_config_args = {
                "model": model,
                "api_type": api_type,
                "api_key": api_key,
            }
            if base_url: # base_url is not used for Azure
                llm_config_args["base_url"] = base_url
            
            # For OpenAI (including OpenRouter), use default_headers parameter
            if api_type == "openai" and extra_headers:
                llm_config_args["default_headers"] = extra_headers

            llm_config = LLMConfig(**llm_config_args)

            if api_type == "azure":
                llm_config.api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
                llm_config.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
                llm_config.deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
        except ValueError as ve:
            logger.error(f"Test LLM Config Error: {ve}")
            print(f"ERROR: {ve}. Please set up your LLM environment variables for testing or use --skip-llm.")
            return
        except Exception as e:
            logger.error(f"Test: Failed to initialize LLMConfig: {e}")
            print(f"ERROR: Failed to initialize LLMConfig: {e}")
            return

    # 2. Initialize Orchestrator
    orchestrator = None
    try:
        logger.info("Test: Initializing AG2 Orchestrator...")
        orchestrator = AG2Orchestrator(llm_config=llm_config)
        logger.info("Test: AG2 Orchestrator initialized.")
    except Exception as e:
        logger.error(f"Test: Failed to initialize AG2 Orchestrator: {e}")
        print(f"ERROR: Failed to initialize AG2 Orchestrator: {e}")
        return

    # 3. Setup MCP Servers from Config
    config_path = os.path.join(os.path.dirname(__file__), "mcp_servers_config.yaml")
    mcp_servers_config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                mcp_servers_config = yaml.safe_load(f) or {}
            logger.info(f"Test: Loaded MCP server config from {config_path}")
        except Exception as e:
            logger.error(f"Test: Error reading MCP config {config_path}: {e}")
    else:
        logger.warning(f"Test: MCP server config file not found at {config_path}. MCP servers will not be set up from config.")

    active_mcp_servers = []
    if mcp_servers_config:
        servers = mcp_servers_config.get('mcpServers', {})
        for server_name, server_config in servers.items():
            if not isinstance(server_config, dict) or 'command' not in server_config or 'args' not in server_config:
                logger.warning(f"Test: Invalid config for server '{server_name}'. Skipping.")
                continue
            
            command = server_config['command']
            args = server_config['args']
            env_vars = server_config.get('env', {})
            description = server_config.get('description', f'MCP server: {server_name}')

            try:
                logger.info(f"Test: Setting up MCP server: {server_name} ({description})")
                
                # Set environment variables for this server
                for key, value in env_vars.items():
                    os.environ[key] = str(value)
                
                await orchestrator.setup_mcp_session(
                    server_name=server_name,
                    command=command,
                    args=args
                )
                await orchestrator.create_toolkit(server_name=server_name)
                active_mcp_servers.append(server_name)
                logger.info(f"Test: Successfully set up and created toolkit for MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Test: FAILED to setup MCP server '{server_name}': {e}. This server will be unavailable for testing.")
                print(f"ERROR: FAILED to setup MCP server '{server_name}': {e}")
    else:
        logger.warning("Test: No MCP servers configured or config file missing. Proceeding with agent initialization without MCP tools.")
        print("WARNING: No MCP servers configured or config file missing. Agent will have no external tools.")

    # 4. Initialize Agent
    try:
        logger.info("Test: Initializing AG2 Agent...")
        await orchestrator.initialize_agent(agent_name="test_agentic_orchestrator")
        logger.info("Test: AG2 Agent initialized.")
    except Exception as e:
        logger.error(f"Test: Failed to initialize AG2 Agent: {e}")
        print(f"ERROR: Failed to initialize AG2 Agent: {e}")
        await orchestrator.aclose()
        return

    # 5. Run Sample Queries
    logger.info("Test: Starting sample queries...")
    sample_queries = [
        "Hello, introduce yourself.",
        f"You have access to tools from the following MCP servers: {', '.join(active_mcp_servers) if active_mcp_servers else 'none'}. What can you do with them?",
        # Add a document to RAG (if rag_server is active)
        # This requires the 'rag_server' to be correctly configured and running.
        # The documentId should be unique for each test run if you want to avoid conflicts,
        # or use a fixed one and handle potential "already exists" errors if the server supports it.
        "If you have a tool to add a document to a RAG system, please add a short document with ID 'test_doc_123' and content 'This is a test document for the AG2 system.'",
        # Search for documents (if rag_server is active)
        "If you have a tool to search a RAG system, please search for documents related to 'AG2 system'.",
        # Retrieve the specific document (if rag_server is active)
        "If you have a tool to retrieve a specific document from a RAG system, please get the document with ID 'test_doc_123'.",
    ]

    for i, query in enumerate(sample_queries):
        logger.info(f"Test: Running query {i+1}/{len(sample_queries)}: '{query}'")
        print(f"\n--- Query {i+1} ---\nUser: {query}")
        try:
            response = await orchestrator.run_query(query, max_turns=3) # Reduced turns for faster testing
            logger.info(f"Test: Query {i+1} response received.")
            print(f"Agent: {response}")
        except Exception as e:
            logger.error(f"Test: Error running query {i+1}: {e}")
            print(f"ERROR: Agent failed to process query {i+1}: {e}")
        await asyncio.sleep(1) # Small delay between queries

    # 6. Cleanup
    logger.info("Test: Cleaning up AG2 Orchestrator...")
    try:
        await orchestrator.aclose()
        logger.info("Test: AG2 Orchestrator closed successfully.")
    except Exception as e:
        logger.error(f"Test: Error during cleanup: {e}")
        print(f"ERROR: During cleanup: {e}")

    logger.info("Test: AG2 System test finished.")
    print("\n--- Test Finished ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the AG2 Orchestrator and MCP servers.")
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip LLM initialization and API calls. Useful for testing MCP server setup in isolation."
    )
    args = parser.parse_args()

    print("Starting AG2 System Test...")
    print("Ensure your LLM API keys (OPENAI_API_KEY or AZURE_OPENAI_API_KEY) are set as environment variables, unless using --skip-llm.")
    print("Ensure MCP servers (like PGvector for RAG) are running if your config.yaml points to them.")
    print("This test will attempt to start MCP servers as subprocesses if configured in mcp_servers_config.yaml.")
    
    # Note: For this test to fully work, especially with MCP servers like PGvector,
    # those servers need to be accessible (e.g., PGvector running on http://localhost:8000).
    # The test script will try to start the MCP server processes as defined in the config.
    
    asyncio.run(test_ag2_system(skip_llm=args.skip_llm))
