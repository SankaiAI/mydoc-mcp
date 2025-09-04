"""
Main file system watcher for mydocs-mcp.

This module provides the primary FileWatcher class that monitors file system
changes and automatically triggers document indexing operations.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Awaitable
from datetime import datetime
from watchdog.observers import Observer

from .config import WatcherConfig, create_watcher_config, load_watcher_config_from_env
from .event_handler import AsyncFileSystemEventHandler, FileEvent
from ..tools.indexDocument import IndexDocumentTool
from ..database.database_manager import DocumentManager


class FileWatcher:
    """
    File system watcher that monitors directories for document changes.
    
    This class coordinates file system monitoring with document indexing,
    providing automatic reindexing of changed documents and handling
    file operations like creation, modification, deletion, and moves.
    """
    
    def __init__(
        self,
        config: Optional[WatcherConfig] = None,
        index_tool: Optional[IndexDocumentTool] = None,
        database_manager: Optional[DocumentManager] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the file watcher.
        
        Args:
            config: Watcher configuration (uses defaults if None)
            index_tool: Tool for document indexing (creates if None)
            database_manager: Database manager instance
            logger: Logger instance (creates if None)
        """
        self.config = config or load_watcher_config_from_env()
        self.logger = logger or logging.getLogger(__name__)
        
        # Core components
        self.database_manager = database_manager
        self.index_tool = index_tool
        
        # Watchdog components
        self.observer = Observer()
        self.event_handler: Optional[AsyncFileSystemEventHandler] = None
        
        # State management
        self.is_watching = False
        self.start_time: Optional[datetime] = None
        self.watch_handles = []
        
        # Statistics
        self.stats = {
            'files_indexed': 0,
            'files_updated': 0,
            'files_deleted': 0,
            'files_moved': 0,
            'indexing_errors': 0,
            'total_events_processed': 0
        }
        
        self.logger.info(f"FileWatcher initialized with {len(self.config.watch_directories)} directories")
    
    async def start(self) -> bool:
        """
        Start the file system watcher.
        
        Returns:
            True if watcher started successfully
        """
        if self.is_watching:
            self.logger.warning("File watcher is already running")
            return True
        
        try:
            # Validate configuration
            if not self.config.watch_directories:
                self.logger.error("No watch directories configured")
                return False
            
            # Initialize event handler
            self.event_handler = AsyncFileSystemEventHandler(
                config=self.config,
                event_callback=self._handle_file_event,
                logger=self.logger
            )
            
            # Set up directory watches
            watch_count = 0
            for directory in self.config.watch_directories:
                try:
                    watch_handle = self.observer.schedule(
                        self.event_handler,
                        directory,
                        recursive=self.config.enable_recursive
                    )
                    self.watch_handles.append(watch_handle)
                    watch_count += 1
                    self.logger.info(f"Watching directory: {directory} (recursive={self.config.enable_recursive})")
                    
                except Exception as e:
                    self.logger.error(f"Failed to watch directory {directory}: {e}")
            
            if watch_count == 0:
                self.logger.error("Failed to set up any directory watches")
                return False
            
            # Start the observer
            self.observer.start()
            self.is_watching = True
            self.start_time = datetime.now()
            
            self.logger.info(f"File watcher started successfully, monitoring {watch_count} directories")
            
            # Log configuration summary
            summary = self.config.get_watch_summary()
            self.logger.info(f"Watch configuration: {summary}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start file watcher: {e}", exc_info=True)
            return False
    
    async def stop(self) -> bool:
        """
        Stop the file system watcher.
        
        Returns:
            True if watcher stopped successfully
        """
        if not self.is_watching:
            self.logger.warning("File watcher is not running")
            return True
        
        try:
            # Stop the observer
            self.observer.stop()
            
            # Wait for observer to finish
            self.observer.join(timeout=5.0)
            
            # Clean up event handler
            if self.event_handler:
                await self.event_handler.flush_pending_events()
                await self.event_handler.cleanup()
            
            # Update state
            self.is_watching = False
            self.watch_handles.clear()
            
            # Log final statistics
            runtime = datetime.now() - self.start_time if self.start_time else None
            self.logger.info(f"File watcher stopped. Runtime: {runtime}")
            self.logger.info(f"Final stats: {self.get_statistics()}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping file watcher: {e}", exc_info=True)
            return False
    
    async def _handle_file_event(self, file_event: FileEvent):
        """
        Handle a file system event by performing appropriate action.
        
        Args:
            file_event: File event to handle
        """
        start_time = time.time()
        action_taken = None
        
        try:
            self.logger.debug(f"Handling {file_event.event_type} event for: {file_event.file_path}")
            
            if file_event.event_type == 'created':
                action_taken = await self._handle_file_created(file_event)
            elif file_event.event_type == 'modified':
                action_taken = await self._handle_file_modified(file_event)
            elif file_event.event_type == 'deleted':
                action_taken = await self._handle_file_deleted(file_event)
            elif file_event.event_type == 'moved':
                action_taken = await self._handle_file_moved(file_event)
            else:
                self.logger.warning(f"Unknown event type: {file_event.event_type}")
                return
            
            # Update statistics
            if action_taken:
                self.stats['total_events_processed'] += 1
                
                if action_taken == 'indexed':
                    self.stats['files_indexed'] += 1
                elif action_taken == 'updated':
                    self.stats['files_updated'] += 1
                elif action_taken == 'deleted':
                    self.stats['files_deleted'] += 1
                elif action_taken == 'moved':
                    self.stats['files_moved'] += 1
            
            processing_time = (time.time() - start_time) * 1000
            self.logger.debug(f"Event processed in {processing_time:.1f}ms, action: {action_taken}")
            
        except Exception as e:
            self.stats['indexing_errors'] += 1
            self.logger.error(f"Error handling file event {file_event.file_path}: {e}", exc_info=True)
    
    async def _handle_file_created(self, file_event: FileEvent) -> Optional[str]:
        """
        Handle file creation event.
        
        Args:
            file_event: File creation event
            
        Returns:
            Action taken ('indexed', 'skipped', etc.)
        """
        try:
            # Index the new file
            result = await self._index_document(file_event.file_path)
            return 'indexed' if result else 'skipped'
            
        except Exception as e:
            self.logger.error(f"Error indexing created file {file_event.file_path}: {e}")
            return None
    
    async def _handle_file_modified(self, file_event: FileEvent) -> Optional[str]:
        """
        Handle file modification event.
        
        Args:
            file_event: File modification event
            
        Returns:
            Action taken ('updated', 'indexed', 'skipped', etc.)
        """
        try:
            # Check if file is already indexed
            if self.database_manager:
                existing_doc = await self.database_manager.doc_queries.get_document_by_path(
                    file_event.file_path
                )
                
                if existing_doc:
                    # File exists in database, update it
                    result = await self._index_document(file_event.file_path, force_reindex=True)
                    return 'updated' if result else 'skipped'
                else:
                    # File not in database, index it
                    result = await self._index_document(file_event.file_path)
                    return 'indexed' if result else 'skipped'
            else:
                # No database manager, just index
                result = await self._index_document(file_event.file_path)
                return 'indexed' if result else 'skipped'
                
        except Exception as e:
            self.logger.error(f"Error handling modified file {file_event.file_path}: {e}")
            return None
    
    async def _handle_file_deleted(self, file_event: FileEvent) -> Optional[str]:
        """
        Handle file deletion event.
        
        Args:
            file_event: File deletion event
            
        Returns:
            Action taken ('deleted', 'not_found', etc.)
        """
        try:
            if not self.database_manager:
                return 'skipped'
            
            # Remove from database
            result = await self.database_manager.doc_queries.delete_document_by_path(
                file_event.file_path
            )
            
            if result:
                self.logger.info(f"Removed deleted file from database: {file_event.file_path}")
                return 'deleted'
            else:
                self.logger.debug(f"Deleted file was not in database: {file_event.file_path}")
                return 'not_found'
                
        except Exception as e:
            self.logger.error(f"Error handling deleted file {file_event.file_path}: {e}")
            return None
    
    async def _handle_file_moved(self, file_event: FileEvent) -> Optional[str]:
        """
        Handle file move event.
        
        Args:
            file_event: File move event
            
        Returns:
            Action taken ('moved', 'indexed', etc.)
        """
        try:
            if not self.database_manager or not file_event.old_path:
                # Fallback to treating as new file
                result = await self._index_document(file_event.file_path)
                return 'indexed' if result else 'skipped'
            
            # Check if old file was indexed
            existing_doc = await self.database_manager.doc_queries.get_document_by_path(
                file_event.old_path
            )
            
            if existing_doc:
                # Update the path in database
                result = await self.database_manager.doc_queries.update_document_path(
                    existing_doc.id,
                    file_event.file_path
                )
                
                if result:
                    # Reindex with new path to update metadata
                    await self._index_document(file_event.file_path, force_reindex=True)
                    self.logger.info(f"Updated moved file path: {file_event.old_path} → {file_event.file_path}")
                    return 'moved'
                else:
                    # Update failed, treat as new file
                    result = await self._index_document(file_event.file_path)
                    return 'indexed' if result else 'skipped'
            else:
                # Old file wasn't indexed, treat as new
                result = await self._index_document(file_event.file_path)
                return 'indexed' if result else 'skipped'
                
        except Exception as e:
            self.logger.error(f"Error handling moved file {file_event.old_path} → {file_event.file_path}: {e}")
            return None
    
    async def _index_document(self, file_path: str, force_reindex: bool = False) -> bool:
        """
        Index a document using the index tool.
        
        Args:
            file_path: Path to document to index
            force_reindex: Whether to force reindexing
            
        Returns:
            True if indexing succeeded
        """
        try:
            if not self.index_tool:
                self.logger.error("No index tool available for document indexing")
                return False
            
            # Prepare parameters
            params = {
                'file_path': file_path,
                'force_reindex': force_reindex
            }
            
            # Execute indexing
            result = await self.index_tool._execute_tool(params)
            
            if result.is_success:
                self.logger.debug(f"Successfully indexed: {file_path}")
                return True
            else:
                self.logger.warning(f"Failed to index {file_path}: {result.error_message}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error indexing document {file_path}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get watcher statistics and status.
        
        Returns:
            Dictionary with watcher statistics
        """
        base_stats = {
            'is_watching': self.is_watching,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'runtime_seconds': (
                (datetime.now() - self.start_time).total_seconds()
                if self.start_time else 0
            ),
            'watched_directories': len(self.config.watch_directories),
            'directories': self.config.watch_directories,
            'configuration': self.config.get_watch_summary(),
            'processing_stats': self.stats.copy()
        }
        
        # Add event handler statistics if available
        if self.event_handler:
            base_stats['event_handler_stats'] = self.event_handler.get_event_statistics()
        
        return base_stats
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the watcher.
        
        Returns:
            Dictionary with health information
        """
        is_healthy = True
        issues = []
        
        # Check if watcher is running
        if not self.is_watching:
            is_healthy = False
            issues.append("Watcher is not running")
        
        # Check observer status
        if self.is_watching and not self.observer.is_alive():
            is_healthy = False
            issues.append("Observer thread is not alive")
        
        # Check error rate
        total_processed = self.stats['total_events_processed']
        error_rate = (
            self.stats['indexing_errors'] / total_processed
            if total_processed > 0 else 0
        )
        
        if error_rate > 0.1:  # More than 10% error rate
            is_healthy = False
            issues.append(f"High error rate: {error_rate:.1%}")
        
        # Check watch directories
        invalid_dirs = []
        for directory in self.config.watch_directories:
            if not Path(directory).exists():
                invalid_dirs.append(directory)
        
        if invalid_dirs:
            is_healthy = False
            issues.append(f"Invalid directories: {invalid_dirs}")
        
        return {
            'healthy': is_healthy,
            'issues': issues,
            'error_rate': error_rate,
            'uptime_seconds': (
                (datetime.now() - self.start_time).total_seconds()
                if self.start_time else 0
            )
        }
    
    async def manual_scan(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform manual scan of a directory for indexing.
        
        Args:
            directory: Directory to scan (scans all watched dirs if None)
            
        Returns:
            Dictionary with scan results
        """
        scan_dirs = [directory] if directory else self.config.watch_directories
        results = {
            'scanned_directories': 0,
            'files_found': 0,
            'files_indexed': 0,
            'files_updated': 0,
            'errors': 0,
            'scan_time_seconds': 0
        }
        
        start_time = time.time()
        
        try:
            for scan_dir in scan_dirs:
                dir_path = Path(scan_dir)
                if not dir_path.exists():
                    self.logger.warning(f"Scan directory does not exist: {scan_dir}")
                    continue
                
                results['scanned_directories'] += 1
                
                # Find all matching files
                pattern = "**/*" if self.config.enable_recursive else "*"
                for file_path in dir_path.glob(pattern):
                    if not file_path.is_file():
                        continue
                    
                    if not self.config.should_watch_file(file_path):
                        continue
                    
                    results['files_found'] += 1
                    
                    try:
                        # Check if needs indexing
                        needs_indexing = True
                        if self.database_manager:
                            existing_doc = await self.database_manager.doc_queries.get_document_by_path(
                                str(file_path)
                            )
                            if existing_doc:
                                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                                needs_indexing = file_mtime > existing_doc.modified_at
                        
                        if needs_indexing:
                            success = await self._index_document(str(file_path), force_reindex=True)
                            if success:
                                if existing_doc:
                                    results['files_updated'] += 1
                                else:
                                    results['files_indexed'] += 1
                            else:
                                results['errors'] += 1
                                
                    except Exception as e:
                        results['errors'] += 1
                        self.logger.error(f"Error scanning file {file_path}: {e}")
            
            results['scan_time_seconds'] = time.time() - start_time
            self.logger.info(f"Manual scan completed: {results}")
            
            return results
            
        except Exception as e:
            results['errors'] += 1
            results['scan_time_seconds'] = time.time() - start_time
            self.logger.error(f"Error during manual scan: {e}")
            return results