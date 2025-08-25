import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from fastapi import HTTPException, status
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, String, JSON, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool
from datetime import datetime, timedelta
import json

from simba.core.config import settings
from src.vault_client import get_database_credentials
from simba.models.simbadoc import SimbaDoc, MetadataType
from simba.database.base import DatabaseService
from simba.database.token_models import TokenUsage, TokenLimits, TokenRevocations
from typing import List, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

Base = declarative_base()

class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that converts datetime objects to ISO format strings."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class SQLDocument(Base):
    """SQLAlchemy model for documents table"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)
    
    # Add relationship to chunks
    chunks = relationship("ChunkEmbedding", back_populates="document", cascade="all, delete-orphan")
    
    @classmethod
    def from_simbadoc(cls, doc: SimbaDoc, user_id: str) -> "SQLDocument":
        """Create Document from SimbaDoc with datetime handling"""
        return cls(
            id=doc.id,
            user_id=user_id,
            data=json.loads(json.dumps(doc.dict(), cls=DateTimeEncoder))
        )
    
    def to_simbadoc(self) -> SimbaDoc:
        """Convert to SimbaDoc"""
        return SimbaDoc(**self.data)

class PostgresDB(DatabaseService):
    """PostgreSQL database access with connection pooling and SQLAlchemy ORM."""
    
    # Connection pool singleton
    _pool = None
    _engine = None
    _Session = None
    
    def __init__(self):
        """Initialize database connection and ensure schema exists."""
        self._get_pool()
        self._initialize_sqlalchemy()
        self._ensure_schema()
    
    @classmethod
    def _get_pool(cls):
        """Get or create the connection pool."""
        if cls._pool is None:
            try:
                # Get database credentials from Vault
                db_creds = get_database_credentials("postgres")
                
                cls._pool = ThreadedConnectionPool(
                    minconn=3,
                    maxconn=10,
                    user=db_creds["username"],
                    password=db_creds["password"],
                    host=db_creds["host"],
                    port=db_creds["port"],
                    dbname=db_creds["database"],
                    sslmode='disable'
                )
                logger.info("Created PostgreSQL connection pool")
            except Exception as e:
                logger.error(f"Failed to create connection pool: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to connect to database"
                )
        return cls._pool
    
    def _initialize_sqlalchemy(self):
        """Initialize SQLAlchemy engine and session factory."""
        if self._engine is None:
            # Get database credentials from Vault
            db_creds = get_database_credentials("postgres")
            
            url = URL.create(
                "postgresql",
                username=db_creds["username"],
                password=db_creds["password"],
                host=db_creds["host"],
                port=db_creds["port"],
                database=db_creds["database"]
            )
            # Use NullPool since we're managing our own connection pool
            self._engine = create_engine(url, poolclass=NullPool)
            self._Session = sessionmaker(bind=self._engine)
            Base.metadata.create_all(self._engine)
            logger.info("Initialized SQLAlchemy engine")
    
    def _ensure_schema(self):
        """Ensure the required database schema exists and pg_tiktoken extension is enabled."""
        Base.metadata.create_all(self._engine)
        self._ensure_pg_tiktoken_extension()
        self._ensure_token_management_tables()
    
    def _ensure_pg_tiktoken_extension(self):
        """Ensure the pg_tiktoken extension is enabled in the database."""
        try:
            # Read and execute the pg_tiktoken extension setup script
            extension_script_path = "src/database/migrations/001_enable_pg_tiktoken.sql"
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Read the SQL script
                    with open(extension_script_path, 'r') as f:
                        sql_script = f.read()
                    
                    # Execute the script
                    cursor.execute(sql_script)
                    conn.commit()
                    logger.info("pg_tiktoken extension setup completed successfully")
                    
        except FileNotFoundError:
            logger.warning(f"pg_tiktoken extension script not found at {extension_script_path}")
        except Exception as e:
            logger.warning(f"Failed to setup pg_tiktoken extension: {str(e)}")
            # Don't raise the exception as the system should work without the extension
            # This provides backward compatibility
    
    def _ensure_token_management_tables(self):
        """Ensure the token management tables exist and are properly initialized."""
        try:
            # Read and execute the token management tables setup script
            migration_script_path = "src/database/migrations/002_create_token_management_tables.sql"
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Read the SQL script
                    with open(migration_script_path, 'r') as f:
                        sql_script = f.read()
                    
                    # Execute the script
                    cursor.execute(sql_script)
                    conn.commit()
                    logger.info("Token management tables setup completed successfully")
                    
        except FileNotFoundError:
            logger.warning(f"Token management tables script not found at {migration_script_path}")
        except Exception as e:
            logger.warning(f"Failed to setup token management tables: {str(e)}")
            # Don't raise the exception as the system should work without the tables
            # This provides backward compatibility
    
    def is_tiktoken_available(self):
        """Check if pg_tiktoken extension is available and working."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("SELECT is_tiktoken_available() as available")
                    result = cursor.fetchone()
                    return result['available'] if result else False
        except Exception as e:
            logger.warning(f"Error checking tiktoken availability: {str(e)}")
            return False
    
    def get_token_count(self, text: str):
        """Get token count for text using pg_tiktoken if available, fallback to basic estimate."""
        if self.is_tiktoken_available():
            try:
                with self.get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute("SELECT tiktoken_count(%s) as count", (text,))
                        result = cursor.fetchone()
                        return result['count'] if result else 0
            except Exception as e:
                logger.warning(f"Error getting token count from tiktoken: {str(e)}")
                # Fall back to basic estimation
        
        # Fallback: basic word-based token estimation
        # This is a rough approximation and not as accurate as tiktoken
        return len(text.split()) * 1.3  # Rough estimate: 1.3 tokens per word
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get a connection from the pool and return it when done."""
        pool = cls._get_pool()
        conn = None
        try:
            conn = pool.getconn()
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
        finally:
            if conn:
                pool.putconn(conn)
    
    # Raw SQL query methods
    @classmethod
    def execute_query(cls, query, params=None):
        """Run an INSERT, UPDATE, or DELETE query."""
        with cls.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    logger.info(f"Executing query: {query}")
                    logger.info(f"Parameters: {params}")
                    cursor.execute(query, params or ())
                    rowcount = cursor.rowcount
                    logger.info(f"Query executed successfully. Affected rows: {rowcount}")
                conn.commit()
                logger.info("Transaction committed")
                return rowcount
            except Exception as e:
                conn.rollback()
                logger.error(f"Query execution error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database query failed: {str(e)}"
                )
    
    @classmethod
    def fetch_all(cls, query, params=None):
        """Run a SELECT query and return all results."""
        with cls.get_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    logger.info(f"Executing fetch_all query: {query}")
                    logger.info(f"Parameters: {params}")
                    cursor.execute(query, params or ())
                    results = cursor.fetchall()
                    logger.info(f"Query returned {len(results)} results")
                    return [dict(row) for row in results]
    
    def health_check(self) -> bool:
        """
        Check database health status.
        
        Returns:
            True if database is healthy, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def check_connection(self) -> bool:
        """
        Check database connection status.
        
        Returns:
            True if database is connected, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def is_token_revoked(self, token_id: str) -> bool:
        """
        Check if a token has been revoked.
        
        Args:
            token_id: Token ID to check
            
        Returns:
            True if revoked, False otherwise
        """
        try:
            query = """
                SELECT 1 FROM token_revocations
                WHERE token = %s
            """
            result = self.fetch_one(query, (token_id,))
            return result is not None
        except Exception as e:
            logger.error(f"Error checking token revocation: {e}")
            return True  # Fail secure - assume revoked if error occurs
    
    def revoke_token(self, token_id: str, reason: Optional[str] = None) -> bool:
        """
        Revoke a token in the database.
        
        Args:
            token_id: Token ID to revoke
            reason: Reason for revocation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO token_revocations (token, reason)
                VALUES (%s, %s)
                ON CONFLICT (token) DO UPDATE
                SET revoked_at = NOW(), reason = EXCLUDED.reason
            """
            rowcount = self.execute_query(query, (token_id, reason))
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    def get_security_audit_logs(self, user_id: Optional[str] = None,
                               service_name: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get security audit logs with optional filtering.
        
        Args:
            user_id: Filter by user ID (optional)
            service_name: Filter by service name (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of security audit log records
        """
        try:
            query = """
                SELECT event_type, severity_level, user_id, service_name,
                       action, details, ip_address, user_agent, session_id, created_at
                FROM security_audit_log
                WHERE 1=1
            """
            params = []
            
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            
            if service_name:
                query += " AND service_name = %s"
                params.append(service_name)
            
            if start_date:
                query += " AND created_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND created_at <= %s"
                params.append(end_date)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            return self.fetch_all(query, params)
            
        except Exception as e:
            logger.error(f"Error getting security audit logs: {e}")
            return []
    
    def get_security_alerts(self, status: Optional[str] = None,
                           severity_level: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get security alerts with optional filtering.
        
        Args:
            status: Filter by status (optional)
            severity_level: Filter by severity level (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of security alert records
        """
        try:
            query = """
                SELECT id, alert_type, severity_level, user_id, service_name,
                       description, details, status, created_at, resolved_at
                FROM security_alerts
                WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            if severity_level:
                query += " AND severity_level = %s"
                params.append(severity_level)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            return self.fetch_all(query, params)
            
        except Exception as e:
            logger.error(f"Error getting security alerts: {e}")
            return []
    
    def create_security_alert(self, alert_type: str, severity_level: str,
                            user_id: str, service_name: str,
                            description: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a security alert.
        
        Args:
            alert_type: Type of alert
            severity_level: Severity level
            user_id: User identifier
            service_name: Service name
            description: Alert description
            details: Additional alert details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO security_alerts
                (alert_type, severity_level, user_id, service_name, description, details)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            details_json = json.dumps(details) if details else None
            rowcount = self.execute_query(query, (
                alert_type, severity_level, user_id, service_name, description, details_json
            ))
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error creating security alert: {e}")
            return False
    
    def resolve_security_alert(self, alert_id: str, resolution_notes: Optional[str] = None) -> bool:
        """
        Resolve a security alert.
        
        Args:
            alert_id: Alert ID to resolve
            resolution_notes: Notes about the resolution
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE security_alerts
                SET status = 'RESOLVED', resolved_at = NOW(), resolution_notes = %s
                WHERE id = %s
            """
            rowcount = self.execute_query(query, (resolution_notes, alert_id))
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error resolving security alert: {e}")
            return False
    
    def get_security_configurations(self) -> List[Dict[str, Any]]:
        """
        Get all security configurations.
        
        Returns:
            List of security configuration records
        """
        try:
            query = """
                SELECT config_key, config_value, config_type, description, is_active, created_at, updated_at
                FROM security_configurations
                ORDER BY config_key
            """
            return self.fetch_all(query)
        except Exception as e:
            logger.error(f"Error getting security configurations: {e}")
            return []
    
    def update_security_configuration(self, config_key: str, config_value: str,
                                     config_type: str, description: str) -> bool:
        """
        Update a security configuration.
        
        Args:
            config_key: Configuration key
            config_value: Configuration value
            config_type: Configuration type
            description: Configuration description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO security_configurations
                (config_key, config_value, config_type, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (config_key) DO UPDATE
                SET config_value = EXCLUDED.config_value,
                    config_type = EXCLUDED.config_type,
                    description = EXCLUDED.description,
                    updated_at = NOW()
            """
            rowcount = self.execute_query(query, (config_key, config_value, config_type, description))
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error updating security configuration: {e}")
            return False
    
    def get_user_security_events(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get security events for a specific user.
        
        Args:
            user_id: User identifier
            days: Number of days to include in history
            
        Returns:
            List of security events
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = """
                SELECT event_type, severity_level, service_name, action, details, created_at
                FROM security_audit_log
                WHERE user_id = %s AND created_at >= %s
                ORDER BY created_at DESC
            """
            return self.fetch_all(query, (user_id, start_date))
        except Exception as e:
            logger.error(f"Error getting user security events: {e}")
            return []
    
    def get_security_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get security summary statistics.
        
        Args:
            days: Number of days to include in summary
            
        Returns:
            Dictionary with security summary statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get total events
            events_query = """
                SELECT COUNT(*) as total_events
                FROM security_audit_log
                WHERE created_at >= %s
            """
            events_result = self.fetch_one(events_query, (start_date,))
            total_events = events_result['total_events'] if events_result else 0
            
            # Get events by type
            type_query = """
                SELECT event_type, COUNT(*) as count
                FROM security_audit_log
                WHERE created_at >= %s
                GROUP BY event_type
                ORDER BY count DESC
            """
            type_results = self.fetch_all(type_query, (start_date,))
            
            # Get active alerts
            alerts_query = """
                SELECT COUNT(*) as active_alerts
                FROM security_alerts
                WHERE status = 'OPEN' AND created_at >= %s
            """
            alerts_result = self.fetch_one(alerts_query, (start_date,))
            active_alerts = alerts_result['active_alerts'] if alerts_result else 0
            
            # Get revoked tokens
            revoked_query = """
                SELECT COUNT(*) as revoked_tokens
                FROM token_revocations
                WHERE revoked_at >= %s
            """
            revoked_result = self.fetch_one(revoked_query, (start_date,))
            revoked_tokens = revoked_result['revoked_tokens'] if revoked_result else 0
            
            return {
                'period_days': days,
                'total_events': total_events,
                'events_by_type': [
                    {'event_type': row['event_type'], 'count': row['count']}
                    for row in type_results
                ],
                'active_alerts': active_alerts,
                'revoked_tokens': revoked_tokens,
                'start_date': start_date.isoformat(),
                'end_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting security summary: {e}")
            return {
                'period_days': days,
                'total_events': 0,
                'events_by_type': [],
                'active_alerts': 0,
                'revoked_tokens': 0,
                'error': str(e)
            }
    
    @classmethod
    def fetch_one(cls, query, params=None):
        """Run a SELECT query and return one result."""
        with cls.get_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    logger.info(f"Executing fetch_one query: {query}")
                    logger.info(f"Parameters: {params}")
                    cursor.execute(query, params or ())
                    row = cursor.fetchone()
                    if row:
                        logger.info(f"Query returned a row with id: {row.get('id')}")
                        return dict(row)
                    else:
                        logger.warning("Query returned no results")
                        return None
            except Exception as e:
                logger.error(f"fetch_one error: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database fetch failed: {str(e)}"
                )
    
    # ORM methods implementing DatabaseService interface
    def insert_document(self, document: SimbaDoc, user_id: str) -> str:
        """Insert a single document using SQLAlchemy ORM."""
        try:
            session = self._Session()
            db_doc = SQLDocument.from_simbadoc(document, user_id)
            session.add(db_doc)
            session.commit()
            return document.id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert document: {e}")
            raise
        finally:
            session.close()
    
    def insert_documents(self, documents: SimbaDoc | List[SimbaDoc], user_id: str) -> List[str]:
        """Insert one or multiple documents using SQLAlchemy ORM."""
        if not isinstance(documents, list):
            documents = [documents]
            
        try:
            session = self._Session()
            db_docs = [SQLDocument.from_simbadoc(doc, user_id) for doc in documents]
            session.add_all(db_docs)
            session.commit()
            return [doc.id for doc in documents]
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert documents: {e}")
            raise
        finally:
            session.close()
    
    def get_document(self, document_id: str | List[str], user_id: str = None) -> Optional[SimbaDoc] | List[Optional[SimbaDoc]]:
        """Retrieve a document by ID or a list of documents by IDs using SQLAlchemy ORM.
        If a list of IDs is provided, returns a list of SimbaDoc (None for not found).
        If a single ID is provided, returns a single SimbaDoc or None.
        """
        try:
            session = self._Session()
            if isinstance(document_id, list):
                query = session.query(SQLDocument).filter(SQLDocument.id.in_(document_id))
                if user_id:
                    query = query.filter(SQLDocument.user_id == user_id)
                docs = query.all()
                # Map id to doc for fast lookup
                doc_map = {doc.id: doc for doc in docs}
                # Return in the same order as input list, None if not found
                return [doc_map.get(doc_id).to_simbadoc() if doc_map.get(doc_id) else None for doc_id in document_id]
            else:
                query = session.query(SQLDocument).filter(SQLDocument.id == document_id)
                if user_id:
                    query = query.filter(SQLDocument.user_id == user_id)
                doc = query.first()
                return doc.to_simbadoc() if doc else None
        except Exception as e:
            logger.error(f"Failed to get document(s) {document_id}: {e}")
            if isinstance(document_id, list):
                return [None for _ in document_id]
            return None
        finally:
            session.close()
    
    def get_all_documents(self, user_id: str = None) -> List[SimbaDoc]:
        """Retrieve all documents using SQLAlchemy ORM."""
        try:
            session = self._Session()
            query = session.query(SQLDocument)
            
            # Filter by user_id if provided
            if user_id:
                query = query.filter(SQLDocument.user_id == user_id)
            
            docs = query.all()
            return [doc.to_simbadoc() for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return []
        finally:
            session.close()
    
    def update_document(self, document_id: str, document: SimbaDoc, user_id: str = None) -> bool:
        """Update a document using SQLAlchemy ORM with proper datetime handling."""
        try:
            session = self._Session()
            # Convert to dict with datetime handling
            doc_dict = json.loads(json.dumps(document.dict(), cls=DateTimeEncoder))
            
            # Build query
            query = session.query(SQLDocument).filter(SQLDocument.id == document_id)
            
            # Filter by user_id if provided
            if user_id:
                query = query.filter(SQLDocument.user_id == user_id)
            
            result = query.update({"data": doc_dict})
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update document {document_id}: {e}")
            return False
        finally:
            session.close()
    
    def delete_document(self, document_id: str, user_id: str = None) -> bool:
        """Delete a document using SQLAlchemy ORM."""
        try:
            session = self._Session()
            
            # Build query
            query = session.query(SQLDocument).filter(SQLDocument.id == document_id)
            
            # Filter by user_id if provided
            if user_id:
                query = query.filter(SQLDocument.user_id == user_id)
            
            result = query.delete()
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
        finally:
            session.close()
            
    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete multiple documents using SQLAlchemy ORM."""
        try:
            session = self._Session()
            result = session.query(SQLDocument).filter(SQLDocument.id.in_(document_ids)).delete(synchronize_session=False)
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete documents: {e}")
            return False
        finally:
            session.close()
    
    def clear_database(self) -> bool:
        """Clear all documents from the database using SQLAlchemy ORM."""
        try:
            session = self._Session()
            session.query(SQLDocument).delete()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to clear database: {e}")
            return False
        finally:
            session.close()
    
    def query_documents(self, filters: Dict[str, Any]) -> List[SimbaDoc]:
        """Query documents using filters.
        
        Supports filtering on both document ID and nested JSON data fields.
        For JSON data, use dot notation in filter keys, e.g.:
        {
            'id': '123',
            'user_id': 'user-uuid',
            'metadata.source': 'web',
            'content': 'search text'
        }
        
        Args:
            filters: Dictionary of field-value pairs to filter by
            
        Returns:
            List of matching documents
        """
        try:
            session = self._Session()
            query = session.query(SQLDocument)
            
            for key, value in filters.items():
                if key == 'id':
                    query = query.filter(SQLDocument.id == value)
                elif key == 'user_id':
                    query = query.filter(SQLDocument.user_id == value)
                else:
                    # Handle nested JSON filters using PostgreSQL JSON operators
                    path_parts = key.split('.')
                    # Build the JSON path operator
                    json_path_str = '->'.join([f"'{part}'" for part in path_parts[:-1]])
                    if json_path_str:
                        json_path_str += '->>'
                    else:
                        json_path_str = '->>'
                    json_path_str += f"'{path_parts[-1]}'"
                    
                    # Apply the filter using raw SQL for JSON operators
                    query = query.filter(
                        f"data {json_path_str} = :value",
                        value=str(value)
                    )
            
            results = query.all()
            return [doc.to_simbadoc() for doc in results]
            
        except Exception as e:
            logger.error(f"Failed to query documents: {e}")
            return []
        finally:
            session.close()
    
    @classmethod
    def health_check(cls):
        """Test if database c   onnection works."""
        try:
            with cls.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
            
    @classmethod
    def close_pool(cls):
        """Close all connections in the pool."""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
            logger.info("Closed PostgreSQL connection pool")
    
    # Token Management Methods
    
    def log_token_usage(self, user_id: str, session_id: str, tokens_used: int,
                       api_endpoint: str, priority_level: str = "Medium") -> bool:
        """Log token usage for a specific request.
        
        Args:
            user_id: The user identifier
            session_id: The session identifier
            tokens_used: Number of tokens consumed
            api_endpoint: API endpoint or service used
            priority_level: Priority level ('Low', 'Medium', 'High')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._Session()
            token_usage = TokenUsage(
                user_id=user_id,
                session_id=session_id,
                tokens_used=tokens_used,
                api_endpoint=api_endpoint,
                priority_level=priority_level
            )
            session.add(token_usage)
            session.commit()
            logger.info(f"Logged token usage: {tokens_used} tokens for user {user_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log token usage: {e}")
            return False
        finally:
            session.close()
    
    def get_user_token_usage(self, user_id: str, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get token usage for a specific user within a date range.
        
        Args:
            user_id: The user identifier
            start_date: Start date for the query (optional)
            end_date: End date for the query (optional)
            
        Returns:
            List of token usage records
        """
        try:
            session = self._Session()
            query = session.query(TokenUsage).filter(TokenUsage.user_id == user_id)
            
            if start_date:
                query = query.filter(TokenUsage.timestamp >= start_date)
            if end_date:
                query = query.filter(TokenUsage.timestamp <= end_date)
            
            results = query.order_by(TokenUsage.timestamp.desc()).all()
            return [
                {
                    'id': record.id,
                    'user_id': record.user_id,
                    'session_id': record.session_id,
                    'tokens_used': record.tokens_used,
                    'api_endpoint': record.api_endpoint,
                    'priority_level': record.priority_level,
                    'timestamp': record.timestamp.isoformat()
                }
                for record in results
            ]
        except Exception as e:
            logger.error(f"Failed to get user token usage: {e}")
            return []
        finally:
            session.close()
    
    def set_user_token_limit(self, user_id: str, max_tokens_per_period: int,
                           period_interval: str = "1 day") -> bool:
        """Set or update token limits for a user.
        
        Args:
            user_id: The user identifier
            max_tokens_per_period: Maximum tokens allowed per period
            period_interval: Period interval (e.g., "1 day", "7 days")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._Session()
            
            # Check if user already has a token limit
            existing_limit = session.query(TokenLimits).filter(
                TokenLimits.user_id == user_id,
                TokenLimits.period_start >= datetime.utcnow() - timedelta(days=1)
            ).first()
            
            if existing_limit:
                # Update existing limit
                existing_limit.max_tokens_per_period = max_tokens_per_period
                existing_limit.period_interval = timedelta(days=int(period_interval.split()[0]))
                existing_limit.tokens_used_in_period = 0  # Reset usage
                existing_limit.period_start = datetime.utcnow()
            else:
                # Create new limit
                token_limit = TokenLimits(
                    user_id=user_id,
                    max_tokens_per_period=max_tokens_per_period,
                    period_interval=timedelta(days=int(period_interval.split()[0])),
                    tokens_used_in_period=0,
                    period_start=datetime.utcnow()
                )
                session.add(token_limit)
            
            session.commit()
            logger.info(f"Set token limit for user {user_id}: {max_tokens_per_period} tokens per {period_interval}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to set user token limit: {e}")
            return False
        finally:
            session.close()
    
    def get_user_token_limit(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current token limit for a user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Token limit information or None if not found
        """
        try:
            session = self._Session()
            token_limit = session.query(TokenLimits).filter(
                TokenLimits.user_id == user_id,
                TokenLimits.period_start >= datetime.utcnow() - timedelta(days=1)
            ).first()
            
            if token_limit:
                return {
                    'id': token_limit.id,
                    'user_id': token_limit.user_id,
                    'max_tokens_per_period': token_limit.max_tokens_per_period,
                    'period_interval': str(token_limit.period_interval),
                    'tokens_used_in_period': token_limit.tokens_used_in_period,
                    'period_start': token_limit.period_start.isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get user token limit: {e}")
            return None
        finally:
            session.close()
    
    def check_token_quota(self, user_id: str, tokens_requested: int,
                         priority_level: str = "Medium") -> Dict[str, Any]:
        """Check if user has sufficient token quota for the requested tokens.
        
        Args:
            user_id: The user identifier
            tokens_requested: Number of tokens requested
            priority_level: Priority level ('Low', 'Medium', 'High')
            
        Returns:
            Dictionary with quota check results
        """
        try:
            session = self._Session()
            token_limit = session.query(TokenLimits).filter(
                TokenLimits.user_id == user_id,
                TokenLimits.period_start >= datetime.utcnow() - timedelta(days=1)
            ).first()
            
            if not token_limit:
                return {
                    'allowed': False,
                    'reason': 'No token limit set for user',
                    'remaining_tokens': 0,
                    'max_tokens': 0,
                    'used_tokens': 0
                }
            
            remaining_tokens = token_limit.max_tokens_per_period - token_limit.tokens_used_in_period
            
            # Calculate allocation based on priority
            allocation_percentages = {'High': 0.5, 'Medium': 0.3, 'Low': 0.2}
            allocation_percentage = allocation_percentages.get(priority_level, 0.3)
            allocated_tokens = int(remaining_tokens * allocation_percentage)
            
            allowed = tokens_requested <= allocated_tokens and tokens_requested <= remaining_tokens
            
            return {
                'allowed': allowed,
                'reason': 'Quota exceeded' if not allowed else 'Quota available',
                'remaining_tokens': remaining_tokens,
                'max_tokens': token_limit.max_tokens_per_period,
                'used_tokens': token_limit.tokens_used_in_period,
                'allocated_tokens': allocated_tokens,
                'priority_level': priority_level
            }
        except Exception as e:
            logger.error(f"Failed to check token quota: {e}")
            return {
                'allowed': False,
                'reason': f'Error checking quota: {str(e)}',
                'remaining_tokens': 0,
                'max_tokens': 0,
                'used_tokens': 0
            }
        finally:
            session.close()
    
    def update_token_usage(self, user_id: str, tokens_used: int) -> bool:
        """Update token usage for a user.
        
        Args:
            user_id: The user identifier
            tokens_used: Number of tokens to add to usage
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._Session()
            result = session.query(TokenLimits).filter(
                TokenLimits.user_id == user_id,
                TokenLimits.period_start >= datetime.utcnow() - timedelta(days=1)
            ).update({'tokens_used_in_period': TokenLimits.tokens_used_in_period + tokens_used})
            
            session.commit()
            logger.info(f"Updated token usage for user {user_id}: +{tokens_used} tokens")
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update token usage: {e}")
            return False
        finally:
            session.close()
    
    def revoke_token(self, token: str, reason: Optional[str] = None) -> bool:
        """Revoke a token.
        
        Args:
            token: The token to revoke
            reason: Reason for revocation (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._Session()
            token_revocation = TokenRevocations(
                token=token,
                reason=reason
            )
            session.add(token_revocation)
            session.commit()
            logger.info(f"Revoked token: {token}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to revoke token: {e}")
            return False
        finally:
            session.close()
    
    def is_token_revoked(self, token: str) -> bool:
        """Check if a token has been revoked.
        
        Args:
            token: The token to check
            
        Returns:
            True if revoked, False otherwise
        """
        try:
            session = self._Session()
            revoked = session.query(TokenRevocations).filter(
                TokenRevocations.token == token
            ).first()
            return revoked is not None
        except Exception as e:
            logger.error(f"Failed to check token revocation: {e}")
            return False
        finally:
            session.close()
    
    def get_token_usage_summary(self, user_id: Optional[str] = None,
                              days: int = 7) -> Dict[str, Any]:
        """Get token usage summary for users.
        
        Args:
            user_id: Specific user to get summary for (optional)
            days: Number of days to include in summary
            
        Returns:
            Dictionary with usage summary
        """
        try:
            session = self._Session()
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = session.query(TokenUsage).filter(TokenUsage.timestamp >= start_date)
            if user_id:
                query = query.filter(TokenUsage.user_id == user_id)
            
            results = query.all()
            
            total_tokens = sum(record.tokens_used for record in results)
            unique_users = set(record.user_id for record in results)
            
            # Group by day
            daily_usage = {}
            for record in results:
                day = record.timestamp.strftime('%Y-%m-%d')
                if day not in daily_usage:
                    daily_usage[day] = 0
                daily_usage[day] += record.tokens_used
            
            return {
                'total_tokens': total_tokens,
                'total_requests': len(results),
                'unique_users': len(unique_users),
                'daily_usage': daily_usage,
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get token usage summary: {e}")
            return {
                'total_tokens': 0,
                'total_requests': 0,
                'unique_users': 0,
                'daily_usage': {},
                'period_days': days,
                'start_date': start_date.isoformat() if 'start_date' in locals() else None,
                'end_date': datetime.utcnow().isoformat(),
                'error': str(e)
            }
        finally:
            session.close()
    
    # Rate Limiting Methods
    
    def check_rate_limit(self, user_id: str, api_endpoint: str,
                        request_weight: int = 1, window_duration: str = "1 hour") -> Dict[str, Any]:
        """
        Check if a user is within rate limits for an API endpoint.
        
        Args:
            user_id: The user identifier
            api_endpoint: API endpoint identifier
            request_weight: Weight of the current request
            window_duration: Duration of the rate limit window
            
        Returns:
            Dictionary with rate limit check results
        """
        try:
            session = self._Session()
            
            # Parse window duration
            if window_duration == "1 minute":
                window_start = datetime.utcnow() - timedelta(minutes=1)
            elif window_duration == "1 hour":
                window_start = datetime.utcnow() - timedelta(hours=1)
            elif window_duration == "1 day":
                window_start = datetime.utcnow() - timedelta(days=1)
            elif window_duration == "1 week":
                window_start = datetime.utcnow() - timedelta(weeks=1)
            else:
                window_start = datetime.utcnow() - timedelta(hours=1)  # Default
            
            # Get usage in the specified window
            usage_records = session.query(TokenUsage).filter(
                TokenUsage.user_id == user_id,
                TokenUsage.api_endpoint == api_endpoint,
                TokenUsage.timestamp >= window_start
            ).all()
            
            total_requests = sum(record.tokens_used for record in usage_records)
            
            # Get user's rate limit (simplified - in production you'd have a separate rate_limits table)
            rate_limit = session.query(TokenLimits).filter(
                TokenLimits.user_id == user_id
            ).first()
            
            max_requests = rate_limit.max_tokens_per_period if rate_limit else 1000
            remaining_requests = max(0, max_requests - total_requests)
            
            # Check if request is allowed
            allowed = remaining_requests >= request_weight
            
            # Calculate reset time
            if rate_limit:
                period_end = rate_limit.period_start + rate_limit.period_interval
            else:
                period_end = datetime.utcnow() + timedelta(hours=1)
            
            return {
                'allowed': allowed,
                'total_requests': total_requests,
                'max_requests': max_requests,
                'remaining_requests': remaining_requests,
                'request_weight': request_weight,
                'window_duration': window_duration,
                'reset_time': period_end.isoformat(),
                'user_id': user_id,
                'api_endpoint': api_endpoint
            }
            
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return {
                'allowed': True,  # Allow on error to prevent service disruption
                'total_requests': 0,
                'max_requests': 1000,
                'remaining_requests': 1000,
                'request_weight': request_weight,
                'window_duration': window_duration,
                'reset_time': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                'user_id': user_id,
                'api_endpoint': api_endpoint,
                'error': str(e)
            }
        finally:
            session.close()
    
    def enforce_rate_limit(self, user_id: str, api_endpoint: str,
                          request_weight: int = 1, window_duration: str = "1 hour") -> Dict[str, Any]:
        """
        Enforce rate limits and reject requests that exceed limits.
        
        Args:
            user_id: The user identifier
            api_endpoint: API endpoint identifier
            request_weight: Weight of the current request
            window_duration: Duration of the rate limit window
            
        Returns:
            Dictionary with rate limit enforcement results
            
        Raises:
            HTTPException: If rate limits are exceeded
        """
        result = self.check_rate_limit(user_id, api_endpoint, request_weight, window_duration)
        
        if not result['allowed']:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    'error': 'Rate limit exceeded',
                    'message': f'Rate limit exceeded for {api_endpoint}. '
                              f'Try again after {result["reset_time"]}',
                    'retry_after': result['reset_time'],
                    'usage': {
                        'used': result['total_requests'],
                        'limit': result['max_requests'],
                        'remaining': result['remaining_requests']
                    }
                }
            )
        
        return result
    
    def get_rate_limit_status(self, user_id: str, api_endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current rate limit status for a user.
        
        Args:
            user_id: The user identifier
            api_endpoint: Specific API endpoint to check (optional)
            
        Returns:
            Dictionary with rate limit status
        """
        try:
            session = self._Session()
            
            # Get user's token limit
            token_limit = session.query(TokenLimits).filter(
                TokenLimits.user_id == user_id
            ).first()
            
            if not token_limit:
                return {
                    'user_id': user_id,
                    'has_limit': False,
                    'max_tokens': 0,
                    'used_tokens': 0,
                    'remaining_tokens': 0,
                    'usage_percentage': 0,
                    'period_start': datetime.utcnow().isoformat(),
                    'period_end': datetime.utcnow().isoformat()
                }
            
            # Get usage for the current period
            period_start = token_limit.period_start
            usage_records = session.query(TokenUsage).filter(
                TokenUsage.user_id == user_id,
                TokenUsage.timestamp >= period_start
            )
            
            if api_endpoint:
                usage_records = usage_records.filter(TokenUsage.api_endpoint == api_endpoint)
            
            total_used = sum(record.tokens_used for record in usage_records.all())
            remaining_tokens = max(0, token_limit.max_tokens_per_period - total_used)
            usage_percentage = (total_used / token_limit.max_tokens_per_period) * 100
            
            period_end = token_limit.period_start + token_limit.period_interval
            
            return {
                'user_id': user_id,
                'has_limit': True,
                'max_tokens': token_limit.max_tokens_per_period,
                'used_tokens': total_used,
                'remaining_tokens': remaining_tokens,
                'usage_percentage': usage_percentage,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                'api_endpoint': api_endpoint
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {
                'user_id': user_id,
                'has_limit': False,
                'max_tokens': 0,
                'used_tokens': 0,
                'remaining_tokens': 0,
                'usage_percentage': 0,
                'period_start': datetime.utcnow().isoformat(),
                'period_end': datetime.utcnow().isoformat(),
                'error': str(e)
            }
        finally:
            session.close()
    
    def set_rate_limit(self, user_id: str, max_tokens_per_period: int,
                      period_interval: str = "1 day") -> bool:
        """
        Set rate limit for a user.
        
        Args:
            user_id: The user identifier
            max_tokens_per_period: Maximum tokens allowed per period
            period_interval: Period interval (e.g., "1 day", "7 days")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._Session()
            
            # Check if user already has a rate limit
            existing_limit = session.query(TokenLimits).filter(
                TokenLimits.user_id == user_id
            ).first()
            
            if existing_limit:
                # Update existing limit
                existing_limit.max_tokens_per_period = max_tokens_per_period
                existing_limit.period_interval = timedelta(days=int(period_interval.split()[0]))
                existing_limit.tokens_used_in_period = 0  # Reset usage
                existing_limit.period_start = datetime.utcnow()
            else:
                # Create new limit
                token_limit = TokenLimits(
                    user_id=user_id,
                    max_tokens_per_period=max_tokens_per_period,
                    period_interval=timedelta(days=int(period_interval.split()[0])),
                    tokens_used_in_period=0,
                    period_start=datetime.utcnow()
                )
                session.add(token_limit)
            
            session.commit()
            logger.info(f"Set rate limit for user {user_id}: {max_tokens_per_period} tokens per {period_interval}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to set rate limit: {e}")
    
    def schedule_quota_reset(self, user_id: Optional[str] = None,
                           reset_type: str = 'daily',
                           reset_interval: str = '1 day',
                           reset_time: str = '00:00:00',
                           metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Schedule a quota reset operation.
        
        Args:
            user_id: Specific user to reset (None for all users)
            reset_type: Type of reset period
            reset_interval: Interval for custom resets
            reset_time: Time of day for resets
            metadata: Additional metadata for the schedule
            
        Returns:
            Schedule ID
        """
        try:
            query = """
                INSERT INTO quota_reset_schedules
                (user_id, reset_type, reset_interval, reset_time, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            
            result = self.fetch_one(
                query,
                (
                    user_id,
                    reset_type,
                    reset_interval,
                    reset_time,
                    json.dumps(metadata or {})
                )
            )
            
            if result is None:
                raise Exception("Failed to create schedule")
            
            return result['id']
            
        except Exception as e:
            logger.error(f"Error scheduling quota reset: {e}")
            raise
    
    def execute_scheduled_quota_reset(self, schedule_id: int) -> str:
        """
        Execute a scheduled quota reset.
        
        Args:
            schedule_id: ID of schedule to execute
            
        Returns:
            Status of the operation
        """
        try:
            query = "SELECT execute_scheduled_quota_reset(%s)"
            result = self.fetch_one(query, (schedule_id,))
            return result['execute_scheduled_quota_reset']
            
        except Exception as e:
            logger.error(f"Error executing scheduled quota reset: {e}")
            raise
    
    def get_pending_resets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending quota reset schedules.
        
        Args:
            limit: Maximum number of schedules to return
            
        Returns:
            List of pending quota reset schedules
        """
        try:
            query = """
                SELECT id, user_id, reset_type, reset_interval, reset_time,
                       is_active, last_reset, next_reset, created_at, updated_at, metadata
                FROM quota_reset_schedules
                WHERE is_active = true AND next_reset <= NOW() + INTERVAL '1 hour'
                ORDER BY next_reset ASC
                LIMIT %s
            """
            
            results = self.fetch_all(query, (limit,))
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting pending resets: {e}")
            return []
    
    def cancel_scheduled_reset(self, schedule_id: int) -> bool:
        """
        Cancel a scheduled quota reset.
        
        Args:
            schedule_id: ID of schedule to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            query = """
                UPDATE quota_reset_schedules
                SET is_active = false, updated_at = NOW()
                WHERE id = %s
            """
            
            result = self.execute_query(query, (schedule_id,))
            return result > 0
            
        except Exception as e:
            logger.error(f"Error cancelling scheduled reset: {e}")
            return False
    
    def get_reset_history(self, user_id: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get quota reset history.
        
        Args:
            user_id: Filter by user ID (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of quota reset operations
        """
        try:
            query = """
                SELECT id, schedule_id, user_id, reset_type, reset_start, reset_end,
                       tokens_reset, users_affected, status, error_message,
                       execution_time, created_at
                FROM quota_reset_history
                WHERE (%s::text IS NULL OR user_id = %s)
                AND (%s IS NULL OR created_at >= %s)
                AND (%s IS NULL OR created_at <= %s)
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            results = self.fetch_all(
                query,
                (
                    user_id,
                    user_id,
                    start_date,
                    start_date,
                    end_date,
                    end_date,
                    limit
                )
            )
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting reset history: {e}")
            return []
    
    def get_quota_reset_health(self) -> Dict[str, Any]:
        """
        Get quota reset system health status.
        
        Returns:
            Dictionary with system health information
        """
        try:
            query = """
                SELECT
                    COUNT(*) as total_schedules,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as active_schedules,
                    COUNT(CASE WHEN is_active = true AND next_reset <= NOW() + INTERVAL '1 hour' THEN 1 END) as pending_resets,
                    MAX(last_reset) as last_reset,
                    MIN(next_reset) as next_reset
                FROM quota_reset_schedules
            """
            
            result = self.fetch_one(query)
            
            return {
                'total_schedules': result['total_schedules'],
                'active_schedules': result['active_schedules'],
                'pending_resets': result['pending_resets'],
                'last_reset': result['last_reset'],
                'next_reset': result['next_reset'],
                'system_status': 'pending' if result['pending_resets'] > 0 else 'active' if result['active_schedules'] > 0 else 'idle'
            }
            
        except Exception as e:
            logger.error(f"Error getting quota reset health: {e}")
            return {'error': str(e)}
            return False
        finally:
            session.close()
    
    def reset_rate_limit(self, user_id: str) -> bool:
        """
        Reset rate limit usage for a user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._Session()
            
            # Reset usage counters
            result = session.query(TokenLimits).filter(
                TokenLimits.user_id == user_id
            ).update({
                'tokens_used_in_period': 0,
                'period_start': datetime.utcnow()
            })
            
            session.commit()
            logger.info(f"Reset rate limit for user {user_id}")
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to reset rate limit: {e}")
            return False
        finally:
            session.close()
    
    def get_rate_limit_history(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get rate limit usage history for a user.
        
        Args:
            user_id: The user identifier
            days: Number of days to include in history
            
        Returns:
            Dictionary with usage history
        """
        try:
            session = self._Session()
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get usage records
            usage_records = session.query(TokenUsage).filter(
                TokenUsage.user_id == user_id,
                TokenUsage.timestamp >= start_date
            ).order_by(TokenUsage.timestamp.desc()).all()
            
            # Group by day and API endpoint
            daily_usage = {}
            endpoint_usage = {}
            
            for record in usage_records:
                day = record.timestamp.strftime('%Y-%m-%d')
                if day not in daily_usage:
                    daily_usage[day] = 0
                daily_usage[day] += record.tokens_used
                
                if record.api_endpoint not in endpoint_usage:
                    endpoint_usage[record.api_endpoint] = 0
                endpoint_usage[record.api_endpoint] += record.tokens_used
            
            return {
                'user_id': user_id,
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': datetime.utcnow().isoformat(),
                'total_tokens': sum(record.tokens_used for record in usage_records),
                'total_requests': len(usage_records),
                'daily_usage': daily_usage,
                'endpoint_usage': endpoint_usage,
                'average_tokens_per_request': (
                    sum(record.tokens_used for record in usage_records) / len(usage_records)
                ) if usage_records else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit history: {e}")
            return {
                'user_id': user_id,
                'period_days': days,
                'start_date': start_date.isoformat() if 'start_date' in locals() else None,
                'end_date': datetime.utcnow().isoformat(),
                'total_tokens': 0,
                'total_requests': 0,
                'daily_usage': {},
                'endpoint_usage': {},
                'average_tokens_per_request': 0,
                'error': str(e)
            }
        finally:
            session.close()
    
    # Token Usage Logging Methods
    
    def log_token_usage(self, user_id: str, session_id: str, tokens_used: int,
                       api_endpoint: str, priority_level: str = "Medium") -> bool:
        """
        Log token usage for a specific request.
        
        Args:
            user_id: The user identifier
            session_id: The session identifier
            tokens_used: Number of tokens consumed
            api_endpoint: API endpoint or service used
            priority_level: Priority level ('Low', 'Medium', 'High')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._Session()
            token_usage = TokenUsage(
                user_id=user_id,
                session_id=session_id,
                tokens_used=tokens_used,
                api_endpoint=api_endpoint,
                priority_level=priority_level
            )
            session.add(token_usage)
            session.commit()
            logger.info(f"Logged token usage: {tokens_used} tokens for user {user_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log token usage: {e}")
            return False
        finally:
            session.close()
    
    def log_token_usage_batch(self, records: List[Dict[str, Any]]) -> bool:
        """
        Log multiple token usage records in a single transaction.
        
        Args:
            records: List of token usage records to log
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._Session()
            for record in records:
                token_usage = TokenUsage(
                    user_id=record['user_id'],
                    session_id=record['session_id'],
                    tokens_used=record['tokens_used'],
                    api_endpoint=record['api_endpoint'],
                    priority_level=record.get('priority_level', 'Medium')
                )
                session.add(token_usage)
            session.commit()
            logger.info(f"Logged {len(records)} token usage records")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log token usage batch: {e}")
            return False
        finally:
            session.close()
    
    def get_token_usage_history(self, user_id: Optional[str] = None,
                              session_id: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieve token usage history with optional filtering.
        
        Args:
            user_id: Filter by user ID (optional)
            session_id: Filter by session ID (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of token usage records
        """
        try:
            session = self._Session()
            query = session.query(TokenUsage)
            
            # Apply filters
            if user_id:
                query = query.filter(TokenUsage.user_id == user_id)
            if session_id:
                query = query.filter(TokenUsage.session_id == session_id)
            if start_date:
                query = query.filter(TokenUsage.timestamp >= start_date)
            if end_date:
                query = query.filter(TokenUsage.timestamp <= end_date)
            
            # Order by timestamp descending and limit results
            results = query.order_by(TokenUsage.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    'id': record.id,
                    'user_id': record.user_id,
                    'session_id': record.session_id,
                    'tokens_used': record.tokens_used,
                    'api_endpoint': record.api_endpoint,
                    'priority_level': record.priority_level,
                    'timestamp': record.timestamp.isoformat()
                }
                for record in results
            ]
        except Exception as e:
            logger.error(f"Failed to get token usage history: {e}")
            return []
        finally:
            session.close()
    
    def get_token_usage_summary(self, user_id: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate token usage summary statistics.
        
        Args:
            user_id: Filter by user ID (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            session = self._Session()
            query = session.query(TokenUsage)
            
            # Apply filters
            if user_id:
                query = query.filter(TokenUsage.user_id == user_id)
            if start_date:
                query = query.filter(TokenUsage.timestamp >= start_date)
            if end_date:
                query = query.filter(TokenUsage.timestamp <= end_date)
            
            # Calculate summary statistics
            total_tokens = session.query(func.sum(TokenUsage.tokens_used)).filter(
                query.filter(TokenUsage.id == TokenUsage.id).subquery().c.id.isnot(None)
            ).scalar() or 0
            
            total_requests = query.count()
            unique_users = session.query(func.count(func.distinct(TokenUsage.user_id))).filter(
                query.filter(TokenUsage.id == TokenUsage.id).subquery().c.id.isnot(None)
            ).scalar() or 0
            
            unique_endpoints = session.query(func.count(func.distinct(TokenUsage.api_endpoint))).filter(
                query.filter(TokenUsage.id == TokenUsage.id).subquery().c.id.isnot(None)
            ).scalar() or 0
            
            average_tokens_per_request = total_tokens / total_requests if total_requests > 0 else 0
            
            # Get daily breakdown
            daily_usage = {}
            daily_results = session.query(
                func.date(TokenUsage.timestamp).label('usage_date'),
                func.sum(TokenUsage.tokens_used).label('daily_tokens'),
                func.count(TokenUsage.id).label('daily_requests')
            ).filter(
                query.filter(TokenUsage.id == TokenUsage.id).subquery().c.id.isnot(None)
            ).group_by(func.date(TokenUsage.timestamp)).all()
            
            for result in daily_results:
                daily_usage[result.usage_date.isoformat()] = {
                    'tokens': result.daily_tokens,
                    'requests': result.daily_requests
                }
            
            return {
                'total_tokens': total_tokens,
                'total_requests': total_requests,
                'unique_users': unique_users,
                'unique_endpoints': unique_endpoints,
                'average_tokens_per_request': average_tokens_per_request,
                'daily_usage': daily_usage,
                'period_start': start_date.isoformat() if start_date else None,
                'period_end': end_date.isoformat() if end_date else None
            }
        except Exception as e:
            logger.error(f"Failed to get token usage summary: {e}")
            return {
                'total_tokens': 0,
                'total_requests': 0,
                'unique_users': 0,
                'unique_endpoints': 0,
                'average_tokens_per_request': 0,
                'daily_usage': {},
                'error': str(e)
            }
        finally:
            session.close()
    
    def export_token_usage_logs(self, user_id: Optional[str] = None,
                               session_id: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               format: str = "json") -> str:
        """
        Export token usage logs in various formats.
        
        Args:
            user_id: Filter by user ID (optional)
            session_id: Filter by session ID (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            format: Export format ('json' or 'csv')
            
        Returns:
            Exported data as string
        """
        try:
            # Get the records
            records = self.get_token_usage_history(
                user_id=user_id,
                session_id=session_id,
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Reasonable limit for export
            )
            
            if format.lower() == 'json':
                return json.dumps(records, indent=2, cls=DateTimeEncoder)
            elif format.lower() == 'csv':
                import csv
                import io
                
                output = io.StringIO()
                if records:
                    writer = csv.DictWriter(output, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export token usage logs: {e}")
            return json.dumps({'error': str(e)})
    
    def cleanup_old_logs(self, retention_days: int = 90) -> Dict[str, Any]:
        """
        Clean up old token usage logs based on retention policy.
        
        Args:
            retention_days: Number of days to retain logs
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            session = self._Session()
            
            # Count records to be deleted
            count_query = session.query(TokenUsage).filter(
                TokenUsage.timestamp < cutoff_date
            )
            records_to_delete = count_query.count()
            
            # Delete old records
            deleted_count = session.query(TokenUsage).filter(
                TokenUsage.timestamp < cutoff_date
            ).delete(synchronize_session=False)
            
            session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old token usage records")
            
            return {
                'success': True,
                'records_deleted': deleted_count,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to cleanup old logs: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_deleted': 0
            }
        finally:
            session.close()
    
    def get_token_usage_analytics(self, user_id: Optional[str] = None,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get advanced analytics for token usage.
        
        Args:
            user_id: Filter by user ID (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            
        Returns:
            Dictionary with analytics data
        """
        try:
            session = self._Session()
            query = session.query(TokenUsage)
            
            # Apply filters
            if user_id:
                query = query.filter(TokenUsage.user_id == user_id)
            if start_date:
                query = query.filter(TokenUsage.timestamp >= start_date)
            if end_date:
                query = query.filter(TokenUsage.timestamp <= end_date)
            
            # Get trend analysis
            trend_data = session.query(
                func.date(TokenUsage.timestamp).label('usage_date'),
                func.sum(TokenUsage.tokens_used).label('daily_tokens')
            ).filter(
                query.filter(TokenUsage.id == TokenUsage.id).subquery().c.id.isnot(None)
            ).group_by(func.date(TokenUsage.timestamp)).order_by('usage_date').all()
            
            # Calculate trend
            if len(trend_data) >= 2:
                recent_avg = sum(t.daily_tokens for t in trend_data[-7:]) / min(7, len(trend_data))
                earlier_avg = sum(t.daily_tokens for t in trend_data[-14:-7]) / min(7, len(trend_data) - 7)
                
                if earlier_avg > 0:
                    trend_percentage = ((recent_avg - earlier_avg) / earlier_avg) * 100
                    trend_direction = "increasing" if trend_percentage > 5 else "decreasing" if trend_percentage < -5 else "stable"
                else:
                    trend_direction = "stable"
                    trend_percentage = 0
            else:
                trend_direction = "stable"
                trend_percentage = 0
            
            # Get endpoint usage distribution
            endpoint_usage = session.query(
                TokenUsage.api_endpoint,
                func.sum(TokenUsage.tokens_used).label('total_tokens'),
                func.count(TokenUsage.id).label('request_count')
            ).filter(
                query.filter(TokenUsage.id == TokenUsage.id).subquery().c.id.isnot(None)
            ).group_by(TokenUsage.api_endpoint).order_by('total_tokens DESC').all()
            
            # Get priority level distribution
            priority_usage = session.query(
                TokenUsage.priority_level,
                func.sum(TokenUsage.tokens_used).label('total_tokens'),
                func.count(TokenUsage.id).label('request_count')
            ).filter(
                query.filter(TokenUsage.id == TokenUsage.id).subquery().c.id.isnot(None)
            ).group_by(TokenUsage.priority_level).all()
            
            return {
                'trend_analysis': {
                    'direction': trend_direction,
                    'percentage_change': trend_percentage,
                    'period_days': len(trend_data)
                },
                'endpoint_distribution': [
                    {
                        'endpoint': endpoint.api_endpoint,
                        'tokens': endpoint.total_tokens,
                        'requests': endpoint.request_count
                    }
                    for endpoint in endpoint_usage
                ],
                'priority_distribution': [
                    {
                        'priority': priority.priority_level,
                        'tokens': priority.total_tokens,
                        'requests': priority.request_count
                    }
                    for priority in priority_usage
                ],
                'period_start': start_date.isoformat() if start_date else None,
                'period_end': end_date.isoformat() if end_date else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get token usage analytics: {e}")
            return {'error': str(e)}
        finally:
            session.close()

if __name__ == "__main__":
    from langchain.schema import Document as LangchainDocument
    db = PostgresDB()
    db.insert_documents(SimbaDoc(id="1", documents=[LangchainDocument(page_content="Hello, world!", metadata={"source": "test"})], metadata=MetadataType(filename="test")), "user-uuid")
    #print(db.delete_documents(["1"]))
    db.close_pool()
