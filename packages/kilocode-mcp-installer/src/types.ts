export interface MCPServerConfig {
    command: string;
    args: string[];
    env?: Record<string, string>;
}

export interface KiloCodeServerConfig {
    command: string;
    args: string[];
    env: {
        NODE_ENV: string;
        KILOCODE_ENV: string;
        KILOCODE_PROJECT_PATH: string;
        [key: string]: string;
    };
}

export interface ServerMetadata {
    name: string;
    description?: string;
    docsPath?: string;
}

export interface MCPConfig {
    mcpServers: Record<string, MCPServerConfig | ServerMetadata>;
}

export interface KiloCodeConfig {
    mcpServers: Record<string, KiloCodeServerConfig | ServerMetadata>;
}