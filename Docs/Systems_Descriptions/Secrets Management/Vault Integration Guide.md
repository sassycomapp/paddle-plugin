# HashiCorp Vault Integration Guide

## Overview

This guide provides comprehensive documentation for the HashiCorp Vault integration in the paddle-plugin system. The integration replaces hardcoded credentials with secure secret management through Vault.

## Architecture

### Components

1. **Vault Client** (`src/vault_client.py`)
   - Main interface for Vault operations
   - Handles authentication and secret retrieval
   - Provides fallback mechanisms when Vault is unavailable

2. **Vault Configuration**
   - `vault-config.hcl`: Vault server configuration
   - `vault-policies.hcl`: Access control policies

3. **Application Integrations**
   - PostgreSQL database connections
   - MinIO storage credentials
   - API keys (OpenRouter, Brave Search)
   - MCP server configurations

## Setup Instructions

### 1. Install Vault Dependencies

```bash
pip install -r requirements-vault.txt
```

### 2. Start Vault Server

```bash
# Development mode
vault server -dev -dev-listen-address=127.0.0.1:8200

# Production mode (using configuration file)
vault server -config=vault-config.hcl
```

### 3. Initialize Vault

```bash
# Initialize Vault
vault operator init

# Unseal Vault (use the unseal keys from initialization)
vault operator unseal
```

### 4. Configure Vault Policies

```bash
# Apply policies
vault policy write admin vault-policies.hcl
vault policy write readonly vault-policies.hcl
```

### 5. Configure Authentication

```bash
# Token authentication (default)
vault token create -policy=admin

# AppRole authentication (recommended for production)
vault auth enable approle
vault write auth/role/admin policies=admin secret_id_ttl=24h
```

### 6. Store Secrets in Vault

```bash
# Database credentials
vault write secret/data/database/postgres host=localhost port=5432 username=postgres password=secure_password database=postgres

# API keys
vault write secret/data/api-keys/openrouter api_key=sk-or-v1-your-api-key
vault write secret/data/api-keys/brave-search api_key=your-brave-api-key

# MinIO credentials
vault write secret/data/storage/minio access_key=minioadmin secret_key=minioadmin endpoint=localhost:9000 bucket=simba-bucket
```

## Environment Variables

### Required Variables

```bash
# Vault connection
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=your-vault-token

# Optional configuration
VAULT_AUTH_METHOD=token  # token, approle, kubernetes
VAULT_NAMESPACE=         # Vault namespace (if using namespaces)
VAULT_TIMEOUT=30         # Connection timeout in seconds
VAULT_VERIFY_SSL=true    # SSL verification
```

### Application Variables

```bash
# Database credentials (fallback if Vault unavailable)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=postgres

# API keys (fallback if Vault unavailable)
OPENROUTER_API_KEY=your-openrouter-api-key
BRAVE_API_KEY=your-brave-api-key

# MinIO credentials (fallback if Vault unavailable)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_ENDPOINT=localhost:9000
MINIO_BUCKET=simba-bucket
```

## Integration Details

### PostgreSQL Database Integration

The PostgreSQL connections now use Vault for credential management:

```python
# Before (hardcoded)
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="2001"
)

# After (Vault integration)
from src.vault_client import get_database_credentials
db_creds = get_database_credentials("postgres")
conn = psycopg2.connect(
    host=db_creds["host"],
    port=db_creds["port"],
    user=db_creds["username"],
    password=db_creds["password"]
)
```

### MinIO Storage Integration

MinIO credentials are retrieved from Vault:

```python
# Before (hardcoded)
self.client = Minio(
    settings.storage.minio_endpoint,
    access_key=settings.storage.minio_access_key,
    secret_key=settings.storage.minio_secret_key,
    secure=settings.storage.minio_secure
)

# After (Vault integration)
from src.vault_client import get_secret
minio_creds = get_secret("secret/data/storage/minio")
self.client = Minio(
    settings.storage.minio_endpoint,
    access_key=minio_creds.get("access_key"),
    secret_key=minio_creds.get("secret_key"),
    secure=settings.storage.minio_secure
)
```

### API Key Management

API keys are managed through Vault with fallback to environment variables:

```python
# Before (environment variables only)
api_key = os.getenv("OPENROUTER_API_KEY")

# After (Vault with fallback)
from src.vault_client import get_api_key
api_key = get_api_key("openrouter") or os.getenv("OPENROUTER_API_KEY")
```

## Security Features

### 1. Authentication Methods

- **Token Authentication**: Simple token-based authentication
- **AppRole Authentication**: Role-based authentication with secret IDs
- **Kubernetes Authentication**: Kubernetes service account authentication

### 2. Access Control

- **Admin Policy**: Full access to all secrets
- **Read-only Policy**: Access to read secrets only
- **CI/CD Policy**: Access for deployment automation

### 3. Secret Management

- **Dynamic Secrets**: Database credentials with automatic rotation
- **Static Secrets**: API keys and configuration
- **Secret Versioning**: Track changes to secrets
- **Lease Management**: Automatic secret expiration and renewal

### 4. Fallback Mechanisms

When Vault is unavailable, the system falls back to environment variables:

```python
def get_database_credentials(self, db_name: str) -> Dict[str, str]:
    # Try Vault first
    if self.is_available():
        path = f"secret/data/database/{db_name}"
        secret = self.get_secret(path)
        if secret:
            return {
                "host": secret.get("host", "localhost"),
                "port": secret.get("port", "5432"),
                "username": secret.get("username", "postgres"),
                "password": secret.get("password", ""),
                "database": secret.get("database", db_name)
            }
    
    # Fallback to environment variables
    return self._get_fallback_db_credentials(db_name)
```

## Monitoring and Logging

### 1. Logging

The Vault client provides comprehensive logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Vault operations are logged with appropriate levels
# INFO: Successful operations
# WARNING: Fallback to environment variables
# ERROR: Authentication failures
```

### 2. Monitoring

Monitor Vault availability and secret access:

```python
# Check Vault availability
if not client.is_available():
    logger.warning("Vault not available, using fallback credentials")

# Monitor secret access patterns
logger.info(f"Retrieved secret: {path}")
```

## Best Practices

### 1. Security

- **Never hardcode credentials**: Always use Vault or environment variables
- **Use least privilege principle**: Grant minimal required access
- **Enable audit logging**: Log all secret access and modifications
- **Regular credential rotation**: Implement automatic secret rotation
- **Use TLS in production**: Always use HTTPS for Vault communication

### 2. Performance

- **Cache secrets**: Use the built-in caching to reduce API calls
- **Batch operations**: Group multiple secret requests
- **Connection pooling**: Reuse Vault client connections
- **Timeout handling**: Implement proper timeout and retry logic

### 3. Reliability

- **Fallback mechanisms**: Always provide fallback to environment variables
- **Health checks**: Monitor Vault availability
- **Circuit breakers**: Implement circuit breakers for Vault failures
- **Graceful degradation**: System should continue operating without Vault

## Troubleshooting

### Common Issues

1. **Vault Connection Failed**
   ```bash
   # Check Vault status
   vault status
   
   # Check network connectivity
   curl http://127.0.0.1:8200/v1/sys/health
   
   # Verify token
   vault token lookup
   ```

2. **Authentication Failed**
   ```bash
   # Check token validity
   vault token lookup
   
   # Verify policy
   vault token lookup -policy=admin
   ```

3. **Secret Not Found**
   ```bash
   # List available secrets
   vault list secret/data
   
   # Check specific secret
   vault read secret/data/database/postgres
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable hvac debug logging
import hvac
hvac.logger.setLevel(logging.DEBUG)
```

## Migration Guide

### From Hardcoded Credentials to Vault

1. **Identify hardcoded credentials** in the codebase
2. **Store credentials in Vault**
3. **Update code to use Vault client**
4. **Remove hardcoded credentials**
5. **Test the integration**
6. **Update documentation**

### Example Migration

```python
# Before
password = "2001"

# After
from src.vault_client import get_database_credentials
db_creds = get_database_credentials("postgres")
password = db_creds["password"]
```

## Testing

### Unit Tests

```python
import pytest
from src.vault_client import VaultClient

def test_vault_client():
    client = VaultClient()
    assert client.is_available() == False  # Without authentication
    
    # Test with mock Vault
    with patch('src.vault_client.hvac.Client') as mock_client:
        mock_client.return_value.is_authenticated.return_value = True
        assert client.authenticate() == True
```

### Integration Tests

```python
def test_vault_integration():
    # Start test Vault instance
    vault_process = start_test_vault()
    
    try:
        # Store test secrets
        store_test_secrets()
        
        # Test secret retrieval
        client = VaultClient()
        secret = client.get_secret("secret/data/test/hello")
        assert secret == "world"
        
    finally:
        # Clean up
        vault_process.terminate()
```

## Production Deployment

### 1. Vault Configuration

```hcl
# Production vault-config.hcl
storage "consul" {
  address = "consul:8500"
  path    = "vault/"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_cert_file = "/etc/vault/tls.crt"
  tls_key_file  = "/etc/vault/tls.key"
}

api_addr = "https://vault.example.com:8200"
ui = true
```

### 2. Authentication Setup

```bash
# Configure AppRole
vault auth enable approle
vault write auth/role/approle policies=approle secret_id_ttl=24h

# Get role ID and secret ID
vault read auth/approle/role/approle/role-id
vault write -f auth/approle/role/approle/secret-id
```

### 3. Environment Configuration

```bash
# Production environment variables
export VAULT_ADDR=https://vault.example.com:8200
export VAULT_AUTH_METHOD=approle
export VAULT_ROLE_ID=your-role-id
export VAULT_SECRET_ID=your-secret-id
export VAULT_NAMESPACE=production
```

## Conclusion

The HashiCorp Vault integration provides a secure, scalable solution for managing secrets in the paddle-plugin system. By following this guide, you can ensure proper implementation and maintenance of the Vault integration.

For additional support, refer to the official HashiCorp Vault documentation: https://www.vaultproject.io/docs