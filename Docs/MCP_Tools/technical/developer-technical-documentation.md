# MCP Server Technical Documentation for Developers

## Overview

This document provides comprehensive technical documentation for MCP (Model Context Protocol) servers within the KiloCode ecosystem. The documentation is designed for developers who need to understand, implement, and extend MCP servers with advanced technical details, architecture patterns, and implementation guidelines.

## Technical Philosophy

### Key Principles
1. **Simplicity**: Focus on essential technical concepts and patterns
2. **Robustness**: Provide comprehensive technical details and best practices
3. **Security**: Emphasize security considerations and secure implementation
4. **Extensibility**: Design for extensibility and customization
5. **Performance**: Optimize for performance and scalability

### Target Audience
- **Backend Developers**: Developers implementing MCP server backends
- **Frontend Developers**: Developers building MCP client applications
- **Full-Stack Developers**: Developers working with both MCP servers and clients
- **System Architects**: Architects designing MCP-based systems
- **DevOps Engineers**: Engineers deploying and managing MCP infrastructure

## MCP Architecture Overview

### 1. Core Architecture Components

#### 1.1 MCP Protocol Stack
```typescript
// MCP Protocol Stack Architecture
interface MCPProtocolStack {
  // Application Layer
  application: {
    tools: Tool[];
    resources: Resource[];
    capabilities: Capability[];
  };
  
  // Session Layer
  session: {
    id: string;
    state: 'active' | 'inactive' | 'closed';
    capabilities: SessionCapability[];
  };
  
  // Transport Layer
  transport: {
    protocol: 'http' | 'websocket' | 'stdio';
    security: 'none' | 'tls' | 'auth';
    compression: 'none' | 'gzip' | 'brotli';
  };
  
  // Data Layer
  data: {
    serialization: 'json' | 'msgpack' | 'protobuf';
    validation: 'strict' | 'lenient';
    encryption: 'none' | 'aes' | 'rsa';
  };
}
```

#### 1.2 Server Architecture
```typescript
// MCP Server Architecture
interface MCPServerArchitecture {
  // Core Components
  core: {
    server: MCPServer;
    router: Router;
    middleware: Middleware[];
    handlers: Handler[];
  };
  
  // Tool System
  tools: {
    registry: ToolRegistry;
    executor: ToolExecutor;
    validator: ToolValidator;
    logger: ToolLogger;
  };
  
  // Resource System
  resources: {
    manager: ResourceManager;
    storage: ResourceStorage;
    cache: ResourceCache;
    validator: ResourceValidator;
  };
  
  // Session Management
  sessions: {
    manager: SessionManager;
    authenticator: SessionAuthenticator;
    authorizer: SessionAuthorizer;
    monitor: SessionMonitor;
  };
  
  // Transport Layer
  transport: {
    server: TransportServer;
    protocol: ProtocolHandler;
    codec: MessageCodec;
    pipeline: TransportPipeline;
  };
}
```

#### 1.3 Client Architecture
```typescript
// MCP Client Architecture
interface MCPClientArchitecture {
  // Core Components
  core: {
    client: MCPClient;
    connector: ClientConnector;
    pipeline: ClientPipeline;
    handlers: ClientHandler[];
  };
  
  // Tool System
  tools: {
    caller: ToolCaller;
    validator: ToolValidator;
    retry: ToolRetry;
    cache: ToolCache;
  };
  
  // Resource System
  resources: {
    client: ResourceClient;
    cache: ResourceCache;
    loader: ResourceLoader;
    validator: ResourceValidator;
  };
  
  // Session Management
  sessions: {
    manager: SessionManager;
    authenticator: SessionAuthenticator;
    monitor: SessionMonitor;
  };
  
  // Transport Layer
  transport: {
    client: TransportClient;
    protocol: ProtocolHandler;
    codec: MessageCodec;
    pipeline: TransportPipeline;
  };
}
```

### 2. Data Flow Architecture

#### 2.1 Request-Response Flow
```typescript
// Request-Response Flow Architecture
interface RequestResponseFlow {
  // Client Side
  client: {
    request: {
      generate: (toolName: string, params: any) => Request;
      validate: (request: Request) => boolean;
      serialize: (request: Request) => string;
    };
    response: {
      deserialize: (response: string) => Response;
      validate: (response: Response) => boolean;
      process: (response: Response) => any;
    };
  };
  
  // Transport Layer
  transport: {
    encode: (message: Message) => Uint8Array;
    decode: (data: Uint8Array) => Message;
    send: (message: Message) => Promise<void>;
    receive: () => Promise<Message>;
  };
  
  // Server Side
  server: {
    request: {
      receive: () => Promise<Request>;
      deserialize: (data: Uint8Array) => Request;
      validate: (request: Request) => boolean;
    };
    response: {
      process: (request: Request) => Promise<Response>;
      serialize: (response: Response) => string;
      send: (response: Response) => Promise<void>;
    };
  };
}
```

#### 2.2 Session Management Flow
```typescript
// Session Management Flow
interface SessionManagementFlow {
  // Session Creation
  create: {
    request: (clientInfo: ClientInfo) => SessionCreateRequest;
    validate: (request: SessionCreateRequest) => boolean;
    process: (request: SessionCreateRequest) => Session;
    response: (session: Session) => SessionCreateResponse;
  };
  
  // Session Maintenance
  maintain: {
    heartbeat: (session: Session) => HeartbeatRequest;
    validate: (heartbeat: HeartbeatRequest) => boolean;
    process: (heartbeat: HeartbeatRequest) => HeartbeatResponse;
    timeout: (session: Session) => boolean;
  };
  
  // Session Termination
  terminate: {
    request: (session: Session) => SessionTerminateRequest;
    validate: (request: SessionTerminateRequest) => boolean;
    process: (request: SessionTerminateRequest) => SessionTerminateResponse;
    cleanup: (session: Session) => Promise<void>;
  };
}
```

## Implementation Details

### 1. Server Implementation

#### 1.1 Core Server Implementation
```typescript
// Core MCP Server Implementation
class MCPServer {
  private config: ServerConfig;
  private router: Router;
  private middleware: Middleware[];
  private handlers: Handler[];
  private tools: ToolRegistry;
  private resources: ResourceManager;
  private sessions: SessionManager;
  private transport: TransportServer;

  constructor(config: ServerConfig) {
    this.config = config;
    this.router = new Router();
    this.middleware = [];
    this.handlers = [];
    this.tools = new ToolRegistry();
    this.resources = new ResourceManager();
    this.sessions = new SessionManager();
    this.transport = new TransportServer(config.transport);
  }

  // Server Lifecycle
  async start(): Promise<void> {
    await this.transport.start();
    await this.setupRoutes();
    await this.setupMiddleware();
    await this.setupHandlers();
    await this.setupTools();
    await this.setupResources();
    await this.setupSessions();
  }

  async stop(): Promise<void> {
    await this.sessions.shutdown();
    await this.resources.shutdown();
    await this.tools.shutdown();
    await this.transport.stop();
  }

  // Route Setup
  private async setupRoutes(): Promise<void> {
    this.router.addRoute('/tools', this.handleTools.bind(this));
    this.router.addRoute('/resources', this.handleResources.bind(this));
    this.router.addRoute('/sessions', this.handleSessions.bind(this));
    this.router.addRoute('/health', this.handleHealth.bind(this));
  }

  // Middleware Setup
  private async setupMiddleware(): Promise<void> {
    this.middleware.push(new AuthenticationMiddleware());
    this.middleware.push(new AuthorizationMiddleware());
    this.middleware.push(new ValidationMiddleware());
    this.middleware.push(new LoggingMiddleware());
    this.middleware.push(new RateLimitingMiddleware());
  }

  // Handler Setup
  private async setupHandlers(): Promise<void> {
    this.handlers.push(new ToolHandler(this.tools));
    this.handlers.push(new ResourceHandler(this.resources));
    this.handlers.push(new SessionHandler(this.sessions));
    this.handlers.push(new ErrorHandler());
  }

  // Tool Setup
  private async setupTools(): Promise<void> {
    this.tools.registerTool('read_file', new ReadFileTool());
    this.tools.registerTool('write_file', new WriteFileTool());
    this.tools.registerTool('list_directory', new ListDirectoryTool());
    this.tools.registerTool('create_directory', new CreateDirectoryTool());
    this.tools.registerTool('delete_file', new DeleteFileTool());
  }

  // Resource Setup
  private async setupResources(): Promise<void> {
    this.resources.registerResource('filesystem', new FilesystemResource());
    this.resources.registerResource('database', new DatabaseResource());
    this.resources.registerResource('cache', new CacheResource());
  }

  // Session Setup
  private async setupSessions(): Promise<void> {
    this.sessions.setSessionTimeout(this.config.sessionTimeout);
    this.sessions.setSessionCleanupInterval(this.config.cleanupInterval);
  }

  // Request Handling
  async handleRequest(request: Request): Promise<Response> {
    try {
      // Apply middleware
      for (const middleware of this.middleware) {
        request = await middleware.process(request);
      }

      // Route request
      const handler = this.router.getHandler(request.path);
      if (!handler) {
        throw new Error('Handler not found');
      }

      // Handle request
      const response = await handler.handle(request);
      return response;
    } catch (error) {
      // Handle errors
      const errorHandler = this.handlers.find(h => h instanceof ErrorHandler);
      return await errorHandler.handle(error);
    }
  }

  // Health Check
  async handleHealth(request: Request): Promise<Response> {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      sessions: this.sessions.getActiveCount(),
      tools: this.tools.getToolCount(),
      resources: this.resources.getResourceCount(),
    };

    return new Response(200, health);
  }
}
```

#### 1.2 Tool Implementation
```typescript
// Tool Implementation Base Class
abstract class BaseTool {
  abstract name: string;
  abstract description: string;
  abstract parameters: ToolParameters;
  abstract execute(params: any): Promise<ToolResult>;

  // Tool Lifecycle
  async initialize(): Promise<void> {
    // Initialize tool resources
  }

  async validate(params: any): Promise<boolean> {
    // Validate tool parameters
    return this.parameters.validate(params);
  }

  async executeWithValidation(params: any): Promise<ToolResult> {
    if (!await this.validate(params)) {
      throw new Error('Invalid parameters');
    }
    return await this.execute(params);
  }

  async cleanup(): Promise<void> {
    // Cleanup tool resources
  }
}

// File System Tool Implementation
class ReadFileTool extends BaseTool {
  name = 'read_file';
  description = 'Read file contents';
  parameters = {
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: 'Path to the file to read',
      },
      encoding: {
        type: 'string',
        description: 'File encoding (utf8, binary)',
        default: 'utf8',
      },
    },
    required: ['path'],
  };

  async execute(params: any): Promise<ToolResult> {
    try {
      const { path, encoding = 'utf8' } = params;
      
      // Security check - validate path
      if (!this.isValidPath(path)) {
        throw new Error('Invalid file path');
      }

      // Read file
      const content = await fs.promises.readFile(path, encoding);
      
      return {
        success: true,
        content: [
          {
            type: 'text',
            text: content,
          },
        ],
      };
    } catch (error) {
      return {
        success: false,
        error: {
          code: 'FILE_READ_ERROR',
          message: error.message,
        },
      };
    }
  }

  private isValidPath(path: string): boolean {
    // Implement path validation to prevent directory traversal
    return path.startsWith('/workspace/') && !path.includes('..');
  }
}

// Tool Registry Implementation
class ToolRegistry {
  private tools: Map<string, BaseTool> = new Map();
  private logger: Logger;

  constructor(logger: Logger) {
    this.logger = logger;
  }

  registerTool(name: string, tool: BaseTool): void {
    this.tools.set(name, tool);
    this.logger.info(`Tool registered: ${name}`);
  }

  unregisterTool(name: string): void {
    this.tools.delete(name);
    this.logger.info(`Tool unregistered: ${name}`);
  }

  getTool(name: string): BaseTool | undefined {
    return this.tools.get(name);
  }

  getAllTools(): BaseTool[] {
    return Array.from(this.tools.values());
  }

  async initializeAll(): Promise<void> {
    const initPromises = Array.from(this.tools.values()).map(tool => 
      tool.initialize().catch(error => {
        this.logger.error(`Tool initialization failed: ${tool.name}`, error);
      })
    );
    await Promise.all(initPromises);
  }

  async cleanupAll(): Promise<void> {
    const cleanupPromises = Array.from(this.tools.values()).map(tool => 
      tool.cleanup().catch(error => {
        this.logger.error(`Tool cleanup failed: ${tool.name}`, error);
      })
    );
    await Promise.all(cleanupPromises);
  }

  getToolCount(): number {
    return this.tools.size;
  }
}
```

#### 1.3 Resource Implementation
```typescript
// Resource Implementation Base Class
abstract class BaseResource {
  abstract name: string;
  abstract type: string;
  abstract config: ResourceConfig;

  // Resource Lifecycle
  async initialize(): Promise<void> {
    // Initialize resource
  }

  async validate(): Promise<boolean> {
    // Validate resource
    return true;
  }

  async getResource(uri: string): Promise<Resource> {
    // Get resource by URI
    throw new Error('Not implemented');
  }

  async listResources(uri: string): Promise<Resource[]> {
    // List resources under URI
    throw new Error('Not implemented');
  }

  async createResource(uri: string, content: any): Promise<Resource> {
    // Create new resource
    throw new Error('Not implemented');
  }

  async updateResource(uri: string, content: any): Promise<Resource> {
    // Update existing resource
    throw new Error('Not implemented');
  }

  async deleteResource(uri: string): Promise<void> {
    // Delete resource
    throw new Error('Not implemented');
  }

  async cleanup(): Promise<void> {
    // Cleanup resource
  }
}

// File System Resource Implementation
class FilesystemResource extends BaseResource {
  name = 'filesystem';
  type = 'filesystem';
  config: ResourceConfig;

  constructor(config: ResourceConfig) {
    super();
    this.config = config;
  }

  async initialize(): Promise<void> {
    // Initialize filesystem resource
    await fs.promises.mkdir(this.config.root, { recursive: true });
  }

  async getResource(uri: string): Promise<Resource> {
    const path = this.uriToPath(uri);
    const stats = await fs.promises.stat(path);
    
    return {
      uri,
      name: path.basename,
      type: stats.isDirectory() ? 'directory' : 'file',
      size: stats.size,
      modified: stats.mtime,
      created: stats.birthtime,
      content: stats.isFile() ? await this.readFile(path) : null,
    };
  }

  async listResources(uri: string): Promise<Resource[]> {
    const path = this.uriToPath(uri);
    const items = await fs.promises.readdir(path);
    
    const resources = await Promise.all(
      items.map(async (item) => {
        const itemPath = path.join(item);
        const stats = await fs.promises.stat(itemPath);
        
        return {
          uri: this.pathToUri(itemPath),
          name: item,
          type: stats.isDirectory() ? 'directory' : 'file',
          size: stats.size,
          modified: stats.mtime,
          created: stats.birthtime,
          content: stats.isFile() ? await this.readFile(itemPath) : null,
        };
      })
    );
    
    return resources;
  }

  async createResource(uri: string, content: any): Promise<Resource> {
    const path = this.uriToPath(uri);
    await fs.promises.writeFile(path, content);
    return await this.getResource(uri);
  }

  async updateResource(uri: string, content: any): Promise<Resource> {
    const path = this.uriToPath(uri);
    await fs.promises.writeFile(path, content);
    return await this.getResource(uri);
  }

  async deleteResource(uri: string): Promise<void> {
    const path = this.uriToPath(uri);
    await fs.promises.unlink(path);
  }

  private async readFile(path: string): Promise<string> {
    return await fs.promises.readFile(path, 'utf8');
  }

  private uriToPath(uri: string): string {
    // Convert URI to filesystem path
    return path.join(this.config.root, uri.replace(/^filesystem:\//, ''));
  }

  private pathToUri(path: string): string {
    // Convert filesystem path to URI
    const relativePath = path.relative(this.config.root, path);
    return `filesystem:/${relativePath}`;
  }
}

// Resource Manager Implementation
class ResourceManager {
  private resources: Map<string, BaseResource> = new Map();
  private cache: ResourceCache;
  private logger: Logger;

  constructor(logger: Logger, cache: ResourceCache) {
    this.logger = logger;
    this.cache = cache;
  }

  registerResource(name: string, resource: BaseResource): void {
    this.resources.set(name, resource);
    this.logger.info(`Resource registered: ${name}`);
  }

  unregisterResource(name: string): void {
    this.resources.delete(name);
    this.logger.info(`Resource unregistered: ${name}`);
  }

  getResource(name: string): BaseResource | undefined {
    return this.resources.get(name);
  }

  async getResourceByUri(uri: string): Promise<Resource> {
    // Check cache first
    const cached = await this.cache.get(uri);
    if (cached) {
      return cached;
    }

    // Find appropriate resource handler
    const resource = this.findResourceHandler(uri);
    if (!resource) {
      throw new Error(`No resource handler found for URI: ${uri}`);
    }

    // Get resource
    const result = await resource.getResource(uri);
    
    // Cache result
    await this.cache.set(uri, result);
    
    return result;
  }

  async listResources(uri: string): Promise<Resource[]> {
    const resource = this.findResourceHandler(uri);
    if (!resource) {
      throw new Error(`No resource handler found for URI: ${uri}`);
    }

    return await resource.listResources(uri);
  }

  async createResource(uri: string, content: any): Promise<Resource> {
    const resource = this.findResourceHandler(uri);
    if (!resource) {
      throw new Error(`No resource handler found for URI: ${uri}`);
    }

    const result = await resource.createResource(uri, content);
    
    // Invalidate cache
    await this.cache.invalidate(uri);
    
    return result;
  }

  async updateResource(uri: string, content: any): Promise<Resource> {
    const resource = this.findResourceHandler(uri);
    if (!resource) {
      throw new Error(`No resource handler found for URI: ${uri}`);
    }

    const result = await resource.updateResource(uri, content);
    
    // Invalidate cache
    await this.cache.invalidate(uri);
    
    return result;
  }

  async deleteResource(uri: string): Promise<void> {
    const resource = this.findResourceHandler(uri);
    if (!resource) {
      throw new Error(`No resource handler found for URI: ${uri}`);
    }

    await resource.deleteResource(uri);
    
    // Invalidate cache
    await this.cache.invalidate(uri);
  }

  private findResourceHandler(uri: string): BaseResource | undefined {
    for (const resource of this.resources.values()) {
      if (uri.startsWith(`${resource.name}:`)) {
        return resource;
      }
    }
    return undefined;
  }

  async initializeAll(): Promise<void> {
    const initPromises = Array.from(this.resources.values()).map(resource => 
      resource.initialize().catch(error => {
        this.logger.error(`Resource initialization failed: ${resource.name}`, error);
      })
    );
    await Promise.all(initPromises);
  }

  async cleanupAll(): Promise<void> {
    const cleanupPromises = Array.from(this.resources.values()).map(resource => 
      resource.cleanup().catch(error => {
        this.logger.error(`Resource cleanup failed: ${resource.name}`, error);
      })
    );
    await Promise.all(cleanupPromises);
  }

  getResourceCount(): number {
    return this.resources.size;
  }
}
```

### 2. Client Implementation

#### 2.1 Core Client Implementation
```typescript
// Core MCP Client Implementation
class MCPClient {
  private config: ClientConfig;
  private connector: ClientConnector;
  private pipeline: ClientPipeline;
  private tools: ToolCaller;
  private resources: ResourceClient;
  private sessions: SessionManager;
  private transport: TransportClient;

  constructor(config: ClientConfig) {
    this.config = config;
    this.connector = new ClientConnector(config);
    this.pipeline = new ClientPipeline();
    this.tools = new ToolCaller(this.connector);
    this.resources = new ResourceClient(this.connector);
    this.sessions = new SessionManager();
    this.transport = new TransportClient(config.transport);
  }

  // Client Lifecycle
  async connect(): Promise<void> {
    await this.transport.connect();
    await this.setupPipeline();
    await this.setupSessions();
  }

  async disconnect(): Promise<void> {
    await this.sessions.shutdown();
    await this.transport.disconnect();
  }

  // Pipeline Setup
  private async setupPipeline(): Promise<void> {
    this.pipeline.addMiddleware(new RetryMiddleware());
    this.pipeline.addMiddleware(new CacheMiddleware());
    this.pipeline.addMiddleware(new LoggingMiddleware());
    this.pipeline.addMiddleware(new RateLimitingMiddleware());
  }

  // Session Setup
  private async setupSessions(): Promise<void> {
    this.sessions.setSessionTimeout(this.config.sessionTimeout);
    this.sessions.setSessionCleanupInterval(this.config.cleanupInterval);
  }

  // Tool Operations
  async callTool(toolName: string, params: any, options: ToolOptions = {}): Promise<ToolResult> {
    const request = this.tools.createRequest(toolName, params);
    
    // Apply pipeline middleware
    const processedRequest = await this.pipeline.process(request);
    
    // Send request
    const response = await this.transport.send(processedRequest);
    
    // Process response
    return await this.tools.processResponse(response);
  }

  async listTools(): Promise<Tool[]> {
    const request = new Request('tools', { method: 'GET' });
    const response = await this.transport.send(request);
    return response.data.tools;
  }

  // Resource Operations
  async getResource(uri: string): Promise<Resource> {
    return await this.resources.get(uri);
  }

  async listResources(uri: string): Promise<Resource[]> {
    return await this.resources.list(uri);
  }

  async createResource(uri: string, content: any): Promise<Resource> {
    return await this.resources.create(uri, content);
  }

  async updateResource(uri: string, content: any): Promise<Resource> {
    return await this.resources.update(uri, content);
  }

  async deleteResource(uri: string): Promise<void> {
    await this.resources.delete(uri);
  }

  // Session Operations
  async createSession(clientInfo: ClientInfo): Promise<Session> {
    return await this.sessions.create(clientInfo);
  }

  async getSession(sessionId: string): Promise<Session> {
    return await this.sessions.get(sessionId);
  }

  async listSessions(): Promise<Session[]> {
    return await this.sessions.list();
  }

  async terminateSession(sessionId: string): Promise<void> {
    await this.sessions.terminate(sessionId);
  }
}

// Tool Caller Implementation
class ToolCaller {
  private connector: ClientConnector;
  private cache: ToolCache;
  private retry: ToolRetry;
  private validator: ToolValidator;

  constructor(connector: ClientConnector) {
    this.connector = connector;
    this.cache = new ToolCache();
    this.retry = new ToolRetry();
    this.validator = new ToolValidator();
  }

  createRequest(toolName: string, params: any): Request {
    const request = new Request('tools', {
      method: 'POST',
      body: {
        name: toolName,
        arguments: params,
      },
    });

    return request;
  }

  async processResponse(response: Response): Promise<ToolResult> {
    // Validate response
    if (!this.validator.validateResponse(response)) {
      throw new Error('Invalid response');
    }

    // Process result
    const result: ToolResult = {
      success: response.status === 200,
      content: response.data.content || [],
      error: response.data.error || null,
    };

    return result;
  }

  async callWithRetry(toolName: string, params: any, options: ToolOptions = {}): Promise<ToolResult> {
    const cacheKey = this.generateCacheKey(toolName, params);
    
    // Check cache first
    if (options.useCache !== false) {
      const cached = await this.cache.get(cacheKey);
      if (cached) {
        return cached;
      }
    }

    // Call with retry
    const result = await this.retry.execute(async () => {
      const request = this.createRequest(toolName, params);
      const response = await this.connector.send(request);
      return await this.processResponse(response);
    }, options.retryOptions);

    // Cache result
    if (options.useCache !== false) {
      await this.cache.set(cacheKey, result, options.cacheTTL);
    }

    return result;
  }

  private generateCacheKey(toolName: string, params: any): string {
    return `${toolName}:${JSON.stringify(params)}`;
  }
}

// Resource Client Implementation
class ResourceClient {
  private connector: ClientConnector;
  private cache: ResourceCache;
  private loader: ResourceLoader;
  private validator: ResourceValidator;

  constructor(connector: ClientConnector) {
    this.connector = connector;
    this.cache = new ResourceCache();
    this.loader = new ResourceLoader();
    this.validator = new ResourceValidator();
  }

  async get(uri: string): Promise<Resource> {
    const cacheKey = `resource:${uri}`;
    
    // Check cache first
    const cached = await this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Load resource
    const resource = await this.loader.load(uri);
    
    // Validate resource
    if (!this.validator.validate(resource)) {
      throw new Error('Invalid resource');
    }

    // Cache result
    await this.cache.set(cacheKey, resource);

    return resource;
  }

  async list(uri: string): Promise<Resource[]> {
    const request = new Request(`resources/${uri}`, {
      method: 'GET',
    });

    const response = await this.connector.send(request);
    return response.data.resources;
  }

  async create(uri: string, content: any): Promise<Resource> {
    const request = new Request(`resources/${uri}`, {
      method: 'POST',
      body: content,
    });

    const response = await this.connector.send(request);
    return response.data.resource;
  }

  async update(uri: string, content: any): Promise<Resource> {
    const request = new Request(`resources/${uri}`, {
      method: 'PUT',
      body: content,
    });

    const response = await this.connector.send(request);
    return response.data.resource;
  }

  async delete(uri: string): Promise<void> {
    const request = new Request(`resources/${uri}`, {
      method: 'DELETE',
    });

    await this.connector.send(request);
  }
}
```

### 3. Advanced Implementation Patterns

#### 3.1 Plugin Architecture
```typescript
// Plugin System Implementation
interface Plugin {
  name: string;
  version: string;
  initialize(server: MCPServer): Promise<void>;
  cleanup(): Promise<void>;
}

class PluginManager {
  private plugins: Map<string, Plugin> = new Map();
  private server: MCPServer;
  private logger: Logger;

  constructor(server: MCPServer, logger: Logger) {
    this.server = server;
    this.logger = logger;
  }

  async loadPlugin(plugin: Plugin): Promise<void> {
    if (this.plugins.has(plugin.name)) {
      throw new Error(`Plugin already loaded: ${plugin.name}`);
    }

    try {
      await plugin.initialize(this.server);
      this.plugins.set(plugin.name, plugin);
      this.logger.info(`Plugin loaded: ${plugin.name}`);
    } catch (error) {
      this.logger.error(`Plugin load failed: ${plugin.name}`, error);
      throw error;
    }
  }

  async unloadPlugin(name: string): Promise<void> {
    const plugin = this.plugins.get(name);
    if (!plugin) {
      throw new Error(`Plugin not found: ${name}`);
    }

    try {
      await plugin.cleanup();
      this.plugins.delete(name);
      this.logger.info(`Plugin unloaded: ${name}`);
    } catch (error) {
      this.logger.error(`Plugin unload failed: ${name}`, error);
      throw error;
    }
  }

  async reloadPlugin(name: string): Promise<void> {
    const plugin = this.plugins.get(name);
    if (!plugin) {
      throw new Error(`Plugin not found: ${name}`);
    }

    await this.unloadPlugin(name);
    await this.loadPlugin(plugin);
  }

  getLoadedPlugins(): Plugin[] {
    return Array.from(this.plugins.values());
  }
}

// Example Plugin Implementation
class LoggingPlugin implements Plugin {
  name = 'logging';
  version = '1.0.0';

  async initialize(server: MCPServer): Promise<void> {
    // Add logging middleware
    server.addMiddleware(new EnhancedLoggingMiddleware());
    
    // Add logging tools
    server.registerTool('get_logs', new GetLogsTool());
    server.registerTool('clear_logs', new ClearLogsTool());
  }

  async cleanup(): Promise<void> {
    // Cleanup logging resources
  }
}
```

#### 3.2 Event System
```typescript
// Event System Implementation
interface Event {
  type: string;
  timestamp: Date;
  data: any;
  source: string;
}

interface EventHandler {
  handle(event: Event): Promise<void>;
}

class EventBus {
  private handlers: Map<string, EventHandler[]> = new Map();
  private logger: Logger;

  constructor(logger: Logger) {
    this.logger = logger;
  }

  subscribe(eventType: string, handler: EventHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
  }

  unsubscribe(eventType: string, handler: EventHandler): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  async publish(event: Event): Promise<void> {
    const handlers = this.handlers.get(event.type) || [];
    
    for (const handler of handlers) {
      try {
        await handler.handle(event);
      } catch (error) {
        this.logger.error(`Event handler failed for ${event.type}`, error);
      }
    }
  }

  async publishMultiple(events: Event[]): Promise<void> {
    const promises = events.map(event => this.publish(event));
    await Promise.all(promises);
  }
}

// Example Event Handlers
class LoggingEventHandler implements EventHandler {
  private logger: Logger;

  constructor(logger: Logger) {
    this.logger = logger;
  }

  async handle(event: Event): Promise<void> {
    this.logger.info(`Event: ${event.type}`, event.data);
  }
}

class MetricsEventHandler implements EventHandler {
  private metrics: MetricsCollector;

  constructor(metrics: MetricsCollector) {
    this.metrics = metrics;
  }

  async handle(event: Event): Promise<void> {
    this.metrics.recordEvent(event);
  }
}
```

#### 3.3 Configuration Management
```typescript
// Configuration Management Implementation
interface Config {
  [key: string]: any;
}

interface ConfigSource {
  load(): Promise<Config>;
  watch?(callback: (config: Config) => void): void;
  unwatch?(): void;
}

class ConfigManager {
  private config: Config = {};
  private sources: ConfigSource[] = [];
  private watchers: Map<string, (config: Config) => void> = new Map();
  private logger: Logger;

  constructor(logger: Logger) {
    this.logger = logger;
  }

  addSource(source: ConfigSource): void {
    this.sources.push(source);
  }

  async load(): Promise<void> {
    const configs = await Promise.all(
      this.sources.map(source => source.load())
    );

    // Merge configs (later sources override earlier ones)
    this.config = configs.reduce((merged, config) => ({
      ...merged,
      ...config,
    }), {});

    // Notify watchers
    this.notifyWatchers();
  }

  async watch(): Promise<void> {
    for (const source of this.sources) {
      if (source.watch) {
        source.watch((config) => {
          this.updateConfig(config);
        });
      }
    }
  }

  get<T>(key: string, defaultValue?: T): T {
    return this.config[key] ?? defaultValue;
  }

  set(key: string, value: any): void {
    this.config[key] = value;
    this.notifyWatchers();
  }

  getAll(): Config {
    return { ...this.config };
  }

  private updateConfig(newConfig: Config): void {
    this.config = { ...this.config, ...newConfig };
    this.notifyWatchers();
  }

  private notifyWatchers(): void {
    for (const callback of this.watchers.values()) {
      try {
        callback(this.config);
      } catch (error) {
        this.logger.error('Config watcher callback failed', error);
      }
    }
  }

  onConfigChange(callback: (config: Config) => void): void {
    const id = Math.random().toString(36).substr(2, 9);
    this.watchers.set(id, callback);
    return id;
  }

  offConfigChange(id: string): void {
    this.watchers.delete(id);
  }
}

// Example Config Sources
class FileConfigSource implements ConfigSource {
  private filePath: string;

  constructor(filePath: string) {
    this.filePath = filePath;
  }

  async load(): Promise<Config> {
    try {
      const content = await fs.promises.readFile(this.filePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      return {};
    }
  }

  watch(callback: (config: Config) => void): void {
    fs.watchFile(this.filePath, async () => {
      const config = await this.load();
      callback(config);
    });
  }

  unwatch(): void {
    fs.unwatchFile(this.filePath);
  }
}

class EnvironmentConfigSource implements ConfigSource {
  async load(): Promise<Config> {
    const config: Config = {};
    
    // Load environment variables with MCP_ prefix
    for (const [key, value] of Object.entries(process.env)) {
      if (key.startsWith('MCP_')) {
        const configKey = key.substring(4).toLowerCase();
        config[configKey] = value;
      }
    }
    
    return config;
  }
}
```

## Security Implementation

### 1. Authentication and Authorization

#### 1.1 Authentication System
```typescript
// Authentication System Implementation
interface AuthToken {
  token: string;
  type: string;
  expiresAt: Date;
  userId: string;
  permissions: string[];
}

interface AuthProvider {
  authenticate(credentials: Credentials): Promise<AuthToken>;
  validate(token: string): Promise<boolean>;
  refresh(token: string): Promise<AuthToken>;
  revoke(token: string): Promise<void>;
}

class JWTAuthProvider implements AuthProvider {
  private secret: string;
  private issuer: string;
  private audience: string;
  private expiresIn: number;

  constructor(config: AuthConfig) {
    this.secret = config.secret;
    this.issuer = config.issuer;
    this.audience = config.audience;
    this.expiresIn = config.expiresIn;
  }

  async authenticate(credentials: Credentials): Promise<AuthToken> {
    // Validate credentials
    if (!this.validateCredentials(credentials)) {
      throw new Error('Invalid credentials');
    }

    // Generate token
    const token = this.generateToken(credentials);
    
    return {
      token,
      type: 'bearer',
      expiresAt: new Date(Date.now() + this.expiresIn * 1000),
      userId: credentials.userId,
      permissions: credentials.permissions,
    };
  }

  async validate(token: string): Promise<boolean> {
    try {
      const decoded = jwt.verify(token, this.secret) as any;
      
      // Check expiration
      if (decoded.exp < Date.now() / 1000) {
        return false;
      }
      
      // Check issuer and audience
      if (decoded.iss !== this.issuer || decoded.aud !== this.audience) {
        return false;
      }
      
      return true;
    } catch (error) {
      return false;
    }
  }

  async refresh(token: string): Promise<AuthToken> {
    const decoded = jwt.verify(token, this.secret) as any;
    
    // Generate new token
    const newToken = this.generateToken({
      userId: decoded.userId,
      permissions: decoded.permissions,
    });
    
    return {
      token: newToken,
      type: 'bearer',
      expiresAt: new Date(Date.now() + this.expiresIn * 1000),
      userId: decoded.userId,
      permissions: decoded.permissions,
    };
  }

  async revoke(token: string): Promise<void> {
    // Add to blacklist
    await this.addToBlacklist(token);
  }

  private validateCredentials(credentials: Credentials): boolean {
    // Implement credential validation
    return true;
  }

  private generateToken(credentials: Credentials): string {
    const payload = {
      userId: credentials.userId,
      permissions: credentials.permissions,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + this.expiresIn,
      iss: this.issuer,
      aud: this.audience,
    };

    return jwt.sign(payload, this.secret);
  }

  private async addToBlacklist(token: string): Promise<void> {
    // Implement token blacklist
  }
}

// Authentication Middleware
class AuthenticationMiddleware implements Middleware {
  private authProvider: AuthProvider;

  constructor(authProvider: AuthProvider) {
    this.authProvider = authProvider;
  }

  async process(request: Request): Promise<Request> {
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader) {
      throw new Error('Authorization header required');
    }

    const [type, token] = authHeader.split(' ');
    
    if (type.toLowerCase() !== 'bearer') {
      throw new Error('Invalid authentication type');
    }

    const isValid = await this.authProvider.validate(token);
    if (!isValid) {
      throw new Error('Invalid or expired token');
    }

    // Add user info to request
    request.user = await this.extractUserInfo(token);
    
    return request;
  }

  private async extractUserInfo(token: string): Promise<User> {
    // Extract user info from token
    return {
      id: 'user-id',
      permissions: ['read', 'write'],
    };
  }
}
```

#### 1.2 Authorization System
```typescript
// Authorization System Implementation
interface Permission {
  resource: string;
  action: string;
  conditions?: Record<string, any>;
}

interface Role {
  name: string;
  permissions: Permission[];
}

interface User {
  id: string;
  roles: string[];
  permissions: Permission[];
}

class AuthorizationManager {
  private roles: Map<string, Role> = new Map();
  private users: Map<string, User> = new Map();
  private logger: Logger;

  constructor(logger: Logger) {
    this.logger = logger;
  }

  defineRole(role: Role): void {
    this.roles.set(role.name, role);
  }

  assignRole(userId: string, roleName: string): void {
    if (!this.roles.has(roleName)) {
      throw new Error(`Role not found: ${roleName}`);
    }

    const user = this.users.get(userId);
    if (!user) {
      throw new Error(`User not found: ${userId}`);
    }

    if (!user.roles.includes(roleName)) {
      user.roles.push(roleName);
      this.updateUserPermissions(user);
    }
  }

  revokeRole(userId: string, roleName: string): void {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error(`User not found: ${userId}`);
    }

    const index = user.roles.indexOf(roleName);
    if (index > -1) {
      user.roles.splice(index, 1);
      this.updateUserPermissions(user);
    }
  }

  checkPermission(userId: string, resource: string, action: string, context?: any): boolean {
    const user = this.users.get(userId);
    if (!user) {
      return false;
    }

    // Check direct permissions
    const directPermission = user.permissions.find(p => 
      p.resource === resource && p.action === action
    );
    
    if (directPermission && this.checkConditions(directPermission.conditions, context)) {
      return true;
    }

    // Check role permissions
    for (const roleName of user.roles) {
      const role = this.roles.get(roleName);
      if (!role) continue;

      const rolePermission = role.permissions.find(p => 
        p.resource === resource && p.action === action
      );
      
      if (rolePermission && this.checkConditions(rolePermission.conditions, context)) {
        return true;
      }
    }

    return false;
  }

  private updateUserPermissions(user: User): void {
    user.permissions = [];
    
    for (const roleName of user.roles) {
      const role = this.roles.get(roleName);
      if (!role) continue;

      user.permissions.push(...role.permissions);
    }
  }

  private checkConditions(conditions?: Record<string, any>, context?: any): boolean {
    if (!conditions) {
      return true;
    }

    for (const [key, value] of Object.entries(conditions)) {
      if (context && context[key] !== value) {
        return false;
      }
    }

    return true;
  }
}

// Authorization Middleware
class AuthorizationMiddleware implements Middleware {
  private authManager: AuthorizationManager;

  constructor(authManager: AuthorizationManager) {
    this.authManager = authManager;
  }

  async process(request: Request): Promise<Request> {
    const user = request.user as User;
    if (!user) {
      throw new Error('User not authenticated');
    }

    const resource = this.extractResource(request);
    const action = this.extractAction(request);

    const hasPermission = this.authManager.checkPermission(
      user.id,
      resource,
      action,
      request.context
    );

    if (!hasPermission) {
      throw new Error('Insufficient permissions');
    }

    return request;
  }

  private extractResource(request: Request): string {
    // Extract resource from request path
    return request.path.split('/')[1] || 'root';
  }

  private extractAction(request: Request): string {
    // Extract action from request method
    switch (request.method) {
      case 'GET':
        return 'read';
      case 'POST':
        return 'create';
      case 'PUT':
        return 'update';
      case 'DELETE':
        return 'delete';
      default:
        return 'execute';
    }
  }
}
```

### 2. Input Validation and Sanitization

#### 2.1 Input Validation
```typescript
// Input Validation Implementation
interface ValidationRule {
  validate(value: any): boolean;
  message?: string;
}

class StringValidationRule implements ValidationRule {
  private minLength?: number;
  private maxLength?: number;
  private pattern?: RegExp;

  constructor(options: { minLength?: number; maxLength?: number; pattern?: RegExp }) {
    this.minLength = options.minLength;
    this.maxLength = options.maxLength;
    this.pattern = options.pattern;
  }

  validate(value: any): boolean {
    if (typeof value !== 'string') {
      return false;
    }

    if (this.minLength && value.length < this.minLength) {
      return false;
    }

    if (this.maxLength && value.length > this.maxLength) {
      return false;
    }

    if (this.pattern && !this.pattern.test(value)) {
      return false;
    }

    return true;
  }

  get message(): string {
    const messages = [];
    
    if (this.minLength) {
      messages.push(`minimum length of ${this.minLength}`);
    }
    
    if (this.maxLength) {
      messages.push(`maximum length of ${this.maxLength}`);
    }
    
    if (this.pattern) {
      messages.push(`must match pattern ${this.pattern}`);
    }

    return `String must ${messages.join(' and ')}.`;
  }
}

class NumberValidationRule implements ValidationRule {
  private min?: number;
  private max?: number;

  constructor(options: { min?: number; max?: number }) {
    this.min = options.min;
    this.max = options.max;
  }

  validate(value: any): boolean {
    if (typeof value !== 'number') {
      return false;
    }

    if (this.min !== undefined && value < this.min) {
      return false;
    }

    if (this.max !== undefined && value > this.max) {
      return false;
    }

    return true;
  }

  get message(): string {
    const messages = [];
    
    if (this.min !== undefined) {
      messages.push(`minimum value of ${this.min}`);
    }
    
    if (this.max !== undefined) {
      messages.push(`maximum value of ${this.max}`);
    }

    return `Number must ${messages.join(' and ')}.`;
  }
}

class ArrayValidationRule implements ValidationRule {
  private items?: ValidationRule[];

  constructor(items?: ValidationRule[]) {
    this.items = items;
  }

  validate(value: any): boolean {
    if (!Array.isArray(value)) {
      return false;
    }

    if (this.items) {
      for (let i = 0; i < value.length; i++) {
        const item = value[i];
        const rule = this.items[i % this.items.length];
        
        if (!rule.validate(item)) {
          return false;
        }
      }
    }

    return true;
  }

  get message(): string {
    return 'Array must contain valid items.';
  }
}

class ObjectValidationRule implements ValidationRule {
  private properties: Record<string, ValidationRule>;

  constructor(properties: Record<string, ValidationRule>) {
    this.properties = properties;
  }

  validate(value: any): boolean {
    if (typeof value !== 'object' || value === null) {
      return false;
    }

    for (const [key, rule] of Object.entries(this.properties)) {
      const propertyValue = value[key];
      
      if (!rule.validate(propertyValue)) {
        return false;
      }
    }

    return true;
  }

  get message(): string {
    return 'Object must have valid properties.';
  }
}

class ValidationMiddleware implements Middleware {
  private rules: Record<string, ValidationRule>;

  constructor(rules: Record<string, ValidationRule>) {
    this.rules = rules;
  }

  async process(request: Request): Promise<Request> {
    const body = request.body;
    
    for (const [key, rule] of Object.entries(this.rules)) {
      const value = body[key];
      
      if (value !== undefined && !rule.validate(value)) {
        throw new Error(`Invalid value for ${key}: ${rule.message}`);
      }
    }

    return request;
  }
}
```

#### 2.2 Output Sanitization
```typescript
// Output Sanitization Implementation
interface SanitizationRule {
  sanitize(value: any): any;
}

class StringSanitizationRule implements SanitizationRule {
  private maxLength?: number;
  private escapeHtml?: boolean;

  constructor(options: { maxLength?: number; escapeHtml?: boolean }) {
    this.maxLength = options.maxLength;
    this.escapeHtml = options.escapeHtml;
  }

  sanitize(value: any): any {
    if (typeof value !== 'string') {
      return value;
    }

    let sanitized = value;

    if (this.maxLength) {
      sanitized = sanitized.substring(0, this.maxLength);
    }

    if (this.escapeHtml) {
      sanitized = this.escapeHtml(sanitized);
    }

    return sanitized;
  }

  private escapeHtml(text: string): string {
    const map: Record<string, string> = {
      '&': '&',
      '<': '<',
      '>': '>',
      '"': '"',
      "'": '&#039;',
    };

    return text.replace(/[&<>"']/g, (m) => map[m]);
  }
}

class NumberSanitizationRule implements SanitizationRule {
  private min?: number;
  private max?: number;

  constructor(options: { min?: number; max?: number }) {
    this.min = options.min;
    this.max = options.max;
  }

  sanitize(value: any): any {
    if (typeof value !== 'number') {
      return value;
    }

    let sanitized = value;

    if (this.min !== undefined && sanitized < this.min) {
      sanitized = this.min;
    }

    if (this.max !== undefined && sanitized > this.max) {
      sanitized = this.max;
    }

    return sanitized;
  }
}

class ObjectSanitizationRule implements SanitizationRule {
  private properties: Record<string, SanitizationRule>;

  constructor(properties: Record<string, SanitizationRule>) {
    this.properties = properties;
  }

  sanitize(value: any): any {
    if (typeof value !== 'object' || value === null) {
      return value;
    }

    const sanitized: any = {};

    for (const [key, rule] of Object.entries(this.properties)) {
      const propertyValue = value[key];
      sanitized[key] = rule.sanitize(propertyValue);
    }

    return sanitized;
  }
}

class SanitizationMiddleware implements Middleware {
  private rules: Record<string, SanitizationRule>;

  constructor(rules: Record<string, SanitizationRule>) {
    this.rules = rules;
  }

  async process(request: Request): Promise<Request> {
    const response = request.response;
    
    if (response && response.data) {
      response.data = this.sanitize(response.data);
    }

    return request;
  }

  private sanitize(value: any): any {
    if (typeof value === 'object' && value !== null) {
      if (Array.isArray(value)) {
        return value.map(item => this.sanitize(item));
      } else {
        const sanitized: any = {};
        
        for (const [key, val] of Object.entries(value)) {
          if (this.rules[key]) {
            sanitized[key] = this.rules[key].sanitize(val);
          } else {
            sanitized[key] = this.sanitize(val);
          }
        }
        
        return sanitized;
      }
    }

    return value;
  }
}
```

## Performance Optimization

### 1. Caching Strategies

#### 1.1 Multi-Level Cache
```typescript
// Multi-Level Cache Implementation
interface Cache {
  get(key: string): Promise<any>;
  set(key: string, value: any, ttl?: number): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
}

class MemoryCache implements Cache {
  private cache: Map<string, { value: any; expires: number }> = new Map();

  async get(key: string): Promise<any> {
    const item = this.cache.get(key);
    
    if (!item) {
      return null;
    }

    if (item.expires && item.expires < Date.now()) {
      this.cache.delete(key);
      return null;
    }

    return item.value;
  }

  async set(key: string, value: any, ttl?: number): Promise<void> {
    const expires = ttl ? Date.now() + ttl * 1000 : undefined;
    this.cache.set(key, { value, expires });
  }

  async delete(key: string): Promise<void> {
    this.cache.delete(key);
  }

  async clear(): Promise<void> {
    this.cache.clear();
  }
}

class RedisCache implements Cache {
  private redis: Redis;

  constructor(redis: Redis) {
    this.redis = redis;
  }

  async get(key: string): Promise<any> {
    const value = await this.redis.get(key);
    return value ? JSON.parse(value) : null;
  }

  async set(key: string, value: any, ttl?: number): Promise<void> {
    const serialized = JSON.stringify(value);
    await this.redis.set(key, serialized, 'EX', ttl || 3600);
  }

  async delete(key: string): Promise<void> {
    await this.redis.del(key);
  }

  async clear(): Promise<void> {
    await this.redis.flushdb();
  }
}

class MultiLevelCache implements Cache {
  private l1Cache: Cache;
  private l2Cache: Cache;

  constructor(l1Cache: Cache, l2Cache: Cache) {
    this.l1Cache = l1Cache;
    this.l2Cache = l2Cache;
  }

  async get(key: string): Promise<any> {
    // Try L1 cache first
    const value = await this.l1Cache.get(key);
    if (value !== null) {
      return value;
    }

    // Try L2 cache
    const l2Value = await this.l2Cache.get(key);
    if (l2Value !== null) {
      // Promote to L1 cache
      await this.l1Cache.set(key, l2Value);
      return l2Value;
    }

    return null;
  }

  async set(key: string, value: any, ttl?: number): Promise<void> {
    // Set in both caches
    await this.l1Cache.set(key, value, ttl);
    await this.l2Cache.set(key, value, ttl);
  }

  async delete(key: string): Promise<void> {
    // Delete from both caches
    await this.l1Cache.delete(key);
    await this.l2Cache.delete(key);
  }

  async clear(): Promise<void> {
    // Clear both caches
    await this.l1Cache.clear();
    await this.l2Cache.clear();
  }
}

// Cache Middleware
class CacheMiddleware implements Middleware {
  private cache: Cache;
  private excludePatterns: RegExp[];

  constructor(cache: Cache, excludePatterns: RegExp[] = []) {
    this.cache = cache;
    this.excludePatterns = excludePatterns;
  }

  async process(request: Request): Promise<Request> {
    // Check if request should be cached
    if (this.shouldExclude(request)) {
      return request;
    }

    // Generate cache key
    const cacheKey = this.generateCacheKey(request);

    // Try to get from cache
    const cached = await this.cache.get(cacheKey);
    if (cached) {
      request.cached = true;
      request.response = cached;
      return request;
    }

    return request;
  }

  private shouldExclude(request: Request): boolean {
    return this.excludePatterns.some(pattern => pattern.test(request.path));
  }

  private generateCacheKey(request: Request): string {
    const method = request.method;
    const path = request.path;
    const body = JSON.stringify(request.body);
    
    return `${method}:${path}:${body}`;
  }
}
```

#### 1.2 Cache Invalidation
```typescript
// Cache Invalidation Implementation
class CacheInvalidator {
  private cache: Cache;
  private subscriptions: Map<string, Set<(key: string) => void>> = new Map();

  constructor(cache: Cache) {
    this.cache = cache;
  }

  async invalidate(pattern: string): Promise<void> {
    const keys = await this.findKeys(pattern);
    
    for (const key of keys) {
      await this.cache.delete(key);
      this.notifySubscribers(key);
    }
  }

  async invalidateByTag(tag: string): Promise<void> {
    const pattern = `tag:${tag}:*`;
    await this.invalidate(pattern);
  }

  subscribe(pattern: string, callback: (key: string) => void): () => void {
    if (!this.subscriptions.has(pattern)) {
      this.subscriptions.set(pattern, new Set());
    }
    
    this.subscriptions.get(pattern)!.add(callback);
    
    return () => {
      const callbacks = this.subscriptions.get(pattern);
      if (callbacks) {
        callbacks.delete(callback);
      }
    };
  }

  private async findKeys(pattern: string): Promise<string[]> {
    // Implement key finding based on pattern
    // This would depend on the cache implementation
    return [];
  }

  private notifySubscribers(key: string): void {
    for (const [pattern, callbacks] of this.subscriptions) {
      if (this.matchesPattern(key, pattern)) {
        for (const callback of callbacks) {
          try {
            callback(key);
          } catch (error) {
            console.error('Cache invalidation callback failed:', error);
          }
        }
      }
    }
  }

  private matchesPattern(key: string, pattern: string): boolean {
    // Simple pattern matching
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(key);
  }
}

// Tag-based Cache Management
class CacheTagManager {
  private cache: Cache;
  private invalidator: CacheInvalidator;

  constructor(cache: Cache) {
    this.cache = cache;
    this.invalidator = new CacheInvalidator(cache);
  }

  async setWithTags(key: string, value: any, tags: string[], ttl?: number): Promise<void> {
    // Set the value
    await this.cache.set(key, value, ttl);

    // Set tag references
    for (const tag of tags) {
      const tagKey = `tag:${tag}:${key}`;
      await this.cache.set(tagKey, '1', ttl);
    }
  }

  async invalidateByTags(tags: string[]): Promise<void> {
    for (const tag of tags) {
      await this.invalidator.invalidateByTag(tag);
    }
  }

  async getTags(key: string): Promise<string[]> {
    // This would require storing tags with the key
    // For simplicity, we'll return an empty array
    return [];
  }
}
```

### 2. Connection Pooling

#### 2.1 Connection Pool Implementation
```typescript
// Connection Pool Implementation
interface Connection {
  id: string;
  createdAt: Date;
  lastUsed: Date;
  isValid(): boolean;
  close(): Promise<void>;
}

class ConnectionPool<T extends Connection> {
  private pool: T[] = [];
  private active: Set<string> = new Set();
  private factory: () => Promise<T>;
  private validator: (connection: T) => Promise<boolean>;
  private maxSize: number;
  private minSize: number;
  private idleTimeout: number;

  constructor(
    factory: () => Promise<T>,
    validator: (connection: T) => Promise<boolean>,
    options: { maxSize: number; minSize: number; idleTimeout: number }
  ) {
    this.factory = factory;
    this.validator = validator;
    this.maxSize = options.maxSize;
    this.minSize = options.minSize;
    this.idleTimeout = options.idleTimeout;
  }

  async getConnection(): Promise<T> {
    // Try to get an existing connection
    const connection = await this.getExistingConnection();
    
    if (connection) {
      return connection;
    }

    // Create a new connection if under max size
    if (this.pool.length + this.active.size < this.maxSize) {
      return await this.createConnection();
    }

    // Wait for an available connection
    return await this.waitForConnection();
  }

  async releaseConnection(connection: T): Promise<void> {
    const id = connection.id;
    
    if (!this.active.has(id)) {
      return;
    }

    this.active.delete(id);

    // Validate connection
    const isValid = await this.validator(connection);
    
    if (isValid) {
      // Return to pool
      this.pool.push(connection);
      
      // Start cleanup timer
      this.startCleanupTimer(connection);
    } else {
      // Close invalid connection
      await connection.close();
    }
  }

  async closeAll(): Promise<void> {
    // Close all connections in pool
    const closePromises = this.pool.map(conn => conn.close());
    await Promise.all(closePromises);
    
    this.pool = [];
    this.active.clear();
  }

  private async getExistingConnection(): Promise<T | null> {
    // Check for idle connections
    const now = Date.now();
    
    for (let i = this.pool.length - 1; i >= 0; i--) {
      const connection = this.pool[i];
      
      // Check if connection has been idle too long
      if (now - connection.lastUsed.getTime() > this.idleTimeout) {
        await connection.close();
        this.pool.splice(i, 1);
        continue;
      }

      // Validate connection
      const isValid = await this.validator(connection);
      
      if (isValid) {
        this.pool.splice(i, 1);
        this.active.add(connection.id);
        connection.lastUsed = new Date();
        return connection;
      } else {
        await connection.close();
        this.pool.splice(i, 1);
      }
    }

    return null;
  }

  private async createConnection(): Promise<T> {
    const connection = await this.factory();
    this.active.add(connection.id);
    return connection;
  }

  private async waitForConnection(): Promise<T> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Connection pool timeout'));
      }, 5000);

      const check = () => {
        if (this.pool.length > 0) {
          clearTimeout(timeout);
          const connection = this.pool.pop()!;
          this.active.add(connection.id);
          resolve(connection);
        } else {
          setTimeout(check, 100);
        }
      };

      check();
    });
  }

  private startCleanupTimer(connection: T): void {
    setTimeout(async () => {
      const index = this.pool.findIndex(conn => conn.id === connection.id);
      
      if (index > -1) {
        const isValid = await this.validator(connection);
        
        if (!isValid) {
          await connection.close();
          this.pool.splice(index, 1);
        }
      }
    }, this.idleTimeout);
  }
}

// Database Connection Pool Example
class DatabaseConnection implements Connection {
  id: string;
  createdAt: Date;
  lastUsed: Date;
  private connection: any;

  constructor(connection: any) {
    this.id = Math.random().toString(36).substr(2, 9);
    this.createdAt = new Date();
    this.lastUsed = new Date();
    this.connection = connection;
  }

  isValid(): boolean {
    // Check if database connection is still valid
    try {
      this.connection.ping();
      return true;
    } catch (error) {
      return false;
    }
  }

  async close(): Promise<void> {
    await this.connection.end();
  }

  async query(sql: string, params?: any[]): Promise<any> {
    this.lastUsed = new Date();
    return await this.connection.query(sql, params);
  }
}

class DatabaseConnectionPool extends ConnectionPool<DatabaseConnection> {
  constructor(config: any) {
    const factory = async () => {
      const connection = await createDatabaseConnection(config);
      return new DatabaseConnection(connection);
    };

    const validator = async (connection: DatabaseConnection) => {
      return connection.isValid();
    };

    super(factory, validator, {
      maxSize: 10,
      minSize: 2,
      idleTimeout: 30000, // 30 seconds
    });
  }
}
```

### 3. Performance Monitoring

#### 3.1 Metrics Collection
```typescript
// Metrics Collection Implementation
interface Metric {
  name: string;
  type: 'counter' | 'gauge' | 'histogram';
  value: number;
  timestamp: Date;
  tags?: Record<string, string>;
}

class MetricsCollector {
  private metrics: Map<string, Metric[]> = new Map();
  private aggregators: Map<string, (metrics: Metric[]) => number> = new Map();

  constructor() {
    // Register default aggregators
    this.registerAggregator('avg', this.calculateAverage);
    this.registerAggregator('sum', this.calculateSum);
    this.registerAggregator('min', this.calculateMin);
    this.registerAggregator('max', this.calculateMax);
    this.registerAggregator('count', this.calculateCount);
  }

  recordMetric(metric: Metric): void {
    const key = this.getMetricKey(metric);
    
    if (!this.metrics.has(key)) {
      this.metrics.set(key, []);
    }
    
    this.metrics.get(key)!.push(metric);
    
    // Keep only recent metrics (last 1000)
    const metrics = this.metrics.get(key)!;
    if (metrics.length > 1000) {
      metrics.splice(0, metrics.length - 1000);
    }
  }

  getMetric(name: string, aggregator: string = 'avg'): number {
    const key = name;
    const metrics = this.metrics.get(key) || [];
    
    if (metrics.length === 0) {
      return 0;
    }

    const aggregatorFn = this.aggregators.get(aggregator);
    if (!aggregatorFn) {
      throw new Error(`Unknown aggregator: ${aggregator}`);
    }

    return aggregatorFn(metrics);
  }

  getMetrics(name: string): Metric[] {
    const key = name;
    return this.metrics.get(key) || [];
  }

  registerAggregator(name: string, aggregator: (metrics: Metric[]) => number): void {
    this.aggregators.set(name, aggregator);
  }

  private getMetricKey(metric: Metric): string {
    const tags = metric.tags ? Object.entries(metric.tags).sort().map(([k, v]) => `${k}=${v}`).join(',') : '';
    return `${metric.name}${tags ? `:${tags}` : ''}`;
  }

  private calculateAverage(metrics: Metric[]): number {
    if (metrics.length === 0) return 0;
    const sum = metrics.reduce((acc, m) => acc + m.value, 0);
    return sum / metrics.length;
  }

  private calculateSum(metrics: Metric[]): number {
    return metrics.reduce((acc, m) => acc + m.value, 0);
  }

  private calculateMin(metrics: Metric[]): number {
    return Math.min(...metrics.map(m => m.value));
  }

  private calculateMax(metrics: Metric[]): number {
    return Math.max(...metrics.map(m => m.value));
  }

  private calculateCount(metrics: Metric[]): number {
    return metrics.length;
  }
}

// Performance Middleware
class PerformanceMiddleware implements Middleware {
  private metrics: MetricsCollector;
  private startTime: Map<string, number> = new Map();

  constructor(metrics: MetricsCollector) {
    this.metrics = metrics;
  }

  async process(request: Request): Promise<Request> {
    const startTime = Date.now();
    this.startTime.set(request.id, startTime);

    // Record request start
    this.metrics.recordMetric({
      name: 'request.start',
      type: 'counter',
      value: 1,
      timestamp: new Date(),
      tags: {
        method: request.method,
        path: request.path,
      },
    });

    return request;
  }

  async processResponse(request: Request, response: Response): Promise<Response> {
    const startTime = this.startTime.get(request.id);
    
    if (startTime) {
      const duration = Date.now() - startTime;
      
      // Record request duration
      this.metrics.recordMetric({
        name: 'request.duration',
        type: 'histogram',
        value: duration,
        timestamp: new Date(),
        tags: {
          method: request.method,
          path: request.path,
          status: response.status.toString(),
        },
      });

      // Record request end
      this.metrics.recordMetric({
        name: 'request.end',
        type: 'counter',
        value: 1,
        timestamp: new Date(),
        tags: {
          method: request.method,
          path: request.path,
          status: response.status.toString(),
        },
      });

      this.startTime.delete(request.id);
    }

    return response;
  }
}
```

## Testing and Quality Assurance

### 1. Unit Testing

#### 1.1 Testing Framework Setup
```typescript
// Testing Framework Configuration
import { expect } from 'chai';
import { SinonStub } from 'sinon';

// Test Configuration
const testConfig = {
  timeout: 5000,
  retries: 3,
  bail: false,
};

// Test Utilities
class TestUtils {
  static createMockRequest(method: string, path: string, body?: any): Request {
    return {
      id: Math.random().toString(36).substr(2, 9),
      method,
      path,
      headers: new Map(),
      body,
      context: {},
    };
  }

  static createMockResponse(status: number, data?: any): Response {
    return {
      status,
      data,
      headers: new Map(),
    };
  }

  static createMockConnection(): Connection {
    return {
      id: Math.random().toString(36).substr(2, 9),
      createdAt: new Date(),
      lastUsed: new Date(),
      isValid: () => true,
      close: async () => {},
    };
  }

  static async waitFor(condition: () => Promise<boolean>, timeout: number = 5000): Promise<void> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      if (await condition()) {
        return;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    throw new Error('Timeout waiting for condition');
  }
}

// Base Test Class
abstract class BaseTest {
  protected beforeEach(): Promise<void> {
    return Promise.resolve();
  }

  protected afterEach(): Promise<void> {
    return Promise.resolve();
  }

  protected async setup(): Promise<void> {
    await this.beforeEach();
  }

  protected async teardown(): Promise<void> {
    await this.afterEach();
  }

  protected async test(name: string, testFn: () => Promise<void>): Promise<void> {
    try {
      await this.setup();
      await testFn();
    } catch (error) {
      throw error;
    } finally {
      await this.teardown();
    }
  }
}
```

#### 1.2 Unit Test Examples
```typescript
// Tool Unit Tests
describe('ReadFileTool', () => {
  let tool: ReadFileTool;
  let mockFs: any;

  beforeEach(() => {
    mockFs = {
      readFile: sinon.stub(),
    };
    
    tool = new ReadFileTool(mockFs);
  });

  afterEach(() => {
    sinon.restore();
  });

  it('should read file successfully', async () => {
    const mockContent = 'File content';
    mockFs.readFile.resolves(mockContent);

    const result = await tool.execute({
      path: '/workspace/test.txt',
    });

    expect(result.success).to.be.true;
    expect(result.content[0].text).to.equal(mockContent);
    expect(mockFs.readFile).to.have.been.calledWith('/workspace/test.txt', 'utf8');
  });

  it('should handle file not found error', async () => {
    mockFs.readFile.rejects(new Error('ENOENT: no such file or directory'));

    const result = await tool.execute({
      path: '/workspace/nonexistent.txt',
    });

    expect(result.success).to.be.false;
    expect(result.error).to.include({
      code: 'FILE_READ_ERROR',
    });
  });

  it('should validate file path', async () => {
    const result = await tool.execute({
      path: '/etc/passwd',
    });

    expect(result.success).to.be.false;
    expect(result.error).to.include({
      code: 'FILE_READ_ERROR',
    });
  });

  it('should use default encoding', async () => {
    mockFs.readFile.resolves('content');

    await tool.execute({
      path: '/workspace/test.txt',
    });

    expect(mockFs.readFile).to.have.been.calledWith('/workspace/test.txt', 'utf8');
  });

  it('should use specified encoding', async () => {
    mockFs.readFile.resolves('content');

    await tool.execute({
      path: '/workspace/test.txt',
      encoding: 'binary',
    });

    expect(mockFs.readFile).to.have.been.calledWith('/workspace/test.txt', 'binary');
  });
});

// Server Unit Tests
describe('MCPServer', () => {
  let server: MCPServer;
  let mockTransport: any;
  let mockTools: any;
  let mockResources: any;
  let mockSessions: any;

  beforeEach(() => {
    mockTransport = {
      start: sinon.stub(),
      stop: sinon.stub(),
      send: sinon.stub(),
    };

    mockTools = {
      registerTool: sinon.stub(),
      getTool: sinon.stub(),
    };

    mockResources = {
      registerResource: sinon.stub(),
      getResource: sinon.stub(),
    };

    mockSessions = {
      setSessionTimeout: sinon.stub(),
      setSessionCleanupInterval: sinon.stub(),
    };

    server = new MCPServer({
      transport: mockTransport,
      tools: mockTools,
      resources: mockResources,
      sessions: mockSessions,
    });
  });

  afterEach(() => {
    sinon.restore();
  });

  it('should start successfully', async () => {
    await server.start();

    expect(mockTransport.start).to.have.been.calledOnce;
    expect(mockTools.registerTool).to.have.been.called;
    expect(mockResources.registerResource).to.have.been.called;
    expect(mockSessions.setSessionTimeout).to.have.been.called;
  });

  it('should stop successfully', async () => {
    await server.stop();

    expect(mockTransport.stop).to.have.been.calledOnce;
  });

  it('should handle request successfully', async () => {
    const mockRequest = TestUtils.createMockRequest('