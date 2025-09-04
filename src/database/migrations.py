"""
mydocs-mcp Database Migration System

This module provides a comprehensive migration system for database schema
versioning, allowing safe upgrades and rollbacks while maintaining data integrity.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import aiosqlite

from .connection import DatabaseConnection
from .models import DatabaseSchema


class Migration(ABC):
    """
    Abstract base class for database migrations.
    
    Each migration must implement the upgrade and rollback methods
    to handle schema changes safely.
    """
    
    def __init__(self, version: int, description: str):
        """
        Initialize migration.
        
        Args:
            version: Migration version number
            description: Human-readable description of changes
        """
        self.version = version
        self.description = description
        self.timestamp = datetime.now()
    
    @abstractmethod
    async def upgrade(self, connection: aiosqlite.Connection) -> None:
        """
        Apply migration (upgrade database schema).
        
        Args:
            connection: Database connection to apply migration to
        """
        pass
    
    @abstractmethod
    async def rollback(self, connection: aiosqlite.Connection) -> None:
        """
        Rollback migration (downgrade database schema).
        
        Args:
            connection: Database connection to rollback migration from
        """
        pass
    
    def __str__(self) -> str:
        return f"Migration {self.version}: {self.description}"


class Migration001_Initial(Migration):
    """
    Initial database schema migration.
    
    Creates all core tables, indexes, and triggers for the mydocs-mcp system.
    """
    
    def __init__(self):
        super().__init__(1, "Create initial database schema")
    
    async def upgrade(self, connection: aiosqlite.Connection) -> None:
        """Create initial schema with all tables and indexes."""
        # Apply performance pragmas
        await DatabaseSchema.apply_performance_pragmas(connection)
        
        # Create all core tables
        await connection.execute(DatabaseSchema.CREATE_DOCUMENTS_TABLE)
        await connection.execute(DatabaseSchema.CREATE_DOCUMENT_METADATA_TABLE)
        await connection.execute(DatabaseSchema.CREATE_SEARCH_INDEX_TABLE)
        await connection.execute(DatabaseSchema.CREATE_SEARCH_CACHE_TABLE)
        
        # Create FTS table
        await connection.execute(DatabaseSchema.CREATE_FTS_TABLE)
        
        # Create all indexes for performance
        for index_sql in DatabaseSchema.CREATE_INDEXES:
            await connection.execute(index_sql)
        
        # Create FTS triggers
        for trigger_sql in DatabaseSchema.CREATE_FTS_TRIGGERS:
            await connection.execute(trigger_sql)
        
        await connection.commit()
    
    async def rollback(self, connection: aiosqlite.Connection) -> None:
        """Drop all tables and objects created in upgrade."""
        # Drop FTS triggers
        triggers = [
            "documents_fts_insert",
            "documents_fts_update", 
            "documents_fts_delete"
        ]
        
        for trigger in triggers:
            await connection.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        
        # Drop FTS table
        await connection.execute("DROP TABLE IF EXISTS documents_fts")
        
        # Drop core tables (foreign keys will handle cascades)
        tables = [
            "search_cache",
            "search_index",
            "document_metadata",
            "documents"
        ]
        
        for table in tables:
            await connection.execute(f"DROP TABLE IF EXISTS {table}")
        
        await connection.commit()


class Migration002_AddDocumentTags(Migration):
    """
    Example future migration: Add document tags table.
    
    This shows how to add new features while maintaining backward compatibility.
    """
    
    def __init__(self):
        super().__init__(2, "Add document tags support")
    
    async def upgrade(self, connection: aiosqlite.Connection) -> None:
        """Add document_tags table."""
        create_tags_table = """
        CREATE TABLE IF NOT EXISTS document_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Foreign key constraint
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            
            -- Unique constraint
            UNIQUE (document_id, tag)
        );
        """
        
        create_tags_index = """
        CREATE INDEX IF NOT EXISTS idx_document_tags_tag ON document_tags(tag);
        """
        
        await connection.execute(create_tags_table)
        await connection.execute(create_tags_index)
        await connection.commit()
    
    async def rollback(self, connection: aiosqlite.Connection) -> None:
        """Remove document_tags table."""
        await connection.execute("DROP TABLE IF EXISTS document_tags")
        await connection.commit()


class MigrationManager:
    """
    Database migration management system.
    
    Handles migration discovery, execution, and rollback operations
    with proper error handling and logging.
    """
    
    def __init__(self, connection: DatabaseConnection, logger: Optional[logging.Logger] = None):
        """
        Initialize migration manager.
        
        Args:
            connection: Database connection instance
            logger: Optional logger instance
        """
        self.db = connection
        self.logger = logger or logging.getLogger(__name__)
        self._migrations: Dict[int, Migration] = {}
        
        # Register built-in migrations
        self._register_built_in_migrations()
    
    def _register_built_in_migrations(self) -> None:
        """Register all built-in migrations."""
        migrations = [
            Migration001_Initial(),
            Migration002_AddDocumentTags(),
        ]
        
        for migration in migrations:
            self.register_migration(migration)
    
    def register_migration(self, migration: Migration) -> None:
        """
        Register a migration.
        
        Args:
            migration: Migration instance to register
        """
        if migration.version in self._migrations:
            raise ValueError(f"Migration version {migration.version} already registered")
        
        self._migrations[migration.version] = migration
        self.logger.debug(f"Registered migration: {migration}")
    
    async def get_current_version(self) -> int:
        """
        Get current database schema version.
        
        Returns:
            Current schema version number
        """
        try:
            connection = await self.db.connect()
            return await DatabaseSchema.get_schema_version(connection)
        except Exception as e:
            self.logger.error(f"Failed to get current version: {e}")
            return 0
    
    async def get_latest_version(self) -> int:
        """
        Get latest available migration version.
        
        Returns:
            Latest migration version number
        """
        if not self._migrations:
            return 0
        
        return max(self._migrations.keys())
    
    async def get_pending_migrations(self) -> List[Migration]:
        """
        Get list of pending migrations.
        
        Returns:
            List of migrations that need to be applied
        """
        current_version = await self.get_current_version()
        
        pending = []
        for version in sorted(self._migrations.keys()):
            if version > current_version:
                pending.append(self._migrations[version])
        
        return pending
    
    async def create_migration_table(self) -> None:
        """Create migration tracking table if it doesn't exist."""
        sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            rollback_sql TEXT
        );
        """
        
        try:
            connection = await self.db.connect()
            await connection.execute(sql)
            await connection.commit()
            self.logger.debug("Migration tracking table created/verified")
            
        except Exception as e:
            self.logger.error(f"Failed to create migration table: {e}")
            raise
    
    async def apply_migration(self, migration: Migration) -> bool:
        """
        Apply a single migration.
        
        Args:
            migration: Migration to apply
            
        Returns:
            True if migration applied successfully, False otherwise
        """
        try:
            connection = await self.db.connect()
            
            # Start transaction
            await connection.execute("BEGIN")
            
            self.logger.info(f"Applying migration: {migration}")
            
            # Apply the migration
            await migration.upgrade(connection)
            
            # Record migration in tracking table
            await connection.execute(
                """
                INSERT OR REPLACE INTO schema_migrations (version, description, applied_at)
                VALUES (?, ?, ?)
                """,
                (migration.version, migration.description, datetime.now())
            )
            
            # Update schema version
            await DatabaseSchema.set_schema_version(connection, migration.version)
            
            # Commit transaction
            await connection.commit()
            
            self.logger.info(f"Successfully applied migration: {migration}")
            return True
            
        except Exception as e:
            # Rollback on error
            try:
                await connection.rollback()
            except:
                pass
            
            self.logger.error(f"Failed to apply migration {migration}: {e}")
            return False
    
    async def rollback_migration(self, migration: Migration) -> bool:
        """
        Rollback a single migration.
        
        Args:
            migration: Migration to rollback
            
        Returns:
            True if migration rolled back successfully, False otherwise
        """
        try:
            connection = await self.db.connect()
            
            # Start transaction
            await connection.execute("BEGIN")
            
            self.logger.info(f"Rolling back migration: {migration}")
            
            # Rollback the migration
            await migration.rollback(connection)
            
            # Remove migration record
            await connection.execute(
                "DELETE FROM schema_migrations WHERE version = ?",
                (migration.version,)
            )
            
            # Update schema version to previous version
            previous_version = migration.version - 1
            await DatabaseSchema.set_schema_version(connection, previous_version)
            
            # Commit transaction
            await connection.commit()
            
            self.logger.info(f"Successfully rolled back migration: {migration}")
            return True
            
        except Exception as e:
            # Rollback on error
            try:
                await connection.rollback()
            except:
                pass
            
            self.logger.error(f"Failed to rollback migration {migration}: {e}")
            return False
    
    async def migrate_to_latest(self) -> bool:
        """
        Migrate database to the latest version.
        
        Returns:
            True if all migrations applied successfully, False otherwise
        """
        # Ensure migration table exists
        await self.create_migration_table()
        
        pending_migrations = await self.get_pending_migrations()
        
        if not pending_migrations:
            self.logger.info("Database is already up to date")
            return True
        
        self.logger.info(f"Applying {len(pending_migrations)} pending migrations")
        
        # Apply migrations in order
        for migration in pending_migrations:
            success = await self.apply_migration(migration)
            if not success:
                self.logger.error(f"Migration failed, stopping at version {migration.version}")
                return False
        
        self.logger.info("All migrations applied successfully")
        return True
    
    async def migrate_to_version(self, target_version: int) -> bool:
        """
        Migrate database to a specific version.
        
        Args:
            target_version: Target schema version
            
        Returns:
            True if migration successful, False otherwise
        """
        current_version = await self.get_current_version()
        
        if current_version == target_version:
            self.logger.info(f"Database is already at version {target_version}")
            return True
        
        if target_version > current_version:
            # Upgrade path
            for version in sorted(self._migrations.keys()):
                if current_version < version <= target_version:
                    migration = self._migrations[version]
                    success = await self.apply_migration(migration)
                    if not success:
                        return False
            
        else:
            # Downgrade path
            for version in sorted(self._migrations.keys(), reverse=True):
                if target_version < version <= current_version:
                    migration = self._migrations[version]
                    success = await self.rollback_migration(migration)
                    if not success:
                        return False
        
        self.logger.info(f"Successfully migrated to version {target_version}")
        return True
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """
        Get comprehensive migration status information.
        
        Returns:
            Dictionary with migration status details
        """
        current_version = await self.get_current_version()
        latest_version = self.get_latest_version()
        pending_migrations = await self.get_pending_migrations()
        
        # Get applied migrations from database
        try:
            connection = await self.db.connect()
            rows = await self.db.fetch_all(
                "SELECT version, description, applied_at FROM schema_migrations ORDER BY version"
            )
            applied_migrations = [
                {
                    "version": row[0],
                    "description": row[1],
                    "applied_at": row[2]
                }
                for row in rows
            ]
        except Exception:
            applied_migrations = []
        
        return {
            "current_version": current_version,
            "latest_version": latest_version,
            "is_up_to_date": current_version >= latest_version,
            "pending_count": len(pending_migrations),
            "pending_migrations": [
                {
                    "version": m.version,
                    "description": m.description
                }
                for m in pending_migrations
            ],
            "applied_migrations": applied_migrations,
            "available_migrations": [
                {
                    "version": version,
                    "description": migration.description
                }
                for version, migration in sorted(self._migrations.items())
            ]
        }


# Utility functions for external use
async def initialize_database(database_path: str, logger: Optional[logging.Logger] = None) -> bool:
    """
    Initialize database with latest schema.
    
    Args:
        database_path: Path to database file
        logger: Optional logger instance
        
    Returns:
        True if initialization successful, False otherwise
    """
    from .connection import get_database_connection
    
    try:
        # Get database connection
        db_connection = await get_database_connection(database_path, logger=logger)
        
        # Create migration manager and apply migrations
        migration_manager = MigrationManager(db_connection, logger)
        success = await migration_manager.migrate_to_latest()
        
        if success:
            if logger:
                logger.info(f"Database initialized successfully: {database_path}")
        else:
            if logger:
                logger.error(f"Database initialization failed: {database_path}")
        
        return success
        
    except Exception as e:
        if logger:
            logger.error(f"Database initialization error: {e}")
        return False


async def get_database_status(database_path: str, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Get comprehensive database status.
    
    Args:
        database_path: Path to database file
        logger: Optional logger instance
        
    Returns:
        Database status information
    """
    from .connection import get_database_connection
    
    try:
        # Get database connection
        db_connection = await get_database_connection(database_path, logger=logger)
        
        # Get migration status
        migration_manager = MigrationManager(db_connection, logger)
        migration_status = await migration_manager.get_migration_status()
        
        # Get connection info
        connection_info = await db_connection.get_connection_info()
        
        return {
            "connection": connection_info,
            "migrations": migration_status
        }
        
    except Exception as e:
        return {
            "connection": {"status": "error", "error": str(e)},
            "migrations": {"error": str(e)}
        }