export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  appName: import.meta.env.VITE_APP_NAME || 'Simba',
  // API keys for external services - loaded from environment variables
  // These should be configured to reference Vault secrets in production
  openRouterApiKey: import.meta.env.VITE_OPENROUTER_API_KEY,
  braveApiKey: import.meta.env.VITE_BRAVE_API_KEY,
  openaiApiKey: import.meta.env.VITE_OPENAI_API_KEY,
  // Security configuration
  enableAuth: import.meta.env.VITE_ENABLE_AUTH === 'true',
  enableApiKeys: import.meta.env.VITE_ENABLE_API_KEYS === 'true',
} as const

// Type-safe config access
export type Config = typeof config

// Vault integration for frontend (when available)
export class VaultConfig {
  private static instance: VaultConfig
  private config: Config

  private constructor() {
    this.config = config
  }

  static getInstance(): VaultConfig {
    if (!VaultConfig.instance) {
      VaultConfig.instance = new VaultConfig()
    }
    return VaultConfig.instance
  }

  async loadVaultConfig(): Promise<void> {
    // In production, this would make API calls to a backend endpoint
    // that retrieves secrets from Vault
    try {
      // This is a placeholder for actual Vault integration
      // In a real implementation, this would call a secure backend endpoint
      const response = await fetch('/api/vault/config')
      if (response.ok) {
        const vaultConfig = await response.json()
        this.config = { ...this.config, ...vaultConfig }
        console.log('Vault configuration loaded successfully')
      }
    } catch (error) {
      console.warn('Failed to load Vault configuration, using environment variables:', error)
      // Fall back to environment variables
    }
  }

  getConfig(): Config {
    return this.config
  }

  getApiKey(service: 'openrouter' | 'brave' | 'openai'): string | undefined {
    return this.config[`${service}ApiKey` as keyof Config] as string | undefined
  }

  hasValidApiKey(service: 'openrouter' | 'brave' | 'openai'): boolean {
    return !!this.getApiKey(service)
  }
}

// Export singleton instance
export const vaultConfig = VaultConfig.getInstance()