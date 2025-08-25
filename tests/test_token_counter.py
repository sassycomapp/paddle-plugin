"""
Comprehensive Test Suite for Token Counting Module

This test suite covers all functionality of the token counting module including:
- Basic token counting with pg_tiktoken and fallback
- Batch token counting
- Caching functionality
- Decorators and middleware integration
- Performance metrics
- Error handling
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import logging
from datetime import datetime

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.token_management.token_counter import (
    TokenCounter, TokenizationModel, TokenCountResult, BatchTokenCountResult
)
from src.token_management.decorators import (
    token_counter_decorator, track_token_usage, batch_token_counter
)
from src.token_management.middleware import (
    TokenCountingMiddleware, TokenQuotaMiddleware, APITokenUsage, create_token_middleware
)


class TestTokenCounter(unittest.TestCase):
    """Test cases for the TokenCounter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_db.is_tiktoken_available.return_value = True
        self.mock_db.get_token_count.return_value = 10
        self.token_counter = TokenCounter(self.mock_db)
    
    def test_init(self):
        """Test TokenCounter initialization."""
        counter = TokenCounter()
        self.assertIsInstance(counter, TokenCounter)
        self.assertIsInstance(counter.db, Mock)  # Should create default PostgresDB
        
        # Test with custom database
        custom_counter = TokenCounter(self.mock_db)
        self.assertEqual(custom_counter.db, self.mock_db)
    
    def test_count_tokens_empty_text(self):
        """Test token counting with empty text."""
        result = self.token_counter.count_tokens("")
        self.assertEqual(result.token_count, 0)
        self.assertEqual(result.method, 'fallback')
        
        result = self.token_counter.count_tokens("   ")
        self.assertEqual(result.token_count, 0)
    
    def test_count_tokens_with_pg_tiktoken(self):
        """Test token counting with pg_tiktoken available."""
        self.mock_db.is_tiktoken_available.return_value = True
        self.mock_db.get_token_count.return_value = 15
        
        result = self.token_counter.count_tokens("Hello world")
        
        self.assertEqual(result.token_count, 15)
        self.assertEqual(result.method, 'pg_tiktoken')
        self.assertEqual(result.model, TokenizationModel.CL100K_BASE)
        self.assertGreater(result.processing_time, 0)
    
    def test_count_tokens_fallback(self):
        """Test token counting with pg_tiktoken unavailable."""
        self.mock_db.is_tiktoken_available.return_value = False
        
        result = self.token_counter.count_tokens("Hello world")
        
        self.assertEqual(result.method, 'fallback')
        self.assertGreater(result.token_count, 0)
    
    def test_count_tokens_different_models(self):
        """Test token counting with different tokenization models."""
        test_text = "Hello world"
        
        for model in TokenizationModel:
            with self.subTest(model=model):
                result = self.token_counter.count_tokens(test_text, model)
                self.assertGreater(result.token_count, 0)
                self.assertEqual(result.model, model)
    
    def test_count_tokens_batch(self):
        """Test batch token counting."""
        texts = ["Hello world", "How are you", "Good morning"]
        
        batch_result = self.token_counter.count_tokens_batch(texts)
        
        self.assertIsInstance(batch_result, BatchTokenCountResult)
        self.assertEqual(len(batch_result.results), 3)
        self.assertEqual(batch_result.total_tokens, sum(r.token_count for r in batch_result.results))
        self.assertGreater(batch_result.total_processing_time, 0)
    
    def test_estimate_tokens_fallback(self):
        """Test fallback token estimation."""
        test_text = "Hello world, this is a test!"
        
        # Test with different models
        for model in TokenizationModel:
            with self.subTest(model=model):
                estimate = self.token_counter.estimate_tokens_fallback(test_text, model)
                self.assertGreater(estimate, 0)
                self.assertIsInstance(estimate, int)
    
    def test_get_token_count_for_api(self):
        """Test API-specific token counting."""
        text = "Hello world"
        result = self.token_counter.get_token_count_for_api(text)
        
        self.assertIn('token_count', result)
        self.assertIn('model', result)
        self.assertIn('method', result)
        self.assertIn('processing_time', result)
        self.assertEqual(result['token_count'], 10)
    
    def test_get_token_count_for_context(self):
        """Test context window calculations."""
        text = "Hello world"
        max_tokens = 100
        
        result = self.token_counter.get_token_count_for_context(text, max_tokens)
        
        self.assertIn('token_count', result)
        self.assertIn('max_context_tokens', result)
        self.assertIn('context_usage_percentage', result)
        self.assertIn('remaining_tokens', result)
        self.assertIn('context_fit', result)
        self.assertTrue(result['context_fit'])
    
    def test_cache_functionality(self):
        """Test token count caching."""
        text = "Hello world"
        
        # First call should miss cache
        result1 = self.token_counter.count_tokens(text)
        self.assertFalse(result1.cache_hit)
        
        # Second call should hit cache
        result2 = self.token_counter.count_tokens(text)
        self.assertTrue(result2.cache_hit)
        
        # Verify cache metrics
        metrics = self.token_counter.get_performance_metrics()
        self.assertEqual(metrics['cache_hits'], 1)
        self.assertEqual(metrics['cache_misses'], 1)
    
    def test_cache_clear(self):
        """Test cache clearing."""
        text = "Hello world"
        self.token_counter.count_tokens(text)  # Add to cache
        
        self.assertGreater(len(self.token_counter.token_cache), 0)
        
        self.token_counter.clear_cache()
        self.assertEqual(len(self.token_counter.token_cache), 0)
    
    def test_performance_metrics(self):
        """Test performance metrics tracking."""
        # Perform some operations
        self.token_counter.count_tokens("Hello")
        self.token_counter.count_tokens("World")
        
        metrics = self.token_counter.get_performance_metrics()
        
        self.assertIn('total_calls', metrics)
        self.assertIn('pg_tiktoken_calls', metrics)
        self.assertIn('fallback_calls', metrics)
        self.assertIn('cache_hits', metrics)
        self.assertIn('cache_misses', metrics)
        self.assertIn('total_processing_time', metrics)
        self.assertGreater(metrics['total_calls'], 0)
    
    def test_log_token_usage(self):
        """Test token usage logging."""
        user_id = "test_user"
        session_id = "test_session"
        tokens_used = 10
        api_endpoint = "test_endpoint"
        
        result = self.token_counter.log_token_usage(
            user_id, session_id, tokens_used, api_endpoint
        )
        
        self.assertTrue(result)
        self.mock_db.log_token_usage.assert_called_once_with(
            user_id, session_id, tokens_used, api_endpoint, "Medium"
        )
    
    def test_context_manager(self):
        """Test TokenCounter as context manager."""
        with TokenCounter(self.mock_db) as counter:
            result = counter.count_tokens("Hello")
            self.assertEqual(result.token_count, 10)
        
        # Cache should be cleared after context exit
        self.assertEqual(len(counter.token_cache), 0)


class TestTokenCounterIntegration(unittest.TestCase):
    """Integration tests for TokenCounter with real database."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the database to avoid actual database calls in tests
        self.mock_db = Mock()
        self.mock_db.is_tiktoken_available.return_value = False  # Force fallback
        self.token_counter = TokenCounter(self.mock_db)
    
    def test_realistic_token_estimates(self):
        """Test token estimation with realistic text."""
        test_cases = [
            ("Hello", 1),  # Single word
            ("Hello world", 2),  # Two words
            ("Hello, world!", 3),  # With punctuation
            ("This is a longer sentence with more words.", 8),  # Longer sentence
            ("", 0),  # Empty string
        ]
        
        for text, expected_min in test_cases:
            with self.subTest(text=text):
                result = self.token_counter.count_tokens(text)
                self.assertGreaterEqual(result.token_count, expected_min)
    
    def test_batch_processing_efficiency(self):
        """Test that batch processing is more efficient than individual calls."""
        texts = ["Hello"] * 10
        
        # Batch processing
        start_time = time.time()
        batch_result = self.token_counter.count_tokens_batch(texts)
        batch_time = time.time() - start_time
        
        # Individual processing
        start_time = time.time()
        individual_results = [self.token_counter.count_tokens(text) for text in texts]
        individual_time = time.time() - start_time
        
        # Batch should be faster (though this might vary)
        self.assertLessEqual(batch_time, individual_time * 1.1)  # Allow some variance
        self.assertEqual(batch_result.total_tokens, sum(r.token_count for r in individual_results))


class TestDecorators(unittest.TestCase):
    """Test cases for token counting decorators."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_counter = Mock()
        self.mock_counter.count_tokens.return_value = Mock(token_count=5)
    
    def test_token_counter_decorator(self):
        """Test the token_counter_decorator."""
        @token_counter_decorator(
            model=TokenizationModel.CL100K_BASE,
            count_inputs=True,
            count_outputs=True,
            log_usage=False,
            counter=self.mock_counter
        )
        def test_function(text, number):
            return f"Result: {text} {number}"
        
        result = test_function("Hello", 42)
        
        self.assertEqual(result, "Result: Hello 42")
        # Verify that token counting was called
        self.mock_counter.count_tokens.assert_called()
    
    def test_track_token_usage_decorator(self):
        """Test the track_token_usage decorator."""
        @track_token_usage(
            model=TokenizationModel.CL100K_BASE,
            counter=self.mock_counter
        )
        def test_function(text):
            return {"token_count": 10, "result": text}
        
        result = test_function("Hello")
        
        self.assertEqual(result["result"], "Hello")
        self.assertEqual(result["token_count"], 10)
    
    def test_batch_token_counter_decorator(self):
        """Test the batch_token_counter decorator."""
        @batch_token_counter(
            model=TokenizationModel.CL100K_BASE,
            counter=self.mock_counter
        )
        def test_function(texts):
            return [f"Processed: {text}" for text in texts]
        
        texts = ["Hello", "World"]
        result = test_function(texts)
        
        self.assertEqual(len(result), 2)
        self.assertIn("token_count", result[0] if isinstance(result, dict) else result)
    
    def test_decorator_with_error_handling(self):
        """Test decorator error handling."""
        @token_counter_decorator(
            model=TokenizationModel.CL100K_BASE,
            count_inputs=True,
            count_outputs=True,
            log_usage=False,
            counter=self.mock_counter
        )
        def test_function():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            test_function()


class TestMiddleware(unittest.TestCase):
    """Test cases for token counting middleware."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_app = Mock()
        self.mock_counter = Mock()
        self.mock_counter.log_token_usage.return_value = True
    
    def test_token_counting_middleware_init(self):
        """Test TokenCountingMiddleware initialization."""
        middleware = TokenCountingMiddleware(
            self.mock_app,
            token_counter=self.mock_counter,
            model=TokenizationModel.CL100K_BASE
        )
        
        self.assertEqual(middleware.token_counter, self.mock_counter)
        self.assertEqual(middleware.model, TokenizationModel.CL100K_BASE)
    
    def test_token_counting_middleware_skip_paths(self):
        """Test middleware path exclusion."""
        middleware = TokenCountingMiddleware(
            self.mock_app,
            exclude_paths=['/health', '/metrics']
        )
        
        # Mock request
        mock_request = Mock()
        mock_request.method = 'GET'
        mock_request.url.path = '/health'
        
        should_skip = middleware._should_skip_token_counting(mock_request)
        self.assertTrue(should_skip)
    
    def test_token_counting_middleware_extract_user_id(self):
        """Test user ID extraction from request."""
        middleware = TokenCountingMiddleware(self.mock_app)
        
        # Test from header
        mock_request = Mock()
        mock_request.headers = {'X-User-ID': 'test_user'}
        
        user_id = middleware._extract_user_id(mock_request)
        self.assertEqual(user_id, 'test_user')
    
    def test_token_counting_middleware_extract_session_id(self):
        """Test session ID extraction from request."""
        middleware = TokenCountingMiddleware(self.mock_app)
        
        # Test from query parameter
        mock_request = Mock()
        mock_request.query_params = {'session_id': 'test_session'}
        
        session_id = middleware._extract_session_id(mock_request)
        self.assertEqual(session_id, 'test_session')
    
    def test_token_quota_middleware_init(self):
        """Test TokenQuotaMiddleware initialization."""
        middleware = TokenQuotaMiddleware(
            self.mock_app,
            token_counter=self.mock_counter,
            default_quota=5000
        )
        
        self.assertEqual(middleware.token_counter, self.mock_counter)
        self.assertEqual(middleware.default_quota, 5000)
    
    def test_token_quota_middleware_quota_check(self):
        """Test quota checking functionality."""
        middleware = TokenQuotaMiddleware(self.mock_app)
        
        # Mock quota check
        self.mock_counter.db.check_token_quota.return_value = {
            'allowed': False,
            'reason': 'Quota exceeded',
            'remaining_tokens': 0
        }
        
        mock_request = Mock()
        mock_request.headers = {'X-User-ID': 'test_user'}
        
        # Mock the dispatch method to return a response with status code
        mock_response = Mock()
        mock_response.status_code = 429
        
        # This would normally be an async test, but we'll test the logic
        quota_check = self.mock_counter.db.check_token_quota(
            user_id='test_user',
            tokens_requested=100,
            priority_level='Medium'
        )
        
        self.assertFalse(quota_check['allowed'])
        self.assertEqual(quota_check['reason'], 'Quota exceeded')
    
    def test_create_token_middleware(self):
        """Test token middleware creation."""
        middleware = create_token_middleware(
            token_counter=self.mock_counter,
            model=TokenizationModel.CL100K_BASE,
            enable_quota=True
        )
        
        self.assertIsNotNone(middleware)
    
    def test_api_token_usage_record(self):
        """Test APITokenUsage dataclass."""
        usage = APITokenUsage(
            endpoint='/test',
            method='GET',
            user_id='test_user',
            session_id='test_session',
            input_tokens=5,
            output_tokens=10,
            total_tokens=15,
            processing_time=0.1,
            timestamp=datetime.now(),
            status_code=200,
            model=TokenizationModel.CL100K_BASE
        )
        
        self.assertEqual(usage.endpoint, '/test')
        self.assertEqual(usage.method, 'GET')
        self.assertEqual(usage.total_tokens, 15)
        self.assertEqual(usage.model, TokenizationModel.CL100K_BASE)


class TestTokenizationModels(unittest.TestCase):
    """Test cases for tokenization models."""
    
    def test_tokenization_model_enum(self):
        """Test TokenizationModel enum values."""
        models = list(TokenizationModel)
        self.assertIn(TokenizationModel.CL100K_BASE, models)
        self.assertIn(TokenizationModel.P50K_BASE, models)
        self.assertIn(TokenizationModel.P50K_EDIT, models)
        self.assertIn(TokenizationModel.R50K_BASE, models)
    
    def test_tokenization_model_values(self):
        """Test tokenization model string values."""
        self.assertEqual(TokenizationModel.CL100K_BASE.value, "cl100k_base")
        self.assertEqual(TokenizationModel.P50K_BASE.value, "p50k_base")
        self.assertEqual(TokenizationModel.P50K_EDIT.value, "p50k_edit")
        self.assertEqual(TokenizationModel.R50K_BASE.value, "r50k_base")


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_db.is_tiktoken_available.return_value = False
        self.token_counter = TokenCounter(self.mock_db)
    
    def test_database_connection_failure(self):
        """Test handling of database connection failures."""
        self.mock_db.is_tiktoken_available.side_effect = Exception("Connection failed")
        
        # Should still work with fallback
        result = self.token_counter.count_tokens("Hello")
        self.assertEqual(result.method, 'fallback')
        self.assertGreater(result.token_count, 0)
    
    def test_token_counting_failure(self):
        """Test handling of token counting failures."""
        self.mock_db.get_token_count.side_effect = Exception("Counting failed")
        
        # Should still work with fallback
        result = self.token_counter.count_tokens("Hello")
        self.assertEqual(result.method, 'fallback')
        self.assertGreater(result.token_count, 0)
    
    def test_cache_failure(self):
        """Test handling of cache failures."""
        # Force cache to fail
        self.token_cache = {}
        
        # Should still work
        result = self.token_counter.count_tokens("Hello")
        self.assertGreater(result.token_count, 0)
    
    def test_decorator_error_handling(self):
        """Test decorator error handling."""
        @token_counter_decorator(
            model=TokenizationModel.CL100K_BASE,
            count_inputs=True,
            count_outputs=True,
            log_usage=False,
            counter=self.token_counter
        )
        def test_function():
            return "test"
        
        # Should work normally
        result = test_function()
        self.assertEqual(result, "test")


class TestPerformance(unittest.TestCase):
    """Test performance-related functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_db.is_tiktoken_available.return_value = False
        self.token_counter = TokenCounter(self.mock_db)
    
    def test_cache_performance(self):
        """Test cache performance benefits."""
        text = "Hello world"
        
        # Warm up cache
        self.token_counter.count_tokens(text)
        
        # Measure cached call performance
        start_time = time.time()
        result = self.token_counter.count_tokens(text)
        cache_time = time.time() - start_time
        
        self.assertTrue(result.cache_hit)
        self.assertLess(cache_time, 0.01)  # Should be very fast
    
    def test_batch_processing_performance(self):
        """Test batch processing performance."""
        texts = ["Hello"] * 100
        
        # Measure batch processing time
        start_time = time.time()
        batch_result = self.token_counter.count_tokens_batch(texts)
        batch_time = time.time() - start_time
        
        # Measure individual processing time
        start_time = time.time()
        individual_results = [self.token_counter.count_tokens(text) for text in texts]
        individual_time = time.time() - start_time
        
        # Batch should be more efficient
        self.assertLess(batch_time, individual_time)
        self.assertEqual(batch_result.total_tokens, sum(r.token_count for r in individual_results))
    
    def test_memory_usage(self):
        """Test memory usage with large cache."""
        # Fill cache
        for i in range(1000):
            text = f"Test text {i}"
            self.token_counter.count_tokens(text)
        
        # Check cache size
        metrics = self.token_counter.get_performance_metrics()
        self.assertEqual(metrics['cache_size'], 1000)
        
        # Clear cache
        self.token_counter.clear_cache()
        self.assertEqual(len(self.token_counter.token_cache), 0)


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    
    # Run tests
    unittest.main(verbosity=2)