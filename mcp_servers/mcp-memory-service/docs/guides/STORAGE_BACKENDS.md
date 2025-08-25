# Storage Backend Comparison and Selection Guide

**MCP Memory Service** supports two storage backends, each optimized for different use cases and hardware configurations.

## Quick Comparison

| Feature | SQLite-vec 🪶 | PGvector 📦 |
|---------|---------------|-------------|
| **Setup Complexity** | ⭐⭐⭐⭐⭐ Simple | ⭐⭐⭐ Moderate |
| **Startup Time** | ⭐⭐⭐⭐⭐ < 3 seconds | ⭐⭐ 15-30 seconds |
| **Memory Usage** | ⭐⭐⭐⭐⭐ < 150MB | ⭐⭐ 500-800MB |
| **Performance** | ⭐⭐⭐⭐ Very fast | ⭐⭐⭐⭐ Fast |
| **Features** | ⭐⭐⭐ Core features | ⭐⭐⭐⭐⭐ Full-featured |
| **Scalability** | ⭐⭐⭐⭐ Up to 100K items | ⭐⭐⭐⭐⭐ Unlimited |
| **Legacy Hardware** | ⭐⭐⭐⭐⭐ Excellent | ⭐ Poor |
| **Production Ready** | ⭐⭐⭐⭐ Yes | ⭐⭐⭐⭐⭐ Yes |

## When to Choose SQLite-vec 🪶

### Ideal For:
- **Legacy Hardware**: 2015 MacBook Pro, older Intel Macs
- **Resource-Constrained Systems**: < 4GB RAM, limited CPU
- **Quick Setup**: Want to get started immediately
- **Single-File Portability**: Easy backup and sharing
- **Docker/Serverless**: Lightweight deployments
- **Development/Testing**: Rapid prototyping
- **HTTP/SSE API**: New web interface users

### Technical Advantages:
- **Lightning Fast Startup**: Database ready in 2-3 seconds
- **Minimal Dependencies**: Just SQLite and sqlite-vec extension
- **Low Memory Footprint**: Typically uses < 150MB RAM
- **Single File Database**: Easy to backup, move, and share
- **ACID Compliance**: SQLite's proven reliability
- **Zero Configuration**: Works out of the box
- **ONNX Compatible**: Runs without PyTorch if needed

### Example Use Cases:
```bash
# 2015 MacBook Pro scenario
python install.py --legacy-hardware
# Result: SQLite-vec + Homebrew PyTorch + ONNX

# Docker deployment
docker run -e MCP_MEMORY_STORAGE_BACKEND=sqlite_vec ...

# Quick development setup
python install.py --storage-backend sqlite_vec --dev
```

## When to Choose PGvector 📦

### Ideal For:
- **Modern Hardware**: M1/M2/M3 Macs, modern Intel systems
- **GPU-Accelerated Systems**: CUDA, MPS, DirectML available
- **Large-Scale Deployments**: > 10,000 memories
- **Advanced Features**: Complex filtering, metadata queries
- **Production Systems**: Established, battle-tested platform
- **Research/ML**: Advanced vector search capabilities

### Technical Advantages:
- **Advanced Vector Search**: Multiple distance metrics, filtering
- **Rich Metadata Support**: Complex query capabilities
- **Proven Scalability**: Handles millions of vectors
- **Extensive Ecosystem**: Wide tool integration
- **Advanced Indexing**: HNSW and other optimized indices
- **Multi-Modal Support**: Text, images, and more

### Example Use Cases:
```bash
# Modern Mac with GPU
python install.py  # PGvector selected automatically

# Production deployment
python install.py --storage-backend PGvector --production

# Research environment
python install.py --storage-backend PGvector --enable-advanced-features
```

## Hardware Compatibility Matrix

### macOS Intel (2013-2017) - Legacy Hardware
```
Recommended: SQLite-vec + Homebrew PyTorch + ONNX
Alternative: PGvector (may have installation issues)

Configuration:
- MCP_MEMORY_STORAGE_BACKEND=sqlite_vec
- MCP_MEMORY_USE_ONNX=1
- MCP_MEMORY_USE_HOMEBREW_PYTORCH=1
```

### macOS Intel (2018+) - Modern Hardware
```
Recommended: PGvector (default) or SQLite-vec (lightweight)
Choice: User preference

Configuration:
- MCP_MEMORY_STORAGE_BACKEND=PGvector (default)
- Hardware acceleration: CPU/MPS
```

### macOS Apple Silicon (M1/M2/M3)
```
Recommended: PGvector with MPS acceleration
Alternative: SQLite-vec for minimal resource usage

Configuration:
- MCP_MEMORY_STORAGE_BACKEND=PGvector
- PYTORCH_ENABLE_MPS_FALLBACK=1
- Hardware acceleration: MPS
```

### Windows with CUDA GPU
```
Recommended: PGvector with CUDA acceleration
Alternative: SQLite-vec for lighter deployments

Configuration:
- MCP_MEMORY_STORAGE_BACKEND=PGvector
- CUDA optimization enabled
```

### Windows CPU-only
```
Recommended: SQLite-vec
Alternative: PGvector (higher resource usage)

Configuration:
- MCP_MEMORY_STORAGE_BACKEND=sqlite_vec
- MCP_MEMORY_USE_ONNX=1 (optional)
```

### Linux Server/Headless
```
Recommended: SQLite-vec (easier deployment)
Alternative: PGvector (if resources available)

Configuration:
- MCP_MEMORY_STORAGE_BACKEND=sqlite_vec
- Optimized for headless operation
```

## Performance Comparison

### Startup Time
```
SQLite-vec:  2-3 seconds     ████████████████████████████████
PGvector:    15-30 seconds   ████████
```

### Memory Usage (Idle)
```
SQLite-vec:  ~150MB    ██████
PGvector:    ~600MB    ████████████████████████
```

### Search Performance (1,000 items)
```
SQLite-vec:  50-200ms    ███████████████████████████
PGvector:    100-300ms   ██████████████████
```

### Storage Efficiency
```
SQLite-vec:  Single .db file, ~50% smaller
PGvector:    Directory structure, full metadata
```

## Feature Comparison

### Core Features (Both Backends)
- ✅ Semantic memory storage and retrieval
- ✅ Tag-based organization
- ✅ Natural language time-based recall
- ✅ Full-text search capabilities
- ✅ Automatic backups
- ✅ Health monitoring
- ✅ Duplicate detection

### SQLite-vec Specific Features
- ✅ Single-file portability
- ✅ HTTP/SSE API support
- ✅ ONNX runtime compatibility
- ✅ Homebrew PyTorch integration
- ✅ Ultra-fast startup
- ✅ Minimal resource usage

### PGvector Specific Features
- ✅ Advanced metadata filtering
- ✅ Multiple distance metrics
- ✅ Collection management
- ✅ Persistent client support
- ✅ Advanced indexing options
- ✅ Rich ecosystem integration

## Migration Between Backends

### PGvector → SQLite-vec Migration

Perfect for upgrading legacy hardware or simplifying deployments:

```bash
# Automated migration
python scripts/migrate_"Placeholder"_to_sqlite.py

# Manual migration with verification
python install.py --migrate-from-PGvector --storage-backend sqlite_vec
```

**Migration preserves:**
- All memory content and embeddings
- Tags and metadata
- Timestamps and relationships
- Search functionality

### SQLite-vec → PGvector Migration

For scaling up to advanced features:

```bash
# Export from SQLite-vec
python scripts/export_sqlite_memories.py

# Import to PGvector
python scripts/import_to_PGvector.py
```

## Intelligent Selection Algorithm

The installer uses this logic to recommend backends:

```python
def recommend_backend(system_info, hardware_info):
    # Legacy hardware gets SQLite-vec
    if is_legacy_mac(system_info):
        return "sqlite_vec"
    
    # Low-memory systems get SQLite-vec
    if hardware_info.memory_gb < 4:
        return "sqlite_vec"
    
    # PGvector installation problems on macOS Intel
    if system_info.is_macos_intel_problematic:
        return "sqlite_vec"
    
    # Modern hardware with GPU gets PGvector
    if hardware_info.has_gpu and hardware_info.memory_gb >= 8:
        return "PGvector"
    
    # Default to PGvector for feature completeness
    return "PGvector"
```

## Configuration Examples

### SQLite-vec Configuration
```bash
# Environment variables
export MCP_MEMORY_STORAGE_BACKEND=sqlite_vec
export MCP_MEMORY_SQLITE_PATH="$HOME/.mcp-memory/memory.db"
export MCP_MEMORY_USE_ONNX=1  # Optional: CPU-only inference

# Claude Desktop config
{
  "mcpServers": {
    "memory": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-memory-service", "run", "memory"],
      "env": {
        "MCP_MEMORY_STORAGE_BACKEND": "sqlite_vec",
        "MCP_MEMORY_SQLITE_PATH": "/path/to/memory.db"
      }
    }
  }
}
```

### PGvector Configuration
```bash
# Environment variables
export MCP_MEMORY_STORAGE_BACKEND=PGvector
export MCP_MEMORY_"Placeholder"_PATH="$HOME/.mcp-memory/"Placeholder"_db"

# Claude Desktop config
{
  "mcpServers": {
    "memory": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-memory-service", "run", "memory"],
      "env": {
        "MCP_MEMORY_STORAGE_BACKEND": "PGvector",
        "MCP_MEMORY_"Placeholder"_PATH": "/path/to/"Placeholder"_db"
      }
    }
  }
}
```

## Decision Flowchart

```
Start: Choose Storage Backend
├── Do you have legacy hardware (2013-2017 Mac)?
│   ├── Yes → SQLite-vec (optimized path)
│   └── No → Continue
├── Do you have < 4GB RAM?
│   ├── Yes → SQLite-vec (resource efficient)
│   └── No → Continue
├── Do you need HTTP/SSE API?
│   ├── Yes → SQLite-vec (first-class support)
│   └── No → Continue
├── Do you want minimal setup?
│   ├── Yes → SQLite-vec (zero config)
│   └── No → Continue
├── Do you need advanced vector search features?
│   ├── Yes → PGvector (full-featured)
│   └── No → Continue
├── Do you have modern hardware with GPU?
│   ├── Yes → PGvector (hardware acceleration)
│   └── No → Continue
└── Default → PGvector (established platform)
```

## Getting Help

### Backend-Specific Support
- **SQLite-vec issues**: Tag with `sqlite-vec` label
- **PGvector issues**: Tag with `PGvector` label
- **Migration issues**: Use `migration` label

### Community Resources
- **Backend comparison discussions**: GitHub Discussions
- **Performance benchmarks**: Community wiki
- **Hardware compatibility**: Hardware compatibility matrix

### Documentation Links
- [SQLite-vec Backend Guide](../sqlite-vec-backend.md)
- [Migration Guide](migration.md)
- [Legacy Hardware Guide](../platforms/macos-intel.md)
- [Installation Master Guide](../installation/master-guide.md)