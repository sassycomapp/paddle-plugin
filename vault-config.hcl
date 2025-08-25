# HashiCorp Vault Configuration
# This file defines the Vault server configuration for the paddle-plugin system

# Storage configuration
storage "file" {
  path = "/tmp/vault/data"
}

# Listener configuration
listener "tcp" {
  address     = "127.0.0.1:8200"
  tls_disable = 1
}

# API configuration
api_addr = "http://127.0.0.1:8200"

# UI configuration
ui = true

# Seal configuration (for production, use proper sealing method)
seal "awskms" {
  region     = "us-east-1"
  kms_key_id = "alias/vault"
}