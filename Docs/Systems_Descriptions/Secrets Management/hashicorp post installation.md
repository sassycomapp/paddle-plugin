# HashiCorp Vault Post-Installation Report

## Brief Overview
HashiCorp Vault has been installed and configured for local development and secret management. It provides a secure centralized location for storing and managing sensitive data such as API keys, passwords, and certificates.

## Installation Information
- **Installation Method**: Chocolatey (`choco install vault -y`)
- **Version**: Vault v1.20.0 (built 2025-06-23T10:21:30Z)
- **Main Executable**: `vault.exe` (located in `C:\ProgramData\chocolatey\bin`)
- **Status**: ✅ **INSTALLED and RUNNING** (in development mode)

## Configuration
**Environment Configuration (.env):**
```bash
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=hvs.RQ2KK3iSPqaPbV1IxefJdVRz
```

**Development Mode Configuration:**
- **API Address**: `http://127.0.0.1:8200`
- **Cluster Address**: `https://127.0.0.1:8201`
- **Storage Backend**: In-memory (for development only)
- **Unseal Key**: `eATCQhdgiPp72id4JyUG/O05ZfdpN0OT9y/DAGuxk9Y=` (not needed in dev mode)
- **Root Token**: `hvs.RQ2KK3iSPqaPbV1IxefJdVRz`

## Integration
- **VS Code Extension**: "HashiCorp Vault" extension recommended for IDE integration
- **Environment Variables**: Configured via `.env` file for application use
- **CLI**: Direct command-line interaction using `vault` CLI
- **Applications**: Can integrate using `VAULT_ADDR` and `VAULT_TOKEN` from environment

## Startup Information
**Development Mode Start:**
```bash
vault server -dev
```
This command starts Vault in development mode, which is suitable for local testing and initial setup. It runs entirely in-memory and starts unsealed.

**Setting Environment Variables (PowerShell):**
```powershell
$env:VAULT_ADDR="http://127.0.0.1:8200"
```

**Login (if needed after setting VAULT_ADDR):**
```bash
vault login hvs.RQ2KK3iSPqaPbV1IxefJdVRz
```

## Usage
### Basic CLI Commands:

**Check Status:**
```bash
vault status
```

**Store a Secret (KV-v2 Engine):**
```bash
vault kv put secret/myapp/api-key key="my-secret-api-value"
```

**Retrieve a Secret:**
```bash
vault kv get secret/myapp/api-key
```

**List Secrets:**
```bash
vault kv list secret/
```

**Delete a Secret:**
```bash
vault kv delete secret/myapp/api-key
```

### Example Usage in Applications:
```javascript
// Example Node.js application using Vault SDK
const { VaultClient } = require('@hashicorp/vault-client');

const client = new VaultClient({
  address: process.env.VAULT_ADDR,
  token: process.env.VAULT_TOKEN,
});

async function getSecret(path) {
  const response = await client.secrets.kv.v2.readSecretVersion({ path });
  return response.data.data;
}

// Usage
getSecret('secret/myapp/api-key')
  .then(secret => console.log('API Key:', secret.key))
  .catch(err => console.error('Error retrieving secret:', err));
```

## Key Features
1. **Secret Management**: Secure storage and management of secrets, keys, and certificates.
2. **Dynamic Secrets**: On-the-fly generation of credentials for databases, services, etc.
3. **Lease Management**: Automatic rotation and revocation of secrets.
4. **Multiple Storage Backends**: Supports file, Consul, GCS, Azure, AWS, and more.
5. **Authentication Methods**: Token, AppRole, Kubernetes, LDAP, AWS, etc.
6. **Secret Engines**: Pluggable systems for secrets management (KV, database, transit, etc.).
7. **High Availability**: Enterprise-grade clustering and replication.
8. **Audit Devices**: Logging and monitoring of all Vault operations.

## Security Considerations
- **Development Mode**: WARNING - Dev mode is insecure and should NOT be used in production. It stores data in memory and uses a single unseal key.
- **Production Setup**: For production, use a persistent storage backend (e.g., Consul, AWS S3, Azure Blob Storage), enable TLS, and configure proper authentication and authorization.
- **Root Token**: The root token provides full access to Vault. Rotate it and use more specific policies in production.
- **Unseal Keys**: In production, multiple unseal keys are generated and should be stored securely by different parties.
- **Vault Agent**: Consider using Vault Agent for automatic authentication and token renewal in production environments.

## Troubleshooting
- **Connection Issues**: Ensure `VAULT_ADDR` is set correctly and Vault is running.
- **Permission Denied**: Verify your token has the necessary policies.
- **Sealed Vault**: In production, you'll need to provide unseal keys to access the vault.
- **Commands Not Found**: Ensure the `vault` executable is in your system's PATH.
- **Port Already in Use**: Change the port using the `-dev-listen-address` flag (e.g., `vault server -dev -dev-listen-address=127.0.0.1:8201`).

## Testing
**Basic Verification:**
1. Ensure Vault is running: `vault status`
2. Check authentication: `vault token lookup`
3. Store and retrieve a test secret:
   ```bash
   vault kv put secret/test/hello value=world
   vault kv get secret/test/hello
   ```

## Performance Metrics (Dev Mode)
- **Response Time**: Sub-millisecond for in-memory operations.
- **Storage**: Volatile, cleared on restart.
- **Concurrent Requests**: Limited by system resources.

## Next Steps
1. **Install VS Code Extension**: Search for "HashiCorp Vault" in the VS Code marketplace.
2. **Explore Secret Engines**: Learn about and configure different secret engines (e.g., database, transit).
3. **Implement Authentication**: Set up AppRole, Kubernetes, or other authentication methods.
4. **Create Policies**: Define fine-grained access control policies.
5. **Plan for Production**: Design a production-ready Vault architecture with persistent storage and HA.
6. **Integrate with Applications**: Use official Vault SDKs or CLI to integrate with your applications.

## Documentation
- [Official HashiCorp Vault Documentation](https://developer.hashicorp.com/vault/docs)
- [Vault CLI Documentation](https://developer.hashicorp.com/vault/docs/commands)
- [Vault SDKs](https://developer.hashicorp.com/vault/docs/libraries)
