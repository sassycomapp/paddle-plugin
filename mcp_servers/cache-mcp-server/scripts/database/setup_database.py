#!/usr/bin/env python3
"""
Database Setup Script for Cache Management System

This script initializes the PostgreSQL database with the required collections
for the cache management system. It creates the database, tables, and indexes
needed for all cache layers.

Author: KiloCode
License: Apache 2.0
"""

import os
import sys
import logging
import asyncio
import asyncpg
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.config import CacheConfig, DatabaseConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseSetupConfig:
    """Configuration for database setup."""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    persist_dir: str = "./cache_storage"
    
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )


class DatabaseSetup:
    """Handles database setup and initialization."""
    
    def __init__(self, config: DatabaseSetupConfig):
        """Initialize database setup."""
        self.config = config
        self.connection = None
        
    async def initialize(self):
        """Initialize database connection and setup."""
        try:
            # Create database connection
            self.connection = await asyncpg.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database="postgres"  # Connect to default database first
            )
            
            logger.info("Database connection established")
            
            # Create database if it doesn't exist
            await self._create_database()
            
            # Connect to the target database
            await self.connection.close()
            self.connection = await asyncpg.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database
            )
            
            # Create extensions
            await self._create_extensions()
            
            # Create tables
            await self._create_tables()
            
            # Create indexes
            await self._create_indexes()
            
            # Create constraints
            await self._create_constraints()
            
            # Create triggers
            await self._create_triggers()
            
            logger.info("Database setup completed successfully")
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
        finally:
            if self.connection:
                await self.connection.close()
    
    async def _create_database(self):
        """Create the database if it doesn't exist."""
        try:
            # Check if database exists
            result = await self.connection.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.config.database
            )
            
            if not result:
                # Create database
                await self.connection.execute(
                    f"CREATE DATABASE {self.config.database}"
                )
                logger.info(f"Database '{self.config.database}' created")
            else:
                logger.info(f"Database '{self.config.database}' already exists")
                
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
    
    async def _create_extensions(self):
        """Create required PostgreSQL extensions."""
        try:
            # Create pgvector extension for vector operations
            await self.connection.execute("CREATE EXTENSION IF NOT EXISTS pgvector")
            logger.info("pgvector extension created")
            
            # Create uuid-ossp extension for UUID generation
            await self.connection.execute("CREATE EXTENSION IF NOT EXISTS uuid-ossp")
            logger.info("uuid-ossp extension created")
            
            # Create btree_gin extension for JSONB indexing
            await self.connection.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")
            logger.info("btree_gin extension created")
            
        except Exception as e:
            logger.error(f"Failed to create extensions: {e}")
            raise
    
    async def _create_tables(self):
        """Create required tables for cache layers."""
        try:
            # Predictive Cache Table
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS predictive_cache (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    key VARCHAR(255) NOT NULL UNIQUE,
                    value JSONB NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP WITH TIME ZONE
                )
            """)
            logger.info("predictive_cache table created")
            
            # Semantic Cache Table
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    key VARCHAR(255) NOT NULL UNIQUE,
                    value JSONB NOT NULL,
                    embedding VECTOR(384),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP WITH TIME ZONE
                )
            """)
            logger.info("semantic_cache table created")
            
            # Vector Cache Table
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS vector_cache (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    key VARCHAR(255) NOT NULL UNIQUE,
                    value JSONB NOT NULL,
                    embedding VECTOR(1536),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP WITH TIME ZONE
                )
            """)
            logger.info("vector_cache table created")
            
            # Vector Diary Table
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS vector_diary (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    session_id VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    embedding VECTOR(1536),
                    context_type VARCHAR(100),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    importance_score FLOAT DEFAULT 0.0,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP WITH TIME ZONE
                )
            """)
            logger.info("vector_diary table created")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def _create_indexes(self):
        """Create indexes for better performance."""
        try:
            # Predictive Cache Indexes
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_predictive_cache_key 
                ON predictive_cache (key)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_predictive_cache_expires_at 
                ON predictive_cache (expires_at)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_predictive_cache_created_at 
                ON predictive_cache (created_at)
            """)
            
            # Semantic Cache Indexes
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_semantic_cache_key 
                ON semantic_cache (key)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_semantic_cache_expires_at 
                ON semantic_cache (expires_at)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_semantic_cache_created_at 
                ON semantic_cache (created_at)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding 
                ON semantic_cache USING hnsw (embedding vector_cosine_ops)
            """)
            
            # Vector Cache Indexes
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_cache_key 
                ON vector_cache (key)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_cache_expires_at 
                ON vector_cache (expires_at)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_cache_created_at 
                ON vector_cache (created_at)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_cache_embedding 
                ON vector_cache USING hnsw (embedding vector_cosine_ops)
            """)
            
            # Vector Diary Indexes
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_diary_session_id 
                ON vector_diary (session_id)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_diary_expires_at 
                ON vector_diary (expires_at)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_diary_created_at 
                ON vector_diary (created_at)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_diary_context_type 
                ON vector_diary (context_type)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_diary_embedding 
                ON vector_diary USING hnsw (embedding vector_cosine_ops)
            """)
            
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_diary_importance_score 
                ON vector_diary (importance_score DESC)
            """)
            
            logger.info("Database indexes created")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    async def _create_constraints(self):
        """Create database constraints."""
        try:
            # Add check constraints
            await self.connection.execute("""
                ALTER TABLE predictive_cache 
                ADD CONSTRAINT chk_access_count_non_negative 
                CHECK (access_count >= 0)
            """)
            
            await self.connection.execute("""
                ALTER TABLE semantic_cache 
                ADD CONSTRAINT chk_access_count_non_negative 
                CHECK (access_count >= 0)
            """)
            
            await self.connection.execute("""
                ALTER TABLE vector_cache 
                ADD CONSTRAINT chk_access_count_non_negative 
                CHECK (access_count >= 0)
            """)
            
            await self.connection.execute("""
                ALTER TABLE vector_diary 
                ADD CONSTRAINT chk_access_count_non_negative 
                CHECK (access_count >= 0)
            """)
            
            await self.connection.execute("""
                ALTER TABLE vector_diary 
                ADD CONSTRAINT chk_importance_score_range 
                CHECK (importance_score >= 0.0 AND importance_score <= 1.0)
            """)
            
            logger.info("Database constraints created")
            
        except Exception as e:
            logger.error(f"Failed to create constraints: {e}")
            raise
    
    async def _create_triggers(self):
        """Create database triggers for automatic maintenance."""
        try:
            # Create function to update last_accessed timestamp
            await self.connection.execute("""
                CREATE OR REPLACE FUNCTION update_last_accessed()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.last_accessed = NOW();
                    NEW.access_count = COALESCE(NEW.access_count, 0) + 1;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Create triggers for cache tables
            for table_name in ["predictive_cache", "semantic_cache", "vector_cache"]:
                await self.connection.execute(f"""
                    CREATE TRIGGER trg_update_{table_name}_accessed
                    AFTER UPDATE ON {table_name}
                    FOR EACH ROW
                    EXECUTE FUNCTION update_last_accessed();
                """)
            
            # Create trigger for vector diary
            await self.connection.execute("""
                CREATE TRIGGER trg_update_vector_diary_accessed
                AFTER UPDATE ON vector_diary
                FOR EACH ROW
                EXECUTE FUNCTION update_last_accessed();
            """)
            
            logger.info("Database triggers created")
            
        except Exception as e:
            logger.error(f"Failed to create triggers: {e}")
            raise
    
    async def verify_setup(self) -> Dict[str, Any]:
        """Verify that the database setup is correct."""
        try:
            verification_results = {
                "tables": {},
                "indexes": {},
                "extensions": {},
                "constraints": {}
            }
            
            # Check tables
            tables = await self.connection.fetch(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            for table in tables:
                table_name = table["table_name"]
                if table_name in ["predictive_cache", "semantic_cache", "vector_cache", "vector_diary"]:
                    verification_results["tables"][table_name] = True
            
            # Check indexes
            indexes = await self.connection.fetch(
                "SELECT indexname FROM pg_indexes WHERE schemaname = 'public'"
            )
            for index in indexes:
                index_name = index["indexname"]
                if any(idx in index_name for idx in ["idx_predictive", "idx_semantic", "idx_vector", "idx_diary"]):
                    verification_results["indexes"][index_name] = True
            
            # Check extensions
            extensions = await self.connection.fetch(
                "SELECT extname FROM pg_extension WHERE extname IN ('pgvector', 'uuid-ossp', 'btree_gin')"
            )
            for extension in extensions:
                ext_name = extension["extname"]
                verification_results["extensions"][ext_name] = True
            
            # Check constraints
            constraints = await self.connection.fetch(
                "SELECT conname FROM pg_constraint WHERE conname LIKE 'chk_%'"
            )
            for constraint in constraints:
                constraint_name = constraint["conname"]
                verification_results["constraints"][constraint_name] = True
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            raise


async def main():
    """Main entry point for database setup."""
    try:
        # Load configuration
        config = CacheConfig()
        db_config = config.database
        
        # Create database setup config
        setup_config = DatabaseSetupConfig(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            username=db_config.username,
            password=db_config.password,
            ssl_mode=db_config.ssl_mode,
            persist_dir=config.data_dir
        )
        
        # Initialize database setup
        db_setup = DatabaseSetup(setup_config)
        
        # Run setup
        await db_setup.initialize()
        
        # Verify setup
        verification = await db_setup.verify_setup()
        
        logger.info("Database setup completed successfully")
        logger.info("Verification results:")
        logger.info(f"Tables: {verification['tables']}")
        logger.info(f"Indexes: {len(verification['indexes'])} created")
        logger.info(f"Extensions: {verification['extensions']}")
        logger.info(f"Constraints: {len(verification['constraints'])} created")
        
        print("\nDatabase setup completed successfully!")
        print("Cache management system is ready to use.")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        print(f"Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())