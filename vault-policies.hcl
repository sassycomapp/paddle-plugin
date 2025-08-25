# HashiCorp Vault Policies for paddle-plugin System

# Admin policy - Full access to all secrets
path "sys/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Database secrets engine
path "database/creds/*" {
  capabilities = ["read", "list"]
}

# API keys secrets engine
path "secret/data/api-keys/*" {
  capabilities = ["read", "list", "create", "update", "delete"]
}

# Application secrets
path "secret/data/applications/*" {
  capabilities = ["read", "list", "create", "update", "delete"]
}

# Database configuration
path "secret/data/database/*" {
  capabilities = ["read", "list", "create", "update", "delete"]
}

# Service accounts
path "secret/data/service-accounts/*" {
  capabilities = ["read", "list", "create", "update", "delete"]
}

# Test environment secrets (restricted access)
path "secret/data/test/*" {
  capabilities = ["read", "list"]
}

# Read-only policy for applications
path "secret/data/api-keys/*" {
  capabilities = ["read", "list"]
}

path "secret/data/database/*" {
  capabilities = ["read", "list"]
}

path "secret/data/applications/*" {
  capabilities = ["read", "list"]
}

# CI/CD policy for deployment
path "secret/data/deployment/*" {
  capabilities = ["read", "list", "create", "update"]
}

path "sys/mounts" {
  capabilities = ["read", "list"]
}