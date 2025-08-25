#!/usr/bin/env python3
"""
Collection Creation Script for Cache Management System

This script creates the required collections (tables) for the cache management system.
It can be used to create individual collections or all collections at once.

Author: KiloCode
License: Apache 2.0
"""

import os
import sys
import logging
import asyncio
import asyncpg
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CollectionConfig:
    """Configuration for a database collection."""
    name: str
    description: str
    columns: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]


class CollectionManager:
    """Manages database collection creation and management."""
    
    def __init__(self, db_config: Dict[str, Any]):
        """Initialize collection manager."""
        self.db_config = db_config
        self.connection = None
        
    async def connect(self):
        """Connect to the database."""
        try:
            self.connection = await asyncpg.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database=self.db_config["database"]
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the database."""
        if self.connection:
            await self.connection.close()
            self.connection = None
    
    async def create_collection(self, collection_config: CollectionConfig):
        """Create a single collection."""
        try:
            logger.info(f"Creating collection: {collection_config.name}")
            
            # Create table
            column_definitions = []
            for column in collection_config.columns:
                col_def = f"{column['name']} {column['type']}"
                if column.get("primary_key", False):
                    col_def += " PRIMARY KEY"
                if column.get("not_null", False):
                    col_def += " NOT NULL"
                if column.get("unique", False):
                    col_def += " UNIQUE"
                if column.get("default"):
                    col_def += f" DEFAULT {column['default']}"
                column_definitions.append(col_def)
            
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {collection_config.name} (
                    {', '.join(column_definitions)}
                )
            """
            
            await self.connection.execute(create_table_sql)
            logger.info(f"Table {collection_config.name} created successfully")
            
            # Create indexes
            for index in collection_config.indexes:
                index_sql = f"""
                    CREATE INDEX IF NOT EXISTS idx_{collection_config.name}_{index['name']}
                    ON {collection_config.name} ({index['columns']})
                """
                await self.connection.execute(index_sql)
                logger.info(f"Index idx_{collection_config.name}_{index['name']} created")
            
            # Create constraints
            for constraint in collection_config.constraints:
                constraint_sql = f"""
                    ALTER TABLE {collection_config.name}
                    ADD CONSTRAINT {constraint['name']}
                    CHECK ({constraint['condition']})
                """
                await self.connection.execute(constraint_sql)
                logger.info(f"Constraint {constraint['name']} created")
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_config.name}: {e}")
            raise
    
    async def create_all_collections(self):
        """Create all required collections."""
        try:
            # Define collection configurations
            collections = [
                CollectionConfig(
                    name="predictive_cache",
                    description="Predictive cache entries",
                    columns=[
                        {"name": "id", "type": "UUID PRIMARY KEY DEFAULT uuid_generate_v4()", "primary_key": True},
                        {"name": "key", "type": "VARCHAR(255)", "not_null": True, "unique": True},
                        {"name": "value", "type": "JSONB", "not_null": True},
                        {"name": "metadata", "type": "JSONB"},
                        {"name": "created_at", "type": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()", "not_null": True},
                        {"name": "expires_at", "type": "TIMESTAMP WITH TIME ZONE"},
                        {"name": "access_count", "type": "INTEGER DEFAULT 0"},
                        {"name": "last_accessed", "type": "TIMESTAMP WITH TIME ZONE"}
                    ],
                    indexes=[
                        {"name": "key", "columns": "key"},
                        {"name": "expires_at", "columns": "expires_at"},
                        {"name": "created_at", "columns": "created_at"}
                    ],
                    constraints=[
                        {"name": "chk_access_count_non_negative", "condition": "access_count >= 0"}
                    ]
                ),
                CollectionConfig(
                    name="semantic_cache",
                    description="Semantic cache entries",
                    columns=[
                        {"name": "id", "type": "UUID PRIMARY KEY DEFAULT uuid_generate_v4()", "primary_key": True},
                        {"name": "key", "type": "VARCHAR(255)", "not_null": True, "unique": True},
                        {"name": "value", "type": "JSONB", "not_null": True},
                        {"name": "embedding", "type": "VECTOR(384)"},
                        {"name": "metadata", "type": "JSONB"},
                        {"name": "created_at", "type": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()", "not_null": True},
                        {"name": "expires_at", "type": "TIMESTAMP WITH TIME ZONE"},
                        {"name": "access_count", "type": "INTEGER DEFAULT 0"},
                        {"name": "last_accessed", "type": "TIMESTAMP WITH TIME ZONE"}
                    ],
                    indexes=[
                        {"name": "key", "columns": "key"},
                        {"name": "expires_at", "columns": "expires_at"},
                        {"name": "created_at", "columns": "created_at"},
                        {"name": "embedding", "columns": "embedding vector_cosine_ops"}
                    ],
                    constraints=[
                        {"name": "chk_access_count_non_negative", "condition": "access_count >= 0"}
                    ]
                ),
                CollectionConfig(
                    name="vector_cache",
                    description="Vector cache entries",
                    columns=[
                        {"name": "id", "type": "UUID PRIMARY KEY DEFAULT uuid_generate_v4()", "primary_key": True},
                        {"name": "key", "type": "VARCHAR(255)", "not_null": True, "unique": True},
                        {"name": "value", "type": "JSONB", "not_null": True},
                        {"name": "embedding", "type": "VECTOR(1536)"},
                        {"name": "metadata", "type": "JSONB"},
                        {"name": "created_at", "type": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()", "not_null": True},
                        {"name": "expires_at", "type": "TIMESTAMP WITH TIME ZONE"},
                        {"name": "access_count", "type": "INTEGER DEFAULT 0"},
                        {"name": "last_accessed", "type": "TIMESTAMP WITH TIME ZONE"}
                    ],
                    indexes=[
                        {"name": "key", "columns": "key"},
                        {"name": "expires_at", "columns": "expires_at"},
                        {"name": "created_at", "columns": "created_at"},
                        {"name": "embedding", "columns": "embedding vector_cosine_ops"}
                    ],
                    constraints=[
                        {"name": "chk_access_count_non_negative", "condition": "access_count >= 0"}
                    ]
                ),
                CollectionConfig(
                    name="vector_diary",
                    description="Vector diary entries",
                    columns=[
                        {"name": "id", "type": "UUID PRIMARY KEY DEFAULT uuid_generate_v4()", "primary_key": True},
                        {"name": "session_id", "type": "VARCHAR(255)", "not_null": True},
                        {"name": "content", "type": "TEXT", "not_null": True},
                        {"name": "embedding", "type": "VECTOR(1536)"},
                        {"name": "context_type", "type": "VARCHAR(100)"},
                        {"name": "metadata", "type": "JSONB"},
                        {"name": "created_at", "type": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()", "not_null": True},
                        {"name": "expires_at", "type": "TIMESTAMP WITH TIME ZONE"},
                        {"name": "importance_score", "type": "FLOAT DEFAULT 0.0"},
                        {"name": "access_count", "type": "INTEGER DEFAULT 0"},
                        {"name": "last_accessed", "type": "TIMESTAMP WITH TIME ZONE"}
                    ],
                    indexes=[
                        {"name": "session_id", "columns": "session_id"},
                        {"name": "expires_at", "columns": "expires_at"},
                        {"name": "created_at", "columns": "created_at"},
                        {"name": "context_type", "columns": "context_type"},
                        {"name": "embedding", "columns": "embedding vector_cosine_ops"},
                        {"name": "importance_score", "columns": "importance_score DESC"}
                    ],
                    constraints=[
                        {"name": "chk_access_count_non_negative", "condition": "access_count >= 0"},
                        {"name": "chk_importance_score_range", "condition": "importance_score >= 0.0 AND importance_score <= 1.0"}
                    ]
                )
            ]
            
            # Create each collection
            for collection in collections:
                await self.create_collection(collection)
            
            logger.info("All collections created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create collections: {e}")
            raise
    
    async def verify_collections(self) -> Dict[str, Any]:
        """Verify that all collections exist and are properly configured."""
        try:
            verification_results = {
                "collections": {},
                "indexes": {},
                "constraints": {}
            }
            
            # Check collections
            collections = await self.connection.fetch(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            
            for collection in collections:
                collection_name = collection["table_name"]
                if collection_name in ["predictive_cache", "semantic_cache", "vector_cache", "vector_diary"]:
                    verification_results["collections"][collection_name] = True
            
            # Check indexes
            indexes = await self.connection.fetch(
                "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public'"
            )
            
            for index in indexes:
                index_name = index["indexname"]
                if any(idx in index_name for idx in ["idx_predictive", "idx_semantic", "idx_vector", "idx_diary"]):
                    verification_results["indexes"][index_name] = True
            
            # Check constraints
            constraints = await self.connection.fetch(
                "SELECT conname, consrc FROM pg_constraint WHERE conname LIKE 'chk_%'"
            )
            
            for constraint in constraints:
                constraint_name = constraint["conname"]
                verification_results["constraints"][constraint_name] = True
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Collection verification failed: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections."""
        try:
            stats = {}
            
            collections = ["predictive_cache", "semantic_cache", "vector_cache", "vector_diary"]
            
            for collection in collections:
                collection_stats = await self.connection.fetchrow(
                    f"""
                    SELECT 
                        COUNT(*) as total_entries,
                        COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
                        COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries,
                        AVG(access_count) as avg_access_count,
                        MAX(last_accessed) as last_accessed
                    FROM {collection}
                    """
                )
                
                stats[collection] = {
                    "total_entries": collection_stats["total_entries"],
                    "expired_entries": collection_stats["expired_entries"],
                    "active_entries": collection_stats["active_entries"],
                    "avg_access_count": collection_stats["avg_access_count"],
                    "last_accessed": collection_stats["last_accessed"]
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise


async def main():
    """Main entry point for collection creation."""
    try:
        # Database configuration
        db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "paddle_plugin_cache",
            "user": "postgres",
            "password": "2001"
        }
        
        # Initialize collection manager
        collection_manager = CollectionManager(db_config)
        
        # Connect to database
        await collection_manager.connect()
        
        # Create all collections
        await collection_manager.create_all_collections()
        
        # Verify collections
        verification = await collection_manager.verify_collections()
        
        # Get collection statistics
        stats = await collection_manager.get_collection_stats()
        
        logger.info("Collection creation completed successfully")
        logger.info("Verification results:")
        logger.info(f"Collections: {verification['collections']}")
        logger.info(f"Indexes: {len(verification['indexes'])} created")
        logger.info(f"Constraints: {len(verification['constraints'])} created")
        
        logger.info("Collection statistics:")
        for collection, stat in stats.items():
            logger.info(f"{collection}: {stat}")
        
        print("\nCollection creation completed successfully!")
        print("Cache management system collections are ready to use.")
        
    except Exception as e:
        logger.error(f"Collection creation failed: {e}")
        print(f"Collection creation failed: {e}")
        sys.exit(1)
    finally:
        if collection_manager:
            await collection_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())