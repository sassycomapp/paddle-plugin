"""
Cache MCP Server - Intelligent 5-Layer Caching Architecture

This package implements a comprehensive cache management system with five intelligent layers:
- Predictive Cache (Zero-Token Hinting Layer)
- Semantic Cache (Adaptive Prompt Reuse Layer) 
- Vector Cache (Embedding-Based Context Selector)
- Global Knowledge Cache (Fallback Memory)
- Persistent Context Memory (Vector Diary)

Author: KiloCode
License: Apache 2.0
"""

__version__ = "1.0.0"
__author__ = "KiloCode"
__email__ = "dev@kilocode.com"

from .core.base_cache import BaseCache
from .core.config import CacheConfig
from .mcp.server import CacheMCPServer

__all__ = [
    "BaseCache",
    "CacheConfig", 
    "CacheMCPServer"
]