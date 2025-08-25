# MCP and KiloCode Integration for Token Management

## Overview

This document describes the comprehensive integration between the Token Management System, MCP (Model Context Protocol) servers, and KiloCode orchestration system. The integration provides a unified token management solution that coordinates token budgets per user session, routes calls to MCP tools respecting token budgets, and provides initialization hooks during system startup.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Token Management System                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Token Counter   │  │ Token Budget    │  │ Token Tracking  │  │
│  │ (pg_tiktoken)   │  │ Manager         │  │ & Analytics     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Integration Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ MCP Integration │  │ KiloCode        │  │ External APIs   │  │
│  │ Adapter         │  │ Integration     │  │ Integration     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Systems                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ MCP Servers     │  │ KiloCode        │  │ Memory Systems  │  │
│  │ (Memory, Tools) │  │ Orchestrator    │  │ & RAG           │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Integration Points

1. **MCP Server Integration**: Decorates MCP tools with token counting and budget management
2. **KiloCode Orchestration**: Coordinates token budgets across multiple tasks and sessions
3. **Memory System Integration**: Tracks token usage for memory operations
4. **External API Integration**: Monitors and manages token usage for external API calls

## Core Integration Components

### 1. MCP Token Integration (`src/mcp_token_integration.py`)

#### Key Features
- **Token Counting Decorator**: Automatically counts tokens for MCP tool calls
- **Budget Management**: Enforces token budgets per user session
- **Quota Enforcement**: Prevents exceeding token limits
- **Error Handling**: Graceful handling of token quota exceeded scenarios
- **Logging**: Comprehensive logging of token usage

#### Core Functions

```python
@mcp_token_decorator()
async def store_memory_with_tokens(content: str, ctx: Context, **kwargs) -> Dict:
    """Store memory with automatic token counting and budget management."""
    # Implementation details...

async def setup_mcp_token_hooks(server: FastMCP) -> None:
    """Setup token management hooks for MCP server initialization."""
    # Implementation details...
```

#### Usage Example

```python
from src.mcp_token_integration import mcp_token_decorator, setup_mcp_token_hooks

# Apply token counting to MCP tools
@mcp_token_decorator()
async def retrieve_memory_with_tokens(query: str, ctx: Context, n_results: int = 5) -> Dict:
    """Retrieve memories with automatic token counting."""
    storage = ctx.request_context.lifespan_context.storage
    results = await storage.search(query=query, n_results=n_results)
    return {"memories": results}

# Setup hooks during server initialization
setup_mcp_token_hooks(mcp_server)
```

### 2. KiloCode Token Integration (`src/kilocode_token_integration.py`)

#### Key Features
- **Session-based Budgeting**: Manages token budgets per user session
- **Task Coordination**: Coordinates token usage across multiple tasks
- **Priority Management**: Handles token allocation based on task priority
- **Real-time Monitoring**: Provides real-time token usage tracking
- **Dynamic Adjustment**: Adjusts token budgets based on usage patterns

#### Core Functions

```python
async def kilocode_token_budget(session_id: str, task_id: str, required_tokens: int) -> bool:
    """Check if sufficient tokens are available for a task."""
    # Implementation details...

async def route_with_token_budget(session_id: str, task_func: Callable, *args, **kwargs) -> Any:
    """Execute a task with token budget management."""
    # Implementation details...

async def setup_token_hooks(orchestrator: KiloCodeOrchestrator) -> None:
    """Setup token management hooks for KiloCode initialization."""
    # Implementation details...
```

#### Usage Example

```python
from src.kilocode_token_integration import kilocode_token_budget, route_with_token_budget

# Check token budget before executing a task
if await kilocode_token_budget(session_id, task_id, required_tokens=1000):
    result = await route_with_token_budget(session_id, complex_task, arg1, arg2)
else:
    raise TokenQuotaExceededError("Insufficient tokens for task")
```

### 3. Memory System Integration (`src/memory_token_integration.py`)

#### Key Features
- **Memory Operation Tracking**: Tracks tokens used for memory operations
- **Semantic Search Optimization**: Optimizes token usage for memory retrieval
- **Memory Consolidation**: Manages token usage during memory consolidation
- **Storage Integration**: Integrates with various storage backends
- **Performance Monitoring**: Monitors token usage patterns for memory operations

#### Core Functions

```python
async def integrate_with_memory(storage_backend: MemoryStorage) -> TokenAwareMemoryStorage:
    """Integrate token management with memory storage backend."""
    # Implementation details...

async def track_memory_operation(operation: str, content: str, tokens_used: int) -> None:
    """Track token usage for memory operations."""
    # Implementation details...
```

#### Usage Example

```python
from src.memory_token_integration import integrate_with_memory, track_memory_operation

# Integrate token management with memory storage
token_aware_storage = await integrate_with_memory(memory_storage)

# Track memory operations
await track_memory_operation("store", "Memory content", tokens_used=150)
```

### 4. External API Integration (`src/external_api_token_integration.py`)

#### Key Features
- **API Token Management**: Manages tokens for external API calls
- **Rate Limiting**: Enforces rate limits for external API usage
- **Cost Tracking**: Tracks costs associated with external API calls
- **Fallback Strategies**: Provides fallback mechanisms when tokens are exhausted
- **Monitoring**: Monitors external API token usage and costs

#### Core Functions

```python
async def integrate_with_external_apis(api_configs: List[APIConfig]) -> ExternalAPIClient:
    """Integrate token management with external API clients."""
    # Implementation details...

async def manage_api_tokens(api_name: str, required_tokens: int) -> bool:
    """Check and manage tokens for external API calls."""
    # Implementation details...
```

#### Usage Example

```python
from src.external_api_token_integration import integrate_with_external_apis, manage_api_tokens

# Integrate with external APIs
api_client = await integrate_with_external_apis(openai_config, anthropic_config)

# Check tokens before API call
if await manage_api_tokens("openai", required_tokens=1000):
    response = await api_client.chat.completions.create(model="gpt-4", messages=messages)
```

## Database Schema

### Integration Tables

The integration system extends the existing token management schema with additional tables:

```sql
-- Session-based token tracking
CREATE TABLE IF NOT EXISTS session_token_budgets (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    daily_limit INTEGER NOT NULL DEFAULT 10000,
    monthly_limit INTEGER NOT NULL DEFAULT 300000,
    hard_limit INTEGER NOT NULL DEFAULT 1000000,
    tokens_used_today INTEGER NOT NULL DEFAULT 0,
    tokens_used_month INTEGER NOT NULL DEFAULT 0,
    last_reset TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Task-level token allocation
CREATE TABLE IF NOT EXISTS task_token_allocations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    allocated_tokens INTEGER NOT NULL,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session_token_budgets(session_id)
);

-- External API token tracking
CREATE TABLE IF NOT EXISTS external_api_tokens (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(100) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0.0,
    last_used TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rate_limit_remaining INTEGER,
    rate_limit_reset TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session_token_budgets(session_id)
);

-- Integration logs
CREATE TABLE IF NOT EXISTS integration_logs (
    id SERIAL PRIMARY KEY,
    integration_type VARCHAR(50) NOT NULL,
    component_name VARCHAR(100) NOT NULL,
    session_id VARCHAR(255),
    task_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Integration Configuration

```json
{
  "mcp": {
    "host": "localhost",
    "port": 8000,
    "timeout": 30,
    "max_retries": 3,
    "token_budget_per_request": 4000
  },
  "kilocode": {
    "host": "localhost",
    "port": 8080,
    "timeout": 60,
    "max_concurrent_tasks": 10,
    "session_timeout": 3600
  },
  "external_apis": {
    "timeout": 30,
    "max_retries": 3,
    "rate_limit": 60,
    "fallback_enabled": true
  },
  "token_limits": {
    "daily_limit": 10000,
    "monthly_limit": 300000,
    "hard_limit": 1000000,
    "warning_threshold": 0.8,
    "critical_threshold": 0.95
  },
  "performance": {
    "enable_caching": true,
    "cache_size": 1000,
    "batch_size": 10,
    "async_operations": true
  }
}
```

### Environment Variables

```bash
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=token_management
DATABASE_USER=postgres
DATABASE_PASSWORD=

# MCP Configuration
MCP_HOST=localhost
MCP_PORT=8000
MCP_TIMEOUT=30

# KiloCode Configuration
KILOCODE_HOST=localhost
KILOCODE_PORT=8080
KILOCODE_TIMEOUT=60

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/token_integration.log
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis (for caching)
- Existing token management system

### Installation Steps

1. **Run the Setup Script**
   ```bash
   python scripts/setup_token_integration.py
   ```

2. **Database Migration**
   ```bash
   alembic upgrade head
   ```

3. **Start Services**
   ```bash
   # Start MCP Memory Service
   python -m mcp_memory_service.server
   
   # Start KiloCode Orchestrator
   python -m kilocode.orchestrator
   
   # Start Token Management API
   uvicorn token_management.main:app --host 0.0.0.0 --port 8000
   ```

4. **Setup Systemd Services**
   ```bash
   sudo cp systemd/*.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable token-integration mcp-memory-service kilocode-orchestrator
   sudo systemctl start token-integration mcp-memory-service kilocode-orchestrator
   ```

## Usage Examples

### Basic MCP Integration

```python
from src.mcp_token_integration import mcp_token_decorator, setup_mcp_token_hooks
from mcp.server.fastmcp import FastMCP, Context

# Create MCP server
mcp = FastMCP(name="Token-Aware MCP Server")

# Apply token counting to tools
@mcp.tool()
@mcp_token_decorator()
async def store_memory_with_tokens(
    content: str,
    ctx: Context,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Store memory with automatic token counting."""
    storage = ctx.request_context.lifespan_context.storage
    memory = Memory(content=content, tags=tags or [])
    success, message = await storage.store(memory)
    return {"success": success, "message": message}

# Setup token hooks
setup_mcp_token_hooks(mcp)
```

### KiloCode Task Orchestration

```python
from src.kilocode_token_integration import kilocode_token_budget, route_with_token_budget
from kilocode import KiloCodeOrchestrator

# Create orchestrator
orchestrator = KiloCodeOrchestrator()

# Setup token hooks
await setup_token_hooks(orchestrator)

# Define a token-aware task
@orchestrator.task()
async def process_user_request(session_id: str, user_input: str) -> str:
    """Process user request with token budget management."""
    # Check token budget
    required_tokens = estimate_tokens(user_input)
    if not await kilocode_token_budget(session_id, "process_request", required_tokens):
        raise TokenQuotaExceededError("Insufficient tokens for processing")
    
    # Execute with token tracking
    result = await route_with_token_budget(
        session_id,
        process_request,
        user_input
    )
    
    return result
```

### Memory System Integration

```python
from src.memory_token_integration import integrate_with_memory, track_memory_operation

# Integrate with existing memory storage
memory_storage = SqliteVecStorage("memory.db")
token_aware_storage = await integrate_with_memory(memory_storage)

# Use token-aware storage
async def store_memory_with_tracking(content: str, tags: List[str]):
    """Store memory with token tracking."""
    tokens_used = await token_counter.count_tokens(content)
    
    memory = Memory(content=content, tags=tags)
    success, message = await token_aware_storage.store(memory)
    
    await track_memory_operation("store", content, tokens_used)
    return success, message
```

## Monitoring and Analytics

### Token Usage Metrics

The integration system provides comprehensive token usage metrics:

1. **Session-level Metrics**
   - Tokens used per session
   - Budget utilization rates
   - Remaining tokens by time period

2. **Task-level Metrics**
   - Token allocation per task
   - Task completion rates
   - Token efficiency metrics

3. **System-level Metrics**
   - Total token usage across all sessions
   - API cost tracking
   - Performance metrics

### Monitoring Dashboard

```python
from src.token_dashboard import TokenDashboard

# Create dashboard
dashboard = TokenDashboard()

# Get session metrics
session_metrics = dashboard.get_session_metrics(session_id)

# Get system overview
system_overview = dashboard.get_system_overview()

# Generate reports
daily_report = dashboard.generate_daily_report()
```

## Error Handling

### Common Error Types

```python
class TokenQuotaExceededError(Exception):
    """Raised when token quota is exceeded."""
    pass

class TokenBudgetExhaustedError(Exception):
    """Raised when token budget is exhausted."""
    pass

class IntegrationError(Exception):
    """Raised for integration-related errors."""
    pass
```

### Error Handling Strategies

1. **Graceful Degradation**: When tokens are exhausted, provide fallback responses
2. **User Notifications**: Inform users when approaching token limits
3. **Automatic Recovery**: Implement automatic token budget refresh when possible
4. **Logging**: Comprehensive error logging for debugging

## Performance Optimization

### Caching Strategies

1. **Token Counting Cache**: Cache token counts for frequently used content
2. **Budget Cache**: Cache budget checks for improved performance
3. **Session Cache**: Cache session information for quick access

### Batch Processing

```python
# Batch token counting
tokens_used = await token_counter.count_tokens_batch([
    "Content 1",
    "Content 2", 
    "Content 3"
])

# Batch budget checks
budget_checks = await asyncio.gather(*[
    kilocode_token_budget(session_id, task_id, tokens)
    for task_id, tokens in task_tokens.items()
])
```

## Security Considerations

### Token Security

1. **Encryption**: Encrypt sensitive token data at rest
2. **Access Control**: Implement proper access controls for token management
3. **Audit Logging**: Maintain comprehensive audit logs for token usage
4. **Rate Limiting**: Implement rate limiting to prevent abuse

### Data Privacy

1. **User Data Protection**: Ensure user data is protected during token processing
2. **Anonymization**: Anonymize token usage data where appropriate
3. **Compliance**: Ensure compliance with relevant data protection regulations

## Troubleshooting

### Common Issues

1. **Token Counting Inaccuracies**
   - Verify pg_tiktoken installation
   - Check for model-specific token counting issues
   - Validate fallback estimation logic

2. **Budget Management Issues**
   - Check session initialization
   - Verify database connections
   - Review budget calculation logic

3. **Integration Problems**
   - Check service connectivity
   - Verify configuration files
   - Review logs for error details

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("token_integration").setLevel(logging.DEBUG)

# Check integration status
from src.integration_health import check_integration_health
status = check_integration_health()
print(f"Integration status: {status}")
```

## Future Enhancements

### Planned Features

1. **Advanced Token Analytics**: More sophisticated token usage analytics
2. **Dynamic Budget Adjustment**: AI-driven token budget optimization
3. **Multi-tenant Support**: Enhanced support for multi-tenant environments
4. **Real-time Monitoring**: Real-time token usage monitoring and alerts
5. **Cost Optimization**: Advanced cost optimization for token usage

### Integration Roadmap

1. **Phase 1**: Core MCP and KiloCode integration (Completed)
2. **Phase 2**: Enhanced memory system integration (In Progress)
3. **Phase 3**: External API integration expansion (Planned)
4. **Phase 4**: Advanced analytics and monitoring (Planned)
5. **Phase 5**: Multi-tenant and enterprise features (Future)

## Conclusion

The MCP and KiloCode integration for token management provides a comprehensive solution for managing token usage across multiple systems. The integration ensures efficient token budget management, provides real-time monitoring, and maintains system reliability through robust error handling and performance optimization.

This integration enables seamless operation of AI applications while maintaining strict token budget controls, making it ideal for production environments where cost management and resource optimization are critical.