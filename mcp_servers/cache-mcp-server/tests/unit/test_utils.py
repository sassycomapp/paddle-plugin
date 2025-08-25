"""
Unit tests for Utility Functions.

This module contains comprehensive unit tests for the utility functions,
testing embedding generation, data processing, and helper functions.
"""

import pytest
import asyncio
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from src.core.utils import (
    CacheUtils,
    DataProcessor,
    PerformanceTracker,
    LoggerUtils,
    SecurityUtils,
    ValidationUtils,
    MathUtils,
    TimeUtils,
    FileUtils,
    NetworkUtils,
    generate_embedding,
    cosine_similarity,
    euclidean_distance,
    normalize_vector,
    compress_data,
    decompress_data,
    validate_email,
    validate_url,
    sanitize_input,
    hash_data,
    encrypt_data,
    decrypt_data,
    format_bytes,
    format_duration,
    retry_async,
    rate_limit,
    cache_result,
    benchmark,
    timing_context
)


class TestCacheUtils:
    """Test CacheUtils functionality."""
    
    def test_generate_embedding(self):
        """Test embedding generation."""
        # Mock the embedding model
        with patch('src.core.utils.CacheUtils._get_embedding_model') as mock_model:
            mock_model.return_value = Mock()
            mock_model.return_value.encode.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
            
            embedding = generate_embedding("test text")
            
            assert len(embedding) == 5
            assert all(isinstance(x, float) for x in embedding)
            assert all(-1.0 <= x <= 1.0 for x in embedding)
    
    def test_generate_embedding_batch(self):
        """Test batch embedding generation."""
        texts = ["text1", "text2", "text3"]
        
        with patch('src.core.utils.CacheUtils._get_embedding_model') as mock_model:
            mock_model.return_value = Mock()
            mock_model.return_value.encode.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
            
            embeddings = generate_embedding(texts, batch_size=2)
            
            assert len(embeddings) == 3
            assert all(len(embedding) == 5 for embedding in embeddings)
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        vec3 = [0.0, 0.0, 0.0]
        
        # Identical vectors
        sim = cosine_similarity(vec1, vec2)
        assert sim == 1.0
        
        # Zero vector
        sim = cosine_similarity(vec1, vec3)
        assert sim == 0.0
        
        # Orthogonal vectors
        vec4 = [1.0, 0.0, 0.0]
        vec5 = [0.0, 1.0, 0.0]
        sim = cosine_similarity(vec4, vec5)
        assert sim == 0.0
    
    def test_euclidean_distance(self):
        """Test Euclidean distance calculation."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [3.0, 4.0, 0.0]
        
        distance = euclidean_distance(vec1, vec2)
        assert distance == 5.0  # sqrt(3^2 + 4^2 + 0^2)
    
    def test_normalize_vector(self):
        """Test vector normalization."""
        vec = [3.0, 4.0, 0.0]
        normalized = normalize_vector(vec)
        
        # Should have unit length
        length = sum(x ** 2 for x in normalized) ** 0.5
        assert abs(length - 1.0) < 1e-10
        
        # Should maintain direction
        assert normalized[0] / normalized[1] == 3.0 / 4.0
    
    def test_normalize_zero_vector(self):
        """Test normalization of zero vector."""
        vec = [0.0, 0.0, 0.0]
        normalized = normalize_vector(vec)
        
        # Should return zero vector
        assert all(x == 0.0 for x in normalized)


class TestDataProcessor:
    """Test DataProcessor functionality."""
    
    def test_compress_data(self):
        """Test data compression."""
        original_data = "x" * 1000  # 1KB of data
        
        compressed = compress_data(original_data)
        assert len(compressed) < len(original_data)
        
        # Should be able to decompress
        decompressed = decompress_data(compressed)
        assert decompressed == original_data
    
    def test_compress_decompress_empty(self):
        """Test compression/decompression of empty data."""
        original_data = ""
        
        compressed = compress_data(original_data)
        decompressed = decompress_data(compressed)
        
        assert decompressed == original_data
    
    def test_compress_decompress_large_data(self):
        """Test compression/decompression of large data."""
        original_data = "x" * 1000000  # 1MB of data
        
        compressed = compress_data(original_data)
        assert len(compressed) < len(original_data)
        
        decompressed = decompress_data(compressed)
        assert decompressed == original_data
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        malicious_input = "<script>alert('xss')</script>"
        sanitized = sanitize_input(malicious_input)
        
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
        assert "xss" not in sanitized
    
    def test_sanitize_input_safe(self):
        """Test sanitization of safe input."""
        safe_input = "Hello, World!"
        sanitized = sanitize_input(safe_input)
        
        assert sanitized == safe_input
    
    def test_validate_email(self):
        """Test email validation."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@domain.com"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user..name@domain.com"
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True
        
        for email in invalid_emails:
            assert validate_email(email) is False
    
    def test_validate_url(self):
        """Test URL validation."""
        valid_urls = [
            "http://example.com",
            "https://example.com/path",
            "ftp://example.com",
            "http://localhost:8080"
        ]
        
        invalid_urls = [
            "not-a-url",
            "example.com",
            "http://",
            "://example.com"
        ]
        
        for url in valid_urls:
            assert validate_url(url) is True
        
        for url in invalid_urls:
            assert validate_url(url) is False
    
    def test_hash_data(self):
        """Test data hashing."""
        data = "test data"
        
        hash1 = hash_data(data)
        hash2 = hash_data(data)
        
        # Same data should produce same hash
        assert hash1 == hash2
        
        # Different data should produce different hash
        hash3 = hash_data("different data")
        assert hash1 != hash3
        
        # Hash should be consistent length
        assert len(hash1) == 64  # SHA256 hash length


class TestPerformanceTracker:
    """Test PerformanceTracker functionality."""
    
    def test_timing_context(self):
        """Test timing context manager."""
        with timing_context("test_operation") as timer:
            # Simulate some work
            import time
            time.sleep(0.01)
        
        assert timer.duration > 0
        assert "test_operation" in timer.name
    
    def test_benchmark(self):
        """Test benchmark decorator."""
        @benchmark
        def test_function():
            import time
            time.sleep(0.01)
            return "result"
        
        result, duration = test_function()
        
        assert result == "result"
        assert duration > 0
    
    def test_benchmark_with_args(self):
        """Test benchmark decorator with arguments."""
        @benchmark
        def test_function(arg1, arg2, kwarg1=None):
            return f"{arg1}_{arg2}_{kwarg1}"
        
        result, duration = test_function("hello", "world", kwarg1="test")
        
        assert result == "hello_world_test"
        assert duration > 0
    
    def test_cache_result(self):
        """Test result caching decorator."""
        call_count = 0
        
        @cache_result(ttl=60)
        def cached_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = cached_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call with same args should use cache
        result2 = cached_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment
        
        # Call with different args should execute function
        result3 = cached_function(10)
        assert result3 == 20
        assert call_count == 2
    
    def test_retry_async(self):
        """Test async retry decorator."""
        call_count = 0
        
        @retry_async(max_attempts=3, delay=0.01)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Test error")
            return "success"
        
        # Should succeed after retries
        result = asyncio.run(failing_function())
        assert result == "success"
        assert call_count == 3
    
    def test_retry_async_max_attempts(self):
        """Test async retry decorator with max attempts."""
        call_count = 0
        
        @retry_async(max_attempts=2, delay=0.01)
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Test error")
        
        # Should raise exception after max attempts
        with pytest.raises(Exception):
            asyncio.run(always_failing_function())
        assert call_count == 2
    
    def test_rate_limit(self):
        """Test rate limiting decorator."""
        call_count = 0
        
        @rate_limit(calls_per_second=2)
        def limited_function():
            nonlocal call_count
            call_count += 1
            return call_count
        
        # Should allow calls within rate limit
        result1 = limited_function()
        result2 = limited_function()
        assert result1 == 1
        assert result2 == 2
        
        # Third call should be delayed
        import time
        start_time = time.time()
        result3 = limited_function()
        end_time = time.time()
        
        assert result3 == 3
        assert end_time - start_time >= 0.5  # Should be delayed by at least 0.5 seconds


class TestLoggerUtils:
    """Test LoggerUtils functionality."""
    
    def test_logger_creation(self):
        """Test logger creation."""
        logger = LoggerUtils.get_logger("test_logger")
        
        assert logger.name == "test_logger"
        assert logger.level == 20  # INFO level
    
    def test_logger_with_different_levels(self):
        """Test logger with different levels."""
        logger = LoggerUtils.get_logger("test_logger", level="DEBUG")
        
        assert logger.level == 10  # DEBUG level
        
        logger = LoggerUtils.get_logger("test_logger", level="ERROR")
        assert logger.level == 40  # ERROR level
    
    def test_logger_with_file_output(self):
        """Test logger with file output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            logger = LoggerUtils.get_logger("test_logger", file_path=temp_path)
            
            logger.info("Test message")
            logger.error("Test error")
            
            # Check if file was written
            with open(temp_path, 'r') as f:
                content = f.read()
            
            assert "Test message" in content
            assert "Test error" in content
            
        finally:
            os.unlink(temp_path)


class TestSecurityUtils:
    """Test SecurityUtils functionality."""
    
    def test_encrypt_decrypt_data(self):
        """Test data encryption and decryption."""
        data = "sensitive data"
        password = "test_password"
        
        encrypted = encrypt_data(data, password)
        assert encrypted != data
        
        decrypted = decrypt_data(encrypted, password)
        assert decrypted == data
    
    def test_encrypt_decrypt_wrong_password(self):
        """Test decryption with wrong password."""
        data = "sensitive data"
        password = "correct_password"
        wrong_password = "wrong_password"
        
        encrypted = encrypt_data(data, password)
        
        # Should raise exception with wrong password
        with pytest.raises(Exception):
            decrypt_data(encrypted, wrong_password)
    
    def test_encrypt_decrypt_empty_data(self):
        """Test encryption/decryption of empty data."""
        data = ""
        password = "test_password"
        
        encrypted = encrypt_data(data, password)
        decrypted = decrypt_data(encrypted, password)
        
        assert decrypted == data
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password"
        
        hash1 = SecurityUtils.hash_password(password)
        hash2 = SecurityUtils.hash_password(password)
        
        # Same password should produce different hashes (salted)
        assert hash1 != hash2
        
        # But both should be valid
        assert SecurityUtils.verify_password(password, hash1)
        assert SecurityUtils.verify_password(password, hash2)
    
    def test_verify_password_wrong(self):
        """Test password verification with wrong password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        
        hashed = SecurityUtils.hash_password(password)
        
        assert not SecurityUtils.verify_password(wrong_password, hashed)


class TestValidationUtils:
    """Test ValidationUtils functionality."""
    
    def test_validate_positive_number(self):
        """Test positive number validation."""
        assert ValidationUtils.validate_positive_number(5) is True
        assert ValidationUtils.validate_positive_number(0) is False
        assert ValidationUtils.validate_positive_number(-1) is False
    
    def test_validate_range(self):
        """Test range validation."""
        assert ValidationUtils.validate_range(5, 0, 10) is True
        assert ValidationUtils.validate_range(0, 0, 10) is True
        assert ValidationUtils.validate_range(10, 0, 10) is True
        assert ValidationUtils.validate_range(-1, 0, 10) is False
        assert ValidationUtils.validate_range(11, 0, 10) is False
    
    def test_validate_list_length(self):
        """Test list length validation."""
        assert ValidationUtils.validate_list_length([1, 2, 3], min_length=1, max_length=5) is True
        assert ValidationUtils.validate_list_length([1, 2, 3], min_length=4, max_length=5) is False
        assert ValidationUtils.validate_list_length([1, 2, 3], min_length=1, max_length=2) is False
    
    def test_validate_dict_structure(self):
        """Test dictionary structure validation."""
        schema = {
            "name": str,
            "age": int,
            "email": str
        }
        
        valid_dict = {
            "name": "John",
            "age": 30,
            "email": "john@example.com"
        }
        
        invalid_dict = {
            "name": "John",
            "age": "thirty"  # Wrong type
        }
        
        assert ValidationUtils.validate_dict_structure(valid_dict, schema) is True
        assert ValidationUtils.validate_dict_structure(invalid_dict, schema) is False


class TestMathUtils:
    """Test MathUtils functionality."""
    
    def test_format_bytes(self):
        """Test byte formatting."""
        assert MathUtils.format_bytes(0) == "0 B"
        assert MathUtils.format_bytes(1024) == "1.0 KB"
        assert MathUtils.format_bytes(1024 * 1024) == "1.0 MB"
        assert MathUtils.format_bytes(1024 * 1024 * 1024) == "1.0 GB"
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert MathUtils.format_duration(0) == "0s"
        assert MathUtils.format_duration(30) == "30s"
        assert MathUtils.format_duration(60) == "1m 0s"
        assert MathUtils.format_duration(3661) == "1h 1m 1s"
    
    def test_calculate_percentile(self):
        """Test percentile calculation."""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        assert MathUtils.calculate_percentile(data, 50) == 5.5  # Median
        assert MathUtils.calculate_percentile(data, 90) == 9.1
        assert MathUtils.calculate_percentile(data, 0) == 1
        assert MathUtils.calculate_percentile(data, 100) == 10
    
    def test_calculate_moving_average(self):
        """Test moving average calculation."""
        data = [1, 2, 3, 4, 5]
        window = 3
        
        ma = MathUtils.calculate_moving_average(data, window)
        
        assert len(ma) == len(data) - window + 1
        assert ma[0] == (1 + 2 + 3) / 3  # First window
        assert ma[-1] == (3 + 4 + 5) / 3  # Last window


class TestTimeUtils:
    """Test TimeUtils functionality."""
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        
        formatted = TimeUtils.format_timestamp(timestamp)
        assert "2023-01-01 12:00:00" in formatted
    
    def test_parse_timestamp(self):
        """Test timestamp parsing."""
        timestamp_str = "2023-01-01 12:00:00"
        
        parsed = TimeUtils.parse_timestamp(timestamp_str)
        assert parsed.year == 2023
        assert parsed.month == 1
        assert parsed.day == 1
        assert parsed.hour == 12
        assert parsed.minute == 0
        assert parsed.second == 0
    
    def test_time_ago(self):
        """Test time ago formatting."""
        now = datetime.utcnow()
        past = now - timedelta(minutes=5)
        
        assert "5 minutes ago" in TimeUtils.time_ago(past)
        
        past = now - timedelta(hours=2)
        assert "2 hours ago" in TimeUtils.time_ago(past)
    
    def test_is_expired(self):
        """Test expiration checking."""
        now = datetime.utcnow()
        future_time = now + timedelta(hours=1)
        past_time = now - timedelta(hours=1)
        
        assert TimeUtils.is_expired(past_time, now) is True
        assert TimeUtils.is_expired(future_time, now) is False
    
    def test_get_time_remaining(self):
        """Test time remaining calculation."""
        now = datetime.utcnow()
        future_time = now + timedelta(hours=2, minutes=30)
        
        remaining = TimeUtils.get_time_remaining(future_time, now)
        assert remaining["hours"] == 2
        assert remaining["minutes"] == 30
        assert remaining["seconds"] == 0


class TestFileUtils:
    """Test FileUtils functionality."""
    
    def test_create_directory(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, "new_directory")
            
            FileUtils.create_directory(new_dir)
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)
    
    def test_create_directory_nested(self):
        """Test nested directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = os.path.join(temp_dir, "parent", "child", "grandchild")
            
            FileUtils.create_directory(nested_dir)
            assert os.path.exists(nested_dir)
            assert os.path.isdir(nested_dir)
    
    def test_read_write_file(self):
        """Test file reading and writing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            test_data = "Hello, World!"
            FileUtils.write_file(temp_path, test_data)
            
            read_data = FileUtils.read_file(temp_path)
            assert read_data == test_data
            
        finally:
            os.unlink(temp_path)
    
    def test_file_exists(self):
        """Test file existence checking."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            f.write("test content")
        
        try:
            assert FileUtils.file_exists(temp_path) is True
            assert FileUtils.file_exists("/nonexistent/path") is False
            
        finally:
            os.unlink(temp_path)
    
    def test_get_file_size(self):
        """Test file size retrieval."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            f.write("x" * 1000)  # 1KB
        
        try:
            size = FileUtils.get_file_size(temp_path)
            assert size == 1000
            
        finally:
            os.unlink(temp_path)
    
    def test_delete_file(self):
        """Test file deletion."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            f.write("test content")
        
        FileUtils.delete_file(temp_path)
        assert os.path.exists(temp_path) is False


class TestNetworkUtils:
    """Test NetworkUtils functionality."""
    
    def test_is_port_open(self):
        """Test port checking."""
        # Test with a known open port (http)
        assert NetworkUtils.is_port_open("8.8.8.8", 53) is True  # DNS
        
        # Test with a likely closed port
        assert NetworkUtils.is_port_open("127.0.0.1", 99999) is False
    
    def test_is_url_reachable(self):
        """Test URL reachability."""
        # Test with a known reachable URL
        assert NetworkUtils.is_url_reachable("https://www.google.com") is True
        
        # Test with a likely unreachable URL
        assert NetworkUtils.is_url_reachable("https://nonexistent-domain-12345.com") is False
    
    def test_get_user_agent(self):
        """Test user agent retrieval."""
        ua = NetworkUtils.get_user_agent()
        assert "Mozilla" in ua
        assert "Python" in ua
    
    def test_validate_ip_address(self):
        """Test IP address validation."""
        valid_ips = [
            "127.0.0.1",
            "192.168.1.1",
            "8.8.8.8",
            "0.0.0.0"
        ]
        
        invalid_ips = [
            "256.256.256.256",
            "192.168.1",
            "192.168.1.1.1",
            "not.an.ip"
        ]
        
        for ip in valid_ips:
            assert NetworkUtils.validate_ip_address(ip) is True
        
        for ip in invalid_ips:
            assert NetworkUtils.validate_ip_address(ip) is False


class TestCacheUtilsIntegration:
    """Test CacheUtils integration functionality."""
    
    def test_embedding_similarity_search(self):
        """Test embedding-based similarity search."""
        # Create test embeddings
        embeddings = {
            "doc1": [1.0, 0.0, 0.0],
            "doc2": [0.9, 0.1, 0.0],
            "doc3": [0.0, 1.0, 0.0],
            "doc4": [0.0, 0.0, 1.0]
        }
        
        query_embedding = [0.95, 0.05, 0.0]
        
        # Find most similar documents
        similar = CacheUtils.find_most_similar(query_embedding, embeddings, top_k=2)
        
        assert len(similar) == 2
        assert similar[0]["id"] == "doc1"  # Most similar
        assert similar[1]["id"] == "doc2"  # Second most similar
        assert similar[0]["similarity"] > similar[1]["similarity"]
    
    def test_text_to_embedding_search(self):
        """Test text-to-embedding search."""
        documents = {
            "doc1": "The cat sat on the mat",
            "doc2": "A feline was resting on the rug",
            "doc3": "The dog played in the yard",
            "doc4": "A canine was active in the garden"
        }
        
        query = "cat sitting on mat"
        
        # Mock embedding generation
        with patch('src.core.utils.generate_embedding') as mock_embedding:
            mock_embedding.side_effect = lambda x: [1.0, 0.0, 0.0] if "cat" in x else [0.0, 1.0, 0.0]
            
            similar = CacheUtils.text_similarity_search(query, documents, top_k=2)
            
            assert len(similar) == 2
            assert "doc1" in [doc["id"] for doc in similar]
            assert "doc2" in [doc["id"] for doc in similar]
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        key1 = CacheUtils.generate_cache_key("simple_key")
        key2 = CacheUtils.generate_cache_key("simple_key")
        key3 = CacheUtils.generate_cache_key("different_key")
        
        # Same key should generate same hash
        assert key1 == key2
        
        # Different keys should generate different hashes
        assert key1 != key3
        
        # Hash should be consistent length
        assert len(key1) == 64  # SHA256 hash length
    
    def test_cache_key_with_namespace(self):
        """Test cache key generation with namespace."""
        key1 = CacheUtils.generate_cache_key("simple_key", namespace="user_123")
        key2 = CacheUtils.generate_cache_key("simple_key", namespace="user_456")
        
        # Same key with different namespaces should generate different hashes
        assert key1 != key2
    
    def test_batch_processing(self):
        """Test batch processing functionality."""
        items = [f"item_{i}" for i in range(100)]
        
        # Process in batches of 10
        results = []
        for batch in CacheUtils.batch_process(items, batch_size=10):
            results.extend(batch)
        
        assert len(results) == 100
        assert set(results) == set(items)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])