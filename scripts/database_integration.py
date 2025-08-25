#!/usr/bin/env python3
"""
Database Integration Script

This script handles PostgreSQL database setup, connection pooling, 
backup procedures, and health checks for the cache system.

Author: KiloCode
License: Apache 2.0
"""

import asyncio
import logging
import os
import sys
import time
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import psycopg2
from psycopg2 import pool, sql, errors
from psycopg2.extras import RealDictCursor
import psycopg2.pool
from contextlib import contextmanager
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseIntegration:
    """Handles PostgreSQL database integration for cache system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection_pool = None
        self.health_check_interval = 60  # seconds
        self.backup_interval = 86400  # 24 hours
        self.max_retries = 3
        self.retry_delay = 5
        
        # Database configuration
        self.db_host = config.get('host', 'localhost')
        self.db_port = config.get('port', 5432)
        self.db_name = config.get('name', 'paddle_plugin_cache')
        self.db_user = config.get('user', 'postgres')
        self.db_password = config.get('password', '2001')
        self.persist_dir = config.get('persist_dir', './cache_storage')
        
        # Connection pool configuration
        self.pool_config = config.get('connection_pool', {
            'max_size': 20,
            'min_size': 5,
            'timeout': 30
        })
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize the database and connection pool."""
        try:
            # Create connection pool
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.pool_config['min_size'],
                maxconn=self.pool_config['max_size'],
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                connect_timeout=self.pool_config['timeout']
            )
            
            logger.info(f"Connection pool created with {self.pool_config['min_size']}-{self.pool_config['max_size']} connections")
            
            # Create tables if they don't exist
            self._create_tables()
            
            # Start background tasks
            self._start_background_tasks()
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_tables(self):
        """Create database tables for cache storage."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create cache tables for each layer
                    tables = {
                        'predictive_cache': '''
                            CREATE TABLE IF NOT EXISTS predictive_cache (
                                id SERIAL PRIMARY KEY,
                                key VARCHAR(255) UNIQUE NOT NULL,
                                value JSONB NOT NULL,
                                metadata JSONB,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                expires_at TIMESTAMP,
                                access_count INTEGER DEFAULT 0,
                                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''',
                        'semantic_cache': '''
                            CREATE TABLE IF NOT EXISTS semantic_cache (
                                id SERIAL PRIMARY KEY,
                                key VARCHAR(255) UNIQUE NOT NULL,
                                value JSONB NOT NULL,
                                metadata JSONB,
                                embedding VECTOR(384),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                expires_at TIMESTAMP,
                                access_count INTEGER DEFAULT 0,
                                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''',
                        'vector_cache': '''
                            CREATE TABLE IF NOT EXISTS vector_cache (
                                id SERIAL PRIMARY KEY,
                                key VARCHAR(255) UNIQUE NOT NULL,
                                value JSONB NOT NULL,
                                metadata JSONB,
                                embedding VECTOR(1536),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                expires_at TIMESTAMP,
                                access_count INTEGER DEFAULT 0,
                                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''',
                        'global_cache': '''
                            CREATE TABLE IF NOT EXISTS global_cache (
                                id SERIAL PRIMARY KEY,
                                key VARCHAR(255) UNIQUE NOT NULL,
                                value JSONB NOT NULL,
                                metadata JSONB,
                                knowledge_base_id VARCHAR(100),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                expires_at TIMESTAMP,
                                access_count INTEGER DEFAULT 0,
                                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''',
                        'vector_diary': '''
                            CREATE TABLE IF NOT EXISTS vector_diary (
                                id SERIAL PRIMARY KEY,
                                key VARCHAR(255) UNIQUE NOT NULL,
                                value JSONB NOT NULL,
                                metadata JSONB,
                                session_id VARCHAR(100),
                                context VECTOR(768),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                expires_at TIMESTAMP,
                                access_count INTEGER DEFAULT 0,
                                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''',
                        'cache_stats': '''
                            CREATE TABLE IF NOT EXISTS cache_stats (
                                id SERIAL PRIMARY KEY,
                                cache_layer VARCHAR(50) NOT NULL,
                                operation VARCHAR(20) NOT NULL,
                                key VARCHAR(255),
                                success BOOLEAN DEFAULT true,
                                execution_time_ms INTEGER,
                                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''',
                        'sync_metadata': '''
                            CREATE TABLE IF NOT EXISTS sync_metadata (
                                id SERIAL PRIMARY KEY,
                                source_type VARCHAR(50) NOT NULL,
                                source_id VARCHAR(255) NOT NULL,
                                cache_key VARCHAR(255) UNIQUE NOT NULL,
                                last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                sync_status VARCHAR(20) DEFAULT 'pending',
                                conflict_resolution TEXT,
                                data_hash VARCHAR(64),
                                UNIQUE(source_type, source_id)
                            )
                        '''
                    }
                    
                    for table_name, table_sql in tables.items():
                        try:
                            cursor.execute(table_sql)
                            logger.info(f"Table '{table_name}' created/verified")
                        except Exception as e:
                            logger.warning(f"Could not create table '{table_name}': {e}")
                    
                    # Create indexes for performance
                    indexes = [
                        'CREATE INDEX IF NOT EXISTS idx_cache_expires ON predictive_cache(expires_at)',
                        'CREATE INDEX IF NOT EXISTS idx_cache_expires ON semantic_cache(expires_at)',
                        'CREATE INDEX IF NOT EXISTS idx_cache_expires ON vector_cache(expires_at)',
                        'CREATE INDEX IF NOT EXISTS idx_cache_expires ON global_cache(expires_at)',
                        'CREATE INDEX IF NOT EXISTS idx_cache_expires ON vector_diary(expires_at)',
                        'CREATE INDEX IF NOT EXISTS idx_cache_access ON predictive_cache(last_accessed)',
                        'CREATE INDEX IF NOT EXISTS idx_cache_access ON semantic_cache(last_accessed)',
                        'CREATE INDEX IF NOT EXISTS idx_cache_access ON vector_cache(last_accessed)',
                        'CREATE INDEX IF NOT EXISTS idx_cache_access ON global_cache(last_accessed)',
                        'CREATE INDEX IF NOT EXISTS idx_cache_access ON vector_diary(last_accessed)',
                        'CREATE INDEX IF NOT EXISTS idx_stats_timestamp ON cache_stats(timestamp)',
                        'CREATE INDEX IF NOT EXISTS idx_sync_source ON sync_metadata(source_type, source_id)',
                        'CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_metadata(sync_status)'
                    ]
                    
                    for index_sql in indexes:
                        try:
                            cursor.execute(index_sql)
                            logger.info("Index created/verified")
                        except Exception as e:
                            logger.warning(f"Could not create index: {e}")
                    
                    conn.commit()
                    logger.info("Database tables and indexes created successfully")
                    
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except Exception as e:
            logger.error(f"Error getting database connection: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    async def execute_query(self, query: str, params: Tuple = None, fetch: bool = True) -> Any:
        """Execute a database query asynchronously."""
        loop = asyncio.get_event_loop()
        
        def _execute():
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params or ())
                    if fetch:
                        return cursor.fetchall()
                    conn.commit()
                    return None
        
        try:
            result = await loop.run_in_executor(None, _execute)
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def get_cache_value(self, key: str, layer: str) -> Optional[Dict[str, Any]]:
        """Get a value from cache."""
        query = f'''
            SELECT key, value, metadata, created_at, expires_at, access_count, last_accessed
            FROM {layer}_cache
            WHERE key = %s AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        '''
        
        try:
            result = await self.execute_query(query, (key,))
            if result:
                # Update access count and last accessed time
                await self._update_access_stats(key, layer)
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get cache value: {e}")
            raise
    
    async def set_cache_value(self, key: str, value: Dict[str, Any], layer: str, 
                            ttl: int = None, metadata: Dict[str, Any] = None) -> bool:
        """Set a value in cache."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
        
        query = f'''
            INSERT INTO {layer}_cache (key, value, metadata, expires_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                metadata = EXCLUDED.metadata,
                expires_at = EXCLUDED.expires_at,
                last_accessed = CURRENT_TIMESTAMP
        '''
        
        try:
            await self.execute_query(query, (key, json.dumps(value), json.dumps(metadata or {}), expires_at), fetch=False)
            await self._log_cache_operation('set', key, layer, True)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache value: {e}")
            await self._log_cache_operation('set', key, layer, False, str(e))
            return False
    
    async def delete_cache_value(self, key: str, layer: str) -> bool:
        """Delete a value from cache."""
        query = f'DELETE FROM {layer}_cache WHERE key = %s'
        
        try:
            await self.execute_query(query, (key,), fetch=False)
            await self._log_cache_operation('delete', key, layer, True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache value: {e}")
            await self._log_cache_operation('delete', key, layer, False, str(e))
            return False
    
    async def _update_access_stats(self, key: str, layer: str):
        """Update access statistics for a cache entry."""
        query = f'''
            UPDATE {layer}_cache 
            SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP 
            WHERE key = %s
        '''
        await self.execute_query(query, (key,), fetch=False)
    
    async def _log_cache_operation(self, operation: str, key: str, layer: str, 
                                 success: bool, error_msg: str = None):
        """Log cache operations for monitoring."""
        execution_time = int((time.time() - getattr(self, '_operation_start_time', time.time())) * 1000)
        
        query = '''
            INSERT INTO cache_stats (cache_layer, operation, key, success, execution_time_ms)
            VALUES (%s, %s, %s, %s, %s)
        '''
        
        try:
            await self.execute_query(query, (layer, operation, key, success, execution_time), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log cache operation: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            # Get overall stats
            stats_query = '''
                SELECT 
                    cache_layer,
                    COUNT(*) as total_entries,
                    COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 END) as active_entries,
                    COUNT(CASE WHEN expires_at <= CURRENT_TIMESTAMP THEN 1 END) as expired_entries,
                    SUM(access_count) as total_accesses,
                    AVG(execution_time_ms) as avg_execution_time
                FROM cache_stats 
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                GROUP BY cache_layer
            '''
            
            stats = await self.execute_query(stats_query)
            
            # Get hit/miss ratio
            hit_ratio_query = '''
                SELECT 
                    cache_layer,
                    COUNT(CASE WHEN success = true THEN 1 END) as hits,
                    COUNT(CASE WHEN success = false THEN 1 END) as misses,
                    COUNT(*) as total
                FROM cache_stats 
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                GROUP BY cache_layer
            '''
            
            hit_ratio = await self.execute_query(hit_ratio_query)
            
            return {
                "cache_stats": stats,
                "hit_ratio": hit_ratio,
                "database_status": "healthy",
                "connection_pool": {
                    "min_size": self.pool_config['min_size'],
                    "max_size": self.pool_config['max_size'],
                    "current_size": self.connection_pool.pool.maxsize if self.connection_pool else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired_cache(self) -> Dict[str, Any]:
        """Clean up expired cache entries."""
        cleanup_stats = {}
        
        try:
            for layer in ['predictive_cache', 'semantic_cache', 'vector_cache', 'global_cache', 'vector_diary']:
                query = f'DELETE FROM {layer}_cache WHERE expires_at <= CURRENT_TIMESTAMP'
                result = await self.execute_query(query, fetch=False)
                cleanup_stats[layer] = result.rowcount if hasattr(result, 'rowcount') else 0
            
            logger.info(f"Cache cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            return {"error": str(e)}
    
    async def backup_database(self) -> Dict[str, Any]:
        """Create a backup of the database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.persist_dir}/backup/cache_backup_{timestamp}.sql"
            
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
            
            # Create backup using pg_dump
            backup_cmd = [
                'pg_dump',
                f'--host={self.db_host}',
                f'--port={self.db_port}',
                f'--username={self.db_user}',
                f'--dbname={self.db_name}',
                f'--file={backup_file}',
                '--verbose'
            ]
            
            # Set PGPASSWORD for authentication
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            process = await asyncio.create_subprocess_exec(
                *backup_cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Database backup created: {backup_file}")
                return {
                    "success": True,
                    "backup_file": backup_file,
                    "size": os.path.getsize(backup_file),
                    "timestamp": timestamp
                }
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Database backup failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "timestamp": timestamp
                }
                
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def restore_database(self, backup_file: str) -> Dict[str, Any]:
        """Restore database from backup."""
        try:
            # Restore using psql
            restore_cmd = [
                'psql',
                f'--host={self.db_host}',
                f'--port={self.db_port}',
                f'--username={self.db_user}',
                f'--dbname={self.db_name}',
                f'--file={backup_file}',
                '--verbose'
            ]
            
            # Set PGPASSWORD for authentication
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            process = await asyncio.create_subprocess_exec(
                *restore_cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Database restored from: {backup_file}")
                return {"success": True, "backup_file": backup_file}
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Database restore failed: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    result = cursor.fetchone()
                    
                    if result and result[0] == 1:
                        return {
                            "status": "healthy",
                            "timestamp": datetime.utcnow().isoformat(),
                            "response_time_ms": 10,  # Mock response time
                            "connection_pool": {
                                "min_size": self.pool_config['min_size'],
                                "max_size": self.pool_config['max_size'],
                                "current_size": self.connection_pool.pool.maxsize if self.connection_pool else 0
                            }
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "timestamp": datetime.utcnow().isoformat(),
                            "error": "Database query failed"
                        }
                        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _start_background_tasks(self):
        """Start background tasks for maintenance."""
        # Start health check task
        threading.Thread(target=self._health_check_loop, daemon=True).start()
        
        # Start backup task
        threading.Thread(target=self._backup_loop, daemon=True).start()
        
        # Start cleanup task
        threading.Thread(target=self._cleanup_loop, daemon=True).start()
        
        logger.info("Background tasks started")
    
    def _health_check_loop(self):
        """Background health check loop."""
        while True:
            try:
                asyncio.run(self.health_check())
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _backup_loop(self):
        """Background backup loop."""
        while True:
            try:
                asyncio.run(self.backup_database())
                time.sleep(self.backup_interval)
            except Exception as e:
                logger.error(f"Backup loop error: {e}")
                time.sleep(3600)  # Wait before retrying
    
    def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                asyncio.run(self.cleanup_expired_cache())
                time.sleep(3600)  # Run cleanup every hour
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                time.sleep(3600)
    
    def close(self):
        """Close the connection pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")

# Configuration for database integration
DATABASE_INTEGRATION_CONFIG = {
    "connection_pool": {
        "max_size": 20,
        "min_size": 5,
        "timeout": 30
    },
    "backup": {
        "enabled": True,
        "interval": 86400,  # 24 hours
        "retention": 7  # days
    },
    "monitoring": {
        "enabled": True,
        "health_check_interval": 60
    }
}

async def main():
    """Main function for testing database integration."""
    try:
        # Initialize database integration
        db_integration = DatabaseIntegration(DATABASE_INTEGRATION_CONFIG)
        
        # Test health check
        logger.info("Testing database health check...")
        health = await db_integration.health_check()
        logger.info(f"Health check result: {health}")
        
        # Test cache operations
        logger.info("Testing cache operations...")
        test_key = "test_key"
        test_value = {"message": "Hello, World!", "timestamp": datetime.utcnow().isoformat()}
        
        # Set cache value
        success = await db_integration.set_cache_value(test_key, test_value, "semantic_cache", ttl=3600)
        logger.info(f"Set cache value: {success}")
        
        # Get cache value
        cached_value = await db_integration.get_cache_value(test_key, "semantic_cache")
        logger.info(f"Get cache value: {cached_value}")
        
        # Get cache stats
        stats = await db_integration.get_cache_stats()
        logger.info(f"Cache stats: {stats}")
        
        # Test backup
        logger.info("Testing database backup...")
        backup_result = await db_integration.backup_database()
        logger.info(f"Backup result: {backup_result}")
        
        # Test cleanup
        logger.info("Testing cache cleanup...")
        cleanup_result = await db_integration.cleanup_expired_cache()
        logger.info(f"Cleanup result: {cleanup_result}")
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        raise
    finally:
        if 'db_integration' in locals():
            db_integration.close()

if __name__ == "__main__":
    asyncio.run(main())