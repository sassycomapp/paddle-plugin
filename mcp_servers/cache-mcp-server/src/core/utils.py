"""
Utility functions for the Cache MCP Server

This module provides common utility functions used across the cache system,
including embedding generation, similarity calculations, and performance monitoring.

Author: KiloCode
License: Apache 2.0
"""

import time
import logging
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics container."""
    operation: str
    duration_ms: float
    success: bool
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class CacheUtils:
    """Utility class for cache operations."""
    
    @staticmethod
    def generate_embedding(text: str, model_name: str = "all-MiniLM-L6-v2") -> List[float]:
        """
        Generate embedding for text using the specified model.
        
        Args:
            text: Input text to embed
            model_name: Name of the embedding model
            
        Returns:
            Embedding vector as a list of floats
        """
        try:
            # This is a placeholder implementation
            # In a real implementation, you would use a proper embedding library
            # like sentence-transformers, Simba, or OpenAI embeddings
            
            # Simple hash-based embedding for demonstration
            # In production, replace with actual embedding generation
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to float vector (384 dimensions for MiniLM-L6-v2)
            embedding = []
            for i in range(384):
                byte_index = i // 8
                bit_index = i % 8
                if byte_index < len(hash_bytes):
                    bit = (hash_bytes[byte_index] >> bit_index) & 1
                    embedding.append(float(bit))
                else:
                    embedding.append(0.0)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    @staticmethod
    def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        try:
            if len(vec1) != len(vec2):
                raise ValueError("Vectors must have the same dimension")
            
            # Convert to numpy arrays for efficient computation
            arr1 = np.array(vec1)
            arr2 = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(arr1, arr2)
            norm1 = np.linalg.norm(arr1)
            norm2 = np.linalg.norm(arr2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    @staticmethod
    def calculate_jaccard_similarity(set1: set, set2: set) -> float:
        """
        Calculate Jaccard similarity between two sets.
        
        Args:
            set1: First set
            set2: Second set
            
        Returns:
            Jaccard similarity score (0.0 to 1.0)
        """
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    @staticmethod
    def generate_semantic_hash(text: str, algorithm: str = "sha256") -> str:
        """
        Generate a semantic hash for text.
        
        Args:
            text: Input text
            algorithm: Hash algorithm to use
            
        Returns:
            Hexadecimal hash string
        """
        try:
            if algorithm == "sha256":
                return hashlib.sha256(text.encode()).hexdigest()
            elif algorithm == "md5":
                return hashlib.md5(text.encode()).hexdigest()
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")
                
        except Exception as e:
            logger.error(f"Failed to generate semantic hash: {e}")
            raise
    
    @staticmethod
    def compress_text(text: str, max_length: int = 500) -> str:
        """
        Compress text to a maximum length.
        
        Args:
            text: Input text
            max_length: Maximum length of compressed text
            
        Returns:
            Compressed text
        """
        if len(text) <= max_length:
            return text
        
        # Simple truncation for demonstration
        # In production, use proper text summarization
        return text[:max_length-3] + "..."
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of keywords
        """
        try:
            # Simple keyword extraction for demonstration
            # In production, use proper NLP libraries
            
            # Remove common stop words and split into words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
                'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
            }
            
            words = text.lower().split()
            keywords = []
            
            for word in words:
                # Remove punctuation and filter out stop words
                word = word.strip('.,!?;:"\'()[]{}')
                if len(word) > 2 and word not in stop_words:
                    keywords.append(word)
            
            # Return unique keywords, limited by max_keywords
            unique_keywords = list(set(keywords))
            return unique_keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            return []
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in seconds to human-readable string.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 1e-6:
            return f"{seconds*1e9:.2f} ns"
        elif seconds < 1e-3:
            return f"{seconds*1e6:.2f} μs"
        elif seconds < 1:
            return f"{seconds*1e3:.2f} ms"
        else:
            return f"{seconds:.2f} s"
    
    @staticmethod
    def format_size(bytes_size: int) -> str:
        """
        Format byte size to human-readable string.
        
        Args:
            bytes_size: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
                bytes_size = float(bytes_size / 1024.0)
            return f"{bytes_size:.2f} PB"
    
    @staticmethod
    def is_expired(created_at: datetime, ttl_seconds: Optional[int] = None) -> bool:
        """
        Check if an entry has expired based on creation time and TTL.
        
        Args:
            created_at: Creation timestamp
            ttl_seconds: Time-to-live in seconds
            
        Returns:
            True if expired, False otherwise
        """
        if ttl_seconds is None:
            return False
        
        expires_at = created_at + timedelta(seconds=ttl_seconds)
        return datetime.utcnow() > expires_at
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """
        Get current memory usage information.
        
        Returns:
            Dictionary with memory usage information
        """
        try:
            import psutil
            process = psutil.Process()
            
            return {
                "rss": process.memory_info().rss,
                "vms": process.memory_info().vms,
                "percent": process.memory_percent(),
                "rss_formatted": CacheUtils.format_size(process.memory_info().rss),
                "vms_formatted": CacheUtils.format_size(process.memory_info().vms)
            }
            
        except ImportError:
            logger.warning("psutil not available, memory usage tracking disabled")
            return {}
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {}
    
    @staticmethod
    async def retry_async(
        func,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Tuple[type[Exception], ...] = (Exception,)
    ) -> Any:
        """
        Retry an async function with exponential backoff.
        
        Args:
            func: Async function to retry
            max_retries: Maximum number of retries
            delay: Initial delay between retries
            backoff: Backoff multiplier
            exceptions: Exceptions to catch and retry on
            
        Returns:
            Result of the function call
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time:.2f}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")
        
        if last_exception is not None:
            raise last_exception
    
    @staticmethod
    @asynccontextmanager
    async def performance_monitor(operation_name: str):
        """
        Context manager for monitoring operation performance.
        
        Args:
            operation_name: Name of the operation being monitored
            
        Yields:
            Performance metrics dictionary
        """
        start_time = time.time()
        metrics = {
            "operation": operation_name,
            "start_time": start_time,
            "success": False
        }
        
        try:
            yield metrics
            metrics["success"] = True
        except Exception as e:
            metrics["error"] = str(e)
            raise
        finally:
            end_time = time.time()
            metrics["duration_ms"] = (end_time - start_time) * 1000
            metrics["timestamp"] = datetime.utcnow()
            
            logger.info(f"Operation '{operation_name}' completed in {metrics['duration_ms']:.2f}ms")
    
    @staticmethod
    def sanitize_key(key: str) -> str:
        """
        Sanitize cache key to ensure it's safe for storage.
        
        Args:
            key: Original key
            
        Returns:
            Sanitized key
        """
        # Remove or replace unsafe characters
        sanitized = key.strip()
        sanitized = sanitized.replace('\x00', '')  # Remove null bytes
        sanitized = ''.join(c for c in sanitized if c.isprintable())
        
        # Limit length
        if len(sanitized) > 250:
            sanitized = sanitized[:250]
        
        return sanitized
    
    @staticmethod
    def merge_metadata(base_metadata: Dict[str, Any], new_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge metadata dictionaries, with new_metadata taking precedence.
        
        Args:
            base_metadata: Base metadata dictionary
            new_metadata: New metadata to merge
            
        Returns:
            Merged metadata dictionary
        """
        merged = base_metadata.copy()
        merged.update(new_metadata)
        return merged
    
    @staticmethod
    def validate_embedding(embedding: List[float], expected_dimension: int = 384) -> bool:
        """
        Validate embedding vector.
        
        Args:
            embedding: Embedding vector to validate
            expected_dimension: Expected dimension of the embedding
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(embedding, list):
            return False
        
        if len(embedding) != expected_dimension:
            return False
        
        for value in embedding:
            if not isinstance(value, (int, float)) or not (-1.0 <= value <= 1.0):
                return False
        
        return True
    
    @staticmethod
    def create_cache_key(prefix: str, *args) -> str:
        """
        Create a standardized cache key from prefix and arguments.
        
        Args:
            prefix: Key prefix
            *args: Arguments to include in key
            
        Returns:
            Cache key string
        """
        key_parts = [prefix]
        
        for arg in args:
            if arg is not None:
                key_parts.append(str(arg))
        
        return ":".join(key_parts)
    
    @staticmethod
    def serialize_for_storage(data: Any) -> str:
        """
        Serialize data for storage in cache.
        
        Args:
            data: Data to serialize
            
        Returns:
            Serialized string
        """
        try:
            if isinstance(data, str):
                return data
            else:
                return json.dumps(data, default=str)
        except Exception as e:
            logger.error(f"Failed to serialize data: {e}")
            raise
    
    @staticmethod
    def deserialize_from_storage(data: str) -> Any:
        """
        Deserialize data from cache storage.
        
        Args:
            data: Serialized data string
            
        Returns:
            Deserialized data
        """
        try:
            # Try to parse as JSON first
            parsed = json.loads(data)
            return parsed
        except json.JSONDecodeError:
            # If not JSON, return as string
            return data
        except Exception as e:
            logger.error(f"Failed to deserialize data: {e}")
            raise