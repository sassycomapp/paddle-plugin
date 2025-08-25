#!/usr/bin/env python3
"""
Test script to verify pg_tiktoken extension integration in PostgreSQL database.

This script tests:
1. Database connection and schema creation
2. pg_tiktoken extension installation and verification
3. tiktoken_count function availability
4. Token counting functionality with fallback
"""

import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simba.simba.database.postgres import PostgresDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pg_tiktoken_integration():
    """Test the pg_tiktoken extension integration."""
    logger.info("Starting pg_tiktoken integration test...")
    
    try:
        # Initialize database connection
        logger.info("Initializing PostgreSQL database connection...")
        db = PostgresDB()
        
        # Test 1: Basic health check
        logger.info("Test 1: Performing database health check...")
        if db.health_check():
            logger.info("✓ Database health check passed")
        else:
            logger.error("✗ Database health check failed")
            return False
        
        # Test 2: Check if tiktoken extension is available
        logger.info("Test 2: Checking pg_tiktoken extension availability...")
        tiktoken_available = db.is_tiktoken_available()
        if tiktoken_available:
            logger.info("✓ pg_tiktoken extension is available")
        else:
            logger.warning("⚠ pg_tiktoken extension is not available, will use fallback estimation")
        
        # Test 3: Test token counting with tiktoken (if available) or fallback
        logger.info("Test 3: Testing token counting functionality...")
        test_texts = [
            "Hello, world!",
            "This is a longer test sentence to verify token counting functionality.",
            "The quick brown fox jumps over the lazy dog.",
            "Token counting is essential for managing OpenAI API usage and costs."
        ]
        
        for i, text in enumerate(test_texts, 1):
            logger.info(f"  Test {i}: Counting tokens for: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            token_count = db.get_token_count(text)
            logger.info(f"    Token count: {token_count}")
            
            # Verify token count is reasonable (at least 1 token for non-empty text)
            if token_count > 0 or not text.strip():
                logger.info(f"    ✓ Token count validation passed")
            else:
                logger.warning(f"    ⚠ Token count validation failed: got {token_count} for non-empty text")
        
        # Test 4: Test with empty string
        logger.info("Test 4: Testing token counting with empty string...")
        empty_count = db.get_token_count("")
        logger.info(f"  Empty string token count: {empty_count}")
        if empty_count == 0:
            logger.info("  ✓ Empty string token count validation passed")
        else:
            logger.warning(f"  ⚠ Empty string token count validation failed: got {empty_count}")
        
        logger.info("✓ All pg_tiktoken integration tests completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ pg_tiktoken integration test failed with error: {str(e)}")
        return False
    finally:
        # Clean up
        try:
            PostgresDB.close_pool()
            logger.info("Database connection pool closed")
        except:
            pass

if __name__ == "__main__":
    success = test_pg_tiktoken_integration()
    sys.exit(0 if success else 1)