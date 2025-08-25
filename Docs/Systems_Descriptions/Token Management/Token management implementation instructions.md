
# Token Management System Implementation Plan

### Objectives
- Track token usage accurately per user/session/request using pg_tiktoken.
- Enforce configurable rate limits and token quotas per API/user dynamically.
- Maintain lightweight logs for auditing and usage reporting.
- Implement priority-based token allocation for tasks.
- Integrate securely with your secret stores.
- Minimal dependencies, simple DB schema, easy integration with MCP and KiloCode.

***

## Step 1: Prepare PostgreSQL for Token Management

- **Enable pg_tiktoken extension** in your Postgres DB:

```sql
CREATE EXTENSION IF NOT EXISTS pg_tiktoken;
```

This allows token counting inside SQL queries with alignment to OpenAI-compatible tokenization.

***

## Step 2: Create Token Management Tables

A minimal set of tables to track usage, limits, and priorities:

```sql
-- Log tokens consumed per request with user and session context
CREATE TABLE token_usage (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    tokens_used INT NOT NULL,
    api_endpoint TEXT NOT NULL,
    priority_level TEXT CHECK (priority_level IN ('Low', 'Medium', 'High')) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Store per-user or per-API token quota and limits
CREATE TABLE token_limits (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    max_tokens_per_period INT NOT NULL, -- e.g., per day
    period_interval INTERVAL NOT NULL DEFAULT '1 day',
    tokens_used_in_period INT DEFAULT 0,
    period_start TIMESTAMP DEFAULT NOW()
);

-- Optional table for revoked tokens if applicable
CREATE TABLE token_revocations (
    token TEXT PRIMARY KEY,
    revoked_at TIMESTAMP DEFAULT NOW()
);
```

***

## Step 3: Token Counting Logic (MCP / Middleware Layer)

- In your MCP tools or KiloCode middleware wrapping API calls (e.g., calls to LLM or external APIs), count tokens for inputs and outputs **before** sending requests or after receiving responses.

- Use `pg_tiktoken` SQL function to count tokens precisely:

```sql
SELECT tiktoken_count('cl100k_base', $1) AS token_count;
```

- Example using Python `psycopg2` or MCP DB access layer:

```python
def count_tokens(text: str, db_conn) -> int:
    with db_conn.cursor() as cur:
        cur.execute("SELECT tiktoken_count('cl100k_base', %s)", (text,))
        return cur.fetchone()[0]
```

- Sum input and output tokens for each API interaction.

***

## Step 4: Enforce Rate Limits and Dynamic Allocation

- Before executing any token-consuming operation:

  1. **Check token usage in current period** from `token_limits`.
  
  2. **Calculate allowed tokens for current request** based on task priority:

     - High priority: up to 50% of remaining quota.
     - Medium priority: up to 30%.
     - Low priority: up to 20%.

- Reject or delay requests exceeding quotas.

- Update `token_limits.tokens_used_in_period` atomically after allowed operations or partial fulfillment.

- If using MCP middleware:

```python
def check_and_allocate_tokens(user_id, tokens_requested, priority, db_conn):
    # Fetch token limit and usage
    # Calculate allowed tokens per priority
    # Return True/False or allocated tokens count
    # Update usage after operation
    pass
```

***

## Step 5: Token Usage Logging

- After every API/inter-agent call, log token usage in `token_usage` table:

```sql
INSERT INTO token_usage (
    user_id, session_id, tokens_used, api_endpoint, priority_level
) VALUES ($1, $2, $3, $4, $5);
```

- Batch logging can be used if throughput is a concern (flush periodically).

***

## Step 6: Automated Periodic Quota Reset

- Implement a scheduled job (via OS cron or PostgreSQL's `pg_cron` extension) to **reset `token_limits` usage counters** at period boundaries:

```sql
UPDATE token_limits
SET tokens_used_in_period = 0,
    period_start = NOW()
WHERE period_start < NOW() - period_interval;
```

Run daily or as your period defines.

***

## Step 7: Security & Revocation Handling

- Use environment variables or HashiCorp Vault to securely store API tokens or keys.

- Check incoming tokens against `token_revocations` before processing requests (if applicable).

- Include token renewal and revocation logic in your token middleware.

***

## Step 8: Reporting & Monitoring

- Build simple SQL views or queries to summarize usage per user:

```sql
SELECT user_id,
       SUM(tokens_used) AS total_tokens,
       DATE_TRUNC('day', timestamp) AS day
FROM token_usage
GROUP BY user_id, day
ORDER BY day DESC;
```

- Implement CLI/endpoint in MCP or KiloCode for real-time token usage checks.

- Lightweight alerts can be added if usage approaches limits by querying `token_limits` periodically.

***

## Step 9: Integration with MCP and KiloCode

- **In MCP tools:**

  - Decorate token-consuming functions to count tokens, verify limits, update usage logs.
  
  - Clearly handle allocation failure to gracefully return informative errors or trigger retries.

- **In KiloCode Orchestration:**

  - Coordinate token budget per user session, route calls to MCP tools respecting token budgets.

- **Unit test all token counting, allocation, and logging code** to ensure correctness.

***

### Summary Table of Core Components & Roles

| Component              | Role                                    | Location/File                    |
|------------------------|-----------------------------------------|--------------------------------|
| Token Counting         | Count tokens via `pg_tiktoken`         | `src/mcp/token-manager.js`      |
| Rate Limit Checking    | Enforce quota and allocate tokens      | Middleware + token manager      |
| Token Usage Logging    | Log token usage per request             | `db/token-usage-logger.js`      |
| Token Quota Tracking   | Track usage per period, reset quotas    | Postgres + scheduled jobs       |
| Security (Token Vault) | Securely store API keys/tokens          | Environment / Vault integration |
| Monitoring & Reporting | Summarize usage, alert on spikes        | SQL Views + CLI or MCP endpoints|

***
