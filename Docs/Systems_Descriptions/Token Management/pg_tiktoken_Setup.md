# pg_tiktoken Extension Setup Documentation

## Overview

The pg_tiktoken extension enables fast, accurate token counting directly inside the PostgreSQL database, aligning tokenization precisely with OpenAI's models. This eliminates the need for external token counting middleware and provides better performance and accuracy.

## Implementation Details

### Files Created/Modified

1. **SQL Migration Script**: `src/database/migrations/001_enable_pg_tiktoken.sql`
   - Contains the SQL commands to enable the pg_tiktoken extension
   - Includes verification and testing queries
   - Creates a helper function to check extension availability

2. **PostgreSQL Database Class**: `simba/simba/database/postgres.py`
   - Modified `_ensure_schema()` method to call extension setup
   - Added `_ensure_pg_tiktoken_extension()` method for extension installation
   - Added `is_tiktoken_available()` method to verify extension functionality
   - Added `get_token_count()` method for token counting with fallback

3. **Test Script**: `tests/test_pg_tiktoken_integration.py`
   - Comprehensive test suite for the pg_tiktoken integration
   - Tests database connection, extension availability, and token counting

### Key Features

#### Automatic Extension Setup
- The pg_tiktoken extension is automatically enabled during database initialization
- Uses `CREATE EXTENSION IF NOT EXISTS` for idempotent installation
- Includes proper error handling with graceful fallback

#### Backward Compatibility
- System continues to work even if pg_tiktoken extension is not available
- Falls back to basic word-based token estimation (1.3 tokens per word)
- All operations remain functional regardless of extension status

#### Verification Methods
- `is_tiktoken_available()`: Checks if the extension and tiktoken_count function are working
- `get_token_count(text)`: Returns accurate token count using tiktoken or fallback estimation
- Built-in SQL verification functions in the migration script

## Usage Examples

### Checking Extension Availability
```python
from simba.simba.database.postgres import PostgresDB

db = PostgresDB()
if db.is_tiktoken_available():
    print("pg_tiktoken extension is available and working")
else:
    print("Using fallback token estimation")
```

### Counting Tokens
```python
# Get accurate token count (uses tiktoken if available, fallback otherwise)
text = "This is a sample text for token counting"
token_count = db.get_token_count(text)
print(f"Token count: {token_count}")
```

## Installation Requirements

### PostgreSQL Requirements
- PostgreSQL version 12 or later
- Superuser privileges or CREATEDB privilege for the database user
- pg_tiktoken extension must be installed in the PostgreSQL instance

### System Dependencies
- The extension requires the pg_tiktoken PostgreSQL extension to be available
- Ensure the extension is compiled and installed in your PostgreSQL installation

### Database Setup
The extension setup is automatically triggered when:
1. `PostgresDB` class is instantiated
2. `_ensure_schema()` method is called during initialization
3. The SQL migration script is executed

## Testing

Run the integration test to verify the setup:
```bash
python tests/test_pg_tiktoken_integration.py
```

The test will verify:
- Database connectivity
- Extension availability
- Token counting functionality
- Fallback behavior

## Troubleshooting

### Extension Not Available
If the pg_tiktoken extension is not available:
1. Check if the extension is installed in your PostgreSQL instance
2. Verify the database user has sufficient privileges
3. The system will automatically use fallback token estimation
4. Check logs for warnings about extension setup failures

### Permission Issues
If encountering permission errors:
1. Ensure the database user has CREATEDB privilege
2. Or have a superuser manually run the SQL migration script
3. The system logs will indicate any permission issues

### Performance Considerations
- tiktoken counting is significantly faster than external token counting
- Database-side counting reduces network overhead and processing time
- Fallback estimation is less accurate but provides basic functionality

## Integration with Token Management System

This implementation aligns with the Token Management System documentation by:
- Providing fast, accurate token counting directly in the database
- Eliminating external token counting middleware complexity
- Ensuring precise alignment with OpenAI's tokenization models
- Maintaining system reliability with graceful fallback mechanisms

## Future Enhancements

Potential improvements:
- Support for multiple OpenAI tokenization models (cl100k_base, p50k_base, etc.)
- Batch token counting for improved performance
- Token caching for frequently used text
- Integration with document metadata for token usage tracking