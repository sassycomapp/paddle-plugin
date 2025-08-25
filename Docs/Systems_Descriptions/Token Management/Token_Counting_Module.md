# Token Counting Module Documentation

## Overview

The Token Counting Module provides comprehensive token counting functionality with pg_tiktoken integration for accurate token counting aligned with OpenAI models. This module is designed to be performant, reliable, and easily integrable into existing systems.

## Features

### Core Functionality
- **Accurate Token Counting**: Uses pg_tiktoken for precise token counting when available
- **Fallback Estimation**: Provides word-based token estimation when pg_tiktoken is unavailable
- **Batch Processing**: Efficiently counts tokens for multiple texts in a single operation
- **Caching**: LRU cache for frequently accessed token counts to improve performance
- **Multiple Models**: Supports different tokenization models (cl100k_base, p50k_base, p50k_edit, r50k_base)

### Integration Features
- **Decorators**: Automatic token counting for function inputs and outputs
- **Middleware**: FastAPI middleware for automatic API request/response token counting
- **Database Integration**: Seamless integration with existing PostgreSQL database setup
- **Performance Metrics**: Comprehensive tracking of token counting performance

### Advanced Features
- **Context Window Calculations**: Analyze token usage against context window limits
- **Quota Management**: Integration with token quota and limit enforcement
- **Usage Logging**: Automatic logging of token usage to database
- **Error Handling**: Graceful degradation and comprehensive error handling

## Architecture

### Components

#### 1. TokenCounter
The main token counting class that provides all core functionality:

```python
from src.token_management import TokenCounter, TokenizationModel

counter = TokenCounter()
result = counter.count_tokens("Hello world", TokenizationModel.CL100K_BASE)
```

#### 2. Decorators
Automatic token counting decorators for functions:

```python
from src.token_management.decorators import token_counter_decorator

@token_counter_decorator(
    model=TokenizationModel.CL100K_BASE,
    count_inputs=True,
    count_outputs=True,
    log_usage=True
)
def process_text(text):
    return f"Processed: {text}"
```

#### 3. Middleware
FastAPI middleware for automatic API token counting:

```python
from src.token_management.middleware import TokenCountingMiddleware

app.add_middleware(TokenCountingMiddleware, 
                  model=TokenizationModel.CL100K_BASE)
```

### Data Flow

1. **Token Counting Request** → TokenCounter.count_tokens()
2. **pg_tiktoken Check** → Database extension availability
3. **Token Counting** → Use pg_tiktoken or fallback estimation
4. **Cache Check** → LRU cache for performance
5. **Result Return** → TokenCountResult with metadata
6. **Usage Logging** → Optional database logging

## Installation and Setup

### Prerequisites
- PostgreSQL database with pg_tiktoken extension enabled
- Python 3.8+
- Required dependencies (see requirements.txt)

### Database Setup
Ensure the pg_tiktoken extension is enabled:

```sql
-- Check if extension is available
SELECT is_tiktoken_available() as available;

-- Enable extension (requires superuser privileges)
CREATE EXTENSION IF NOT EXISTS pg_tiktoken;
```

### Python Package Installation
```bash
pip install -r requirements.txt
```

## Usage Examples

### Basic Token Counting

```python
from src.token_management import TokenCounter, TokenizationModel

# Initialize counter
counter = TokenCounter()

# Count tokens
result = counter.count_tokens("Hello, world!")
print(f"Token count: {result.token_count}")
print(f"Method: {result.method}")
print(f"Model: {result.model}")
```

### Batch Token Counting

```python
texts = ["Hello", "How are you", "Good morning"]
batch_result = counter.count_tokens_batch(texts)

print(f"Total tokens: {batch_result.total_tokens}")
print(f"Processing time: {batch_result.total_processing_time}")
print(f"Cache hits: {batch_result.cache_hits}")
```

### Context Window Analysis

```python
text = "This is a long text that needs to be analyzed..."
max_context = 4096  # GPT-3.5 context window

context_analysis = counter.get_token_count_for_context(
    text, max_context, TokenizationModel.CL100K_BASE
)

print(f"Context usage: {context_analysis['context_usage_percentage']:.1f}%")
print(f"Remaining tokens: {context_analysis['remaining_tokens']}")
print(f"Context fits: {context_analysis['context_fit']}")
```

### Using Decorators

```python
from src.token_management.decorators import token_counter_decorator

@token_counter_decorator(
    model=TokenizationModel.CL100K_BASE,
    count_inputs=True,
    count_outputs=True,
    log_usage=True
)
def chatbot_response(user_input):
    # Process user input and generate response
    return f"Response to: {user_input}"

# Function calls will be automatically token counted
response = chatbot_response("Hello, how are you?")
```

### API Middleware Integration

```python
from fastapi import FastAPI
from src.token_management.middleware import TokenCountingMiddleware

app = FastAPI()

# Add token counting middleware
app.add_middleware(TokenCountingMiddleware,
                  model=TokenizationModel.CL100K_BASE,
                  exclude_paths=['/health', '/metrics'])

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return {"response": "Hello world"}
```

### Quota Management

```python
from src.token_management.middleware import TokenQuotaMiddleware

# Add quota checking middleware
app.add_middleware(TokenQuotaMiddleware,
                  default_quota=10000,
                  quota_header="X-Token-Quota")
```

## Configuration

### TokenCounter Configuration

```python
counter = TokenCounter(
    db=custom_db,  # Optional: custom database instance
    cache_size=1000  # Optional: cache size (default: 1000)
)
```

### Middleware Configuration

```python
middleware = TokenCountingMiddleware(
    app,
    token_counter=custom_counter,
    model=TokenizationModel.CL100K_BASE,
    exclude_paths=['/health', '/metrics', '/docs'],
    include_methods=['GET', 'POST', 'PUT', 'DELETE']
)
```

### Decorator Configuration

```python
@token_counter_decorator(
    model=TokenizationModel.CL100K_BASE,
    count_inputs=True,
    count_outputs=True,
    log_usage=True,
    counter=custom_counter,
    user_id_extractor=lambda: "user123",
    session_id_extractor=lambda: "session456"
)
def my_function(text):
    return text.upper()
```

## Performance Optimization

### Caching Strategy
The module uses an LRU (Least Recently Used) cache to store token counts:
- Default cache size: 1000 entries
- Automatic cache eviction when limit is reached
- Cache key generation using SHA256 hashing

### Batch Processing
For processing multiple texts, use batch methods:
- More efficient than individual calls
- Reduced database overhead
- Better performance for bulk operations

### Database Optimization
- Connection pooling for database operations
- Efficient SQL queries with proper indexing
- Graceful fallback when database is unavailable

## Monitoring and Metrics

### Performance Metrics
The TokenCounter provides comprehensive performance metrics:

```python
metrics = counter.get_performance_metrics()

print(f"Total calls: {metrics['total_calls']}")
print(f"Cache hit rate: {metrics['cache_hit_rate']:.1f}%")
print(f"Average processing time: {metrics['average_processing_time']:.4f}s")
print(f"pg_tiktoken calls: {metrics['pg_tiktoken_calls']}")
print(f"Fallback calls: {metrics['fallback_calls']}")
```

### Usage Tracking
Token usage is automatically logged to the database:
- User ID and session ID tracking
- API endpoint and timestamp recording
- Priority level assignment
- Token count and processing time

### Database Schema
The module integrates with the existing token management tables:

```sql
-- Token usage tracking
CREATE TABLE token_usage (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    tokens_used INT NOT NULL,
    api_endpoint TEXT NOT NULL,
    priority_level TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Token limits and quotas
CREATE TABLE token_limits (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    max_tokens_per_period INT NOT NULL,
    period_interval INTERVAL NOT NULL,
    tokens_used_in_period INT NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Error Handling

### Graceful Degradation
The module handles various error scenarios gracefully:

1. **pg_tiktoken Unavailable**: Falls back to word-based estimation
2. **Database Connection Issues**: Continues operation with cached/fallback values
3. **Cache Failures**: Bypasses cache and continues processing
4. **Invalid Input**: Handles empty strings and special characters

### Error Logging
Comprehensive error logging for debugging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# All errors are logged with context
# Failed database connections, cache issues, etc.
```

### Exception Handling
Custom exceptions for different scenarios:

```python
try:
    result = counter.count_tokens(text)
except Exception as e:
    # Handle token counting errors
    logger.error(f"Token counting failed: {e}")
    # Fallback to manual estimation
    result = counter.estimate_tokens_fallback(text)
```

## Testing

### Running Tests
```bash
# Run all tests
python -m pytest tests/test_token_counter.py -v

# Run specific test class
python -m pytest tests/test_token_counter.py::TestTokenCounter -v

# Run with coverage
python -m pytest tests/test_token_counter.py --cov=src/token_management
```

### Test Coverage
The test suite covers:
- Basic token counting functionality
- Batch processing
- Caching mechanisms
- Decorator functionality
- Middleware integration
- Error handling scenarios
- Performance metrics
- Database integration

## Troubleshooting

### Common Issues

1. **pg_tiktoken Extension Not Available**
   - Check if extension is enabled in PostgreSQL
   - Verify database user has CREATE EXTENSION privileges
   - Use fallback estimation

2. **Performance Issues**
   - Monitor cache hit rates
   - Adjust cache size based on usage patterns
   - Use batch processing for multiple texts

3. **Database Connection Problems**
   - Verify database credentials
   - Check network connectivity
   - Ensure proper connection pooling

### Debug Mode
Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger('src.token_management').setLevel(logging.DEBUG)
```

### Performance Analysis
Use performance metrics to identify bottlenecks:

```python
metrics = counter.get_performance_metrics()
if metrics['cache_hit_rate'] < 50:
    # Consider increasing cache size
    counter.cache_size = 2000
```

## Integration with Existing Systems

### MCP Server Integration
The module can be integrated with MCP (Model Context Protocol) servers:

```python
from src.token_management import TokenCounter

class TokenCountingMCPServer:
    def __init__(self):
        self.counter = TokenCounter()
    
    async def count_tokens(self, text: str, model: str = "cl100k_base"):
        result = self.counter.count_tokens(text, TokenizationModel(model))
        return {
            "token_count": result.token_count,
            "model": result.model.value,
            "method": result.method
        }
```

### KiloCode Orchestration
Integration with KiloCode orchestration system:

```python
from src.token_management.decorators import track_token_usage

@track_token_usage(model=TokenizationModel.CL100K_BASE)
def orchestrate_task(task_data):
    # Task orchestration logic
    return {"status": "completed", "result": task_data}
```

### API Integration
Seamless integration with REST APIs:

```python
from fastapi import FastAPI, Depends
from src.token_management.middleware import TokenCountingMiddleware
from src.token_management import get_token_counter

app = FastAPI()
app.add_middleware(TokenCountingMiddleware)

@app.post("/process")
async def process_text(
    text: str,
    counter: TokenCounter = Depends(get_token_counter)
):
    result = counter.count_tokens(text)
    return {"token_count": result.token_count}
```

## Best Practices

### 1. Cache Management
- Monitor cache hit rates regularly
- Adjust cache size based on usage patterns
- Clear cache periodically for memory management

### 2. Database Optimization
- Use connection pooling for better performance
- Monitor database query performance
- Ensure proper indexing on token management tables

### 3. Error Handling
- Implement proper error handling in production
- Use fallback mechanisms gracefully
- Log errors for debugging and monitoring

### 4. Performance Monitoring
- Track performance metrics regularly
- Set up alerts for performance degradation
- Optimize based on usage patterns

### 5. Security
- Secure database credentials
- Implement proper access controls
- Sanitize input text before processing

## Future Enhancements

### Planned Features
1. **Advanced Caching Strategies**: Implement adaptive caching based on usage patterns
2. **Real-time Monitoring**: Add real-time performance monitoring and alerting
3. **Multi-model Support**: Enhanced support for additional tokenization models
4. **Distributed Caching**: Implement Redis-based distributed caching
5. **Analytics Dashboard**: Web-based dashboard for token usage analytics

### Performance Improvements
1. **Asynchronous Processing**: Full async support for better performance
2. **Parallel Processing**: Multi-threaded batch processing
3. **Database Optimization**: Advanced query optimization and indexing
4. **Memory Management**: Improved memory usage for large texts

### Integration Enhancements
1. **Framework Support**: Enhanced integration with popular frameworks
2. **Plugin System**: Plugin architecture for custom tokenization models
3. **Configuration Management**: Advanced configuration management
4. **Monitoring Integration**: Integration with monitoring and observability systems

## Conclusion

The Token Counting Module provides a robust, performant solution for token counting with pg_tiktoken integration. It offers comprehensive functionality for accurate token counting, efficient processing, and seamless integration with existing systems. The module is designed to be reliable, scalable, and easy to use, making it ideal for production environments.

For additional support and questions, please refer to the project documentation or contact the development team.