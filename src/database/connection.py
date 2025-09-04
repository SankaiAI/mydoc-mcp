"""
mydocs-mcp Database Connection Management

This module provides async database connection management with performance
optimization, connection pooling, and proper resource cleanup for SQLite.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncContextManager, Optional, Dict, Any
import aiosqlite

from .models import DatabaseSchema


class DatabaseConnection:
    """
    Async SQLite database connection wrapper with performance optimization.
    
    This class provides a high-level interface for database operations with
    automatic connection management, performance monitoring, and error handling.
    """
    
    def __init__(self, database_path: str, logger: Optional[logging.Logger] = None):
        """
        Initialize database connection.
        
        Args:
            database_path: Path to SQLite database file
            logger: Optional logger instance
        """
        self.database_path = Path(database_path)
        self.logger = logger or logging.getLogger(__name__)
        self._connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
        self._is_initialized = False
        
    async def connect(self) -> aiosqlite.Connection:
        """
        Establish database connection with performance optimization.
        
        Returns:
            Active aiosqlite connection
        """
        async with self._lock:
            if self._connection is None:
                # Ensure database directory exists
                self.database_path.parent.mkdir(parents=True, exist_ok=True)
                
                self.logger.debug(f"Connecting to database: {self.database_path}")
                
                # Create connection with optimizations
                self._connection = await aiosqlite.connect(
                    str(self.database_path),
                    timeout=30.0,  # 30 second timeout
                    isolation_level=None,  # Auto-commit disabled for transactions
                )
                
                # Apply performance pragmas
                await DatabaseSchema.apply_performance_pragmas(self._connection)
                
                # Initialize schema if needed
                if not self._is_initialized:
                    await self._initialize_schema()
                    self._is_initialized = True
                
                self.logger.info(f"Database connection established: {self.database_path}")
        
        return self._connection
    
    async def _initialize_schema(self) -> None:
        """Initialize database schema if not exists."""
        current_version = await DatabaseSchema.get_schema_version(self._connection)
        
        if current_version < DatabaseSchema.SCHEMA_VERSION:
            self.logger.info(f"Initializing database schema (v{current_version} -> v{DatabaseSchema.SCHEMA_VERSION})")
            await DatabaseSchema.initialize_schema(self._connection)
            await DatabaseSchema.set_schema_version(self._connection, DatabaseSchema.SCHEMA_VERSION)
            self.logger.info("Database schema initialization completed")
    
    async def close(self) -> None:
        """Close database connection."""
        async with self._lock:
            if self._connection:
                await self._connection.close()
                self._connection = None
                self.logger.debug("Database connection closed")
    
    async def execute(self, sql: str, parameters: Optional[tuple] = None) -> aiosqlite.Cursor:
        """
        Execute SQL statement.
        
        Args:
            sql: SQL statement
            parameters: Optional parameters for prepared statement
            
        Returns:
            Cursor with query results
        """
        connection = await self.connect()
        return await connection.execute(sql, parameters or ())
    
    async def executemany(self, sql: str, parameters: list) -> aiosqlite.Cursor:
        """
        Execute SQL statement with multiple parameter sets.
        
        Args:
            sql: SQL statement
            parameters: List of parameter tuples
            
        Returns:
            Cursor with query results
        """
        connection = await self.connect()
        return await connection.executemany(sql, parameters)
    
    async def commit(self) -> None:
        """Commit current transaction."""
        if self._connection:
            await self._connection.commit()
    
    async def rollback(self) -> None:
        """Rollback current transaction."""
        if self._connection:
            await self._connection.rollback()
    
    @asynccontextmanager
    async def transaction(self) -> AsyncContextManager[aiosqlite.Connection]:
        """
        Context manager for database transactions with automatic rollback on error.
        
        Usage:
            async with db.transaction() as conn:
                await conn.execute("INSERT ...")
                await conn.execute("UPDATE ...")
                # Auto-commits on success, rolls back on exception
        """
        connection = await self.connect()
        
        # Start transaction
        await connection.execute("BEGIN")
        
        try:
            yield connection
            # Commit on successful completion
            await connection.commit()
            
        except Exception as e:
            # Rollback on any exception
            await connection.rollback()
            self.logger.error(f"Transaction rolled back due to error: {e}")
            raise
    
    async def fetch_one(self, sql: str, parameters: Optional[tuple] = None) -> Optional[tuple]:
        """
        Fetch single row from query.
        
        Args:
            sql: SQL query
            parameters: Optional parameters
            
        Returns:
            Single row tuple or None
        """
        async with await self.execute(sql, parameters) as cursor:
            return await cursor.fetchone()
    
    async def fetch_all(self, sql: str, parameters: Optional[tuple] = None) -> list:
        """
        Fetch all rows from query.
        
        Args:
            sql: SQL query
            parameters: Optional parameters
            
        Returns:
            List of row tuples
        """
        async with await self.execute(sql, parameters) as cursor:
            return await cursor.fetchall()
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information for diagnostics."""
        if not self._connection:
            return {"status": "disconnected"}
        
        try:
            # Get database info
            pragma_info = {}
            
            for pragma in ["cache_size", "journal_mode", "synchronous", "foreign_keys"]:
                async with self._connection.execute(f"PRAGMA {pragma}") as cursor:
                    result = await cursor.fetchone()
                    pragma_info[pragma] = result[0] if result else None
            
            # Get table count
            async with self._connection.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ) as cursor:
                table_count = (await cursor.fetchone())[0]
            
            return {
                "status": "connected",
                "database_path": str(self.database_path),
                "database_size": self.database_path.stat().st_size if self.database_path.exists() else 0,
                "table_count": table_count,
                "pragma_settings": pragma_info,
                "is_initialized": self._is_initialized
            }
            
        except Exception as e:
            self.logger.error(f"Error getting connection info: {e}")
            return {"status": "error", "error": str(e)}


class ConnectionManager:
    """
    Connection pool manager for handling multiple database connections.
    
    This class provides connection pooling and lifecycle management for
    improved performance and resource utilization.
    """
    
    def __init__(self, max_connections: int = 10, logger: Optional[logging.Logger] = None):
        """
        Initialize connection manager.
        
        Args:
            max_connections: Maximum number of concurrent connections
            logger: Optional logger instance
        """
        self.max_connections = max_connections
        self.logger = logger or logging.getLogger(__name__)
        self._connections: Dict[str, DatabaseConnection] = {}
        self._connection_semaphore = asyncio.Semaphore(max_connections)
        self._lock = asyncio.Lock()
    
    async def get_connection(self, database_path: str) -> DatabaseConnection:
        """
        Get database connection from pool.
        
        Args:
            database_path: Path to database file
            
        Returns:
            DatabaseConnection instance
        """
        async with self._lock:
            if database_path not in self._connections:
                self.logger.debug(f"Creating new connection for: {database_path}")
                self._connections[database_path] = DatabaseConnection(database_path, self.logger)
        
        return self._connections[database_path]
    
    async def close_all(self) -> None:
        """Close all managed connections."""
        async with self._lock:
            close_tasks = [
                conn.close() for conn in self._connections.values()
            ]
            
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
            
            self._connections.clear()
            self.logger.info("All database connections closed")
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status."""
        return {
            "total_connections": len(self._connections),
            "max_connections": self.max_connections,
            "available_slots": self._connection_semaphore._value,
            "connections": {
                path: await conn.get_connection_info() 
                for path, conn in self._connections.items()
            }
        }


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


async def get_database_connection(
    database_path: str,
    max_connections: int = 10,
    logger: Optional[logging.Logger] = None
) -> DatabaseConnection:
    """
    Get database connection from global connection manager.
    
    Args:
        database_path: Path to database file
        max_connections: Maximum number of concurrent connections
        logger: Optional logger instance
        
    Returns:
        DatabaseConnection instance
    """
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = ConnectionManager(max_connections, logger)
    
    return await _connection_manager.get_connection(database_path)


async def close_all_connections() -> None:
    """Close all connections in global connection manager."""
    global _connection_manager
    
    if _connection_manager:
        await _connection_manager.close_all()
        _connection_manager = None


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class ConnectionError(DatabaseError):
    """Exception raised for connection-related errors."""
    pass


class QueryError(DatabaseError):
    """Exception raised for query execution errors."""
    pass


class TransactionError(DatabaseError):
    """Exception raised for transaction-related errors."""
    pass


# Performance monitoring decorator
def monitor_query_performance(func):
    """Decorator to monitor database query performance."""
    import time
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log slow queries (>200ms)
            if execution_time > 200:
                logger = logging.getLogger(__name__)
                logger.warning(f"Slow query detected: {func.__name__} took {execution_time:.2f}ms")
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger = logging.getLogger(__name__)
            logger.error(f"Query failed: {func.__name__} after {execution_time:.2f}ms - {e}")
            raise
    
    return wrapper