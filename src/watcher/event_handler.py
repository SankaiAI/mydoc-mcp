"""
File system event handler for mydocs-mcp.

This module processes file system events and triggers appropriate actions
such as document indexing, updating, or removal based on file changes.
"""

import asyncio
import time
import logging
from pathlib import Path
from typing import Dict, Set, Optional, Callable, Awaitable, Any
from dataclasses import dataclass, field
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileDeletedEvent, FileMovedEvent

from .config import WatcherConfig


@dataclass
class FileEvent:
    """
    Represents a processed file system event.
    
    Attributes:
        event_type: Type of event (created, modified, deleted, moved)
        file_path: Path to the affected file
        old_path: Previous path for moved files
        timestamp: Time when event occurred
        is_directory: Whether the event concerns a directory
    """
    event_type: str
    file_path: str
    old_path: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    is_directory: bool = False


class AsyncFileSystemEventHandler(FileSystemEventHandler):
    """
    Async-compatible file system event handler.
    
    This handler processes file system events, applies filtering based on
    configuration, and triggers async callbacks for document processing.
    """
    
    def __init__(
        self,
        config: WatcherConfig,
        event_callback: Callable[[FileEvent], Awaitable[None]],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the event handler.
        
        Args:
            config: Watcher configuration
            event_callback: Async callback for processing events
            logger: Optional logger instance
        """
        super().__init__()
        self.config = config
        self.event_callback = event_callback
        self.logger = logger or logging.getLogger(__name__)
        
        # Debouncing state
        self._pending_events: Dict[str, FileEvent] = {}
        self._debounce_tasks: Dict[str, asyncio.Task] = {}
        
        # Batch processing state
        self._batch_events: Dict[str, FileEvent] = {}
        self._batch_task: Optional[asyncio.Task] = None
        
        # Event statistics
        self._event_counts = {
            'created': 0,
            'modified': 0,
            'deleted': 0,
            'moved': 0,
            'filtered': 0,
            'processed': 0
        }
        
        self.logger.info("File system event handler initialized")
    
    def on_created(self, event: FileCreatedEvent):
        """Handle file/directory creation events."""
        if event.is_directory:
            return
            
        file_event = FileEvent(
            event_type='created',
            file_path=event.src_path,
            is_directory=event.is_directory
        )
        self._queue_event(file_event)
        self._event_counts['created'] += 1
    
    def on_modified(self, event: FileModifiedEvent):
        """Handle file/directory modification events."""
        if event.is_directory:
            return
            
        file_event = FileEvent(
            event_type='modified',
            file_path=event.src_path,
            is_directory=event.is_directory
        )
        self._queue_event(file_event)
        self._event_counts['modified'] += 1
    
    def on_deleted(self, event: FileDeletedEvent):
        """Handle file/directory deletion events."""
        if event.is_directory:
            return
            
        file_event = FileEvent(
            event_type='deleted',
            file_path=event.src_path,
            is_directory=event.is_directory
        )
        self._queue_event(file_event)
        self._event_counts['deleted'] += 1
    
    def on_moved(self, event: FileMovedEvent):
        """Handle file/directory move events."""
        if event.is_directory:
            return
            
        file_event = FileEvent(
            event_type='moved',
            file_path=event.dest_path,
            old_path=event.src_path,
            is_directory=event.is_directory
        )
        self._queue_event(file_event)
        self._event_counts['moved'] += 1
    
    def _queue_event(self, file_event: FileEvent):
        """
        Queue a file event for processing with debouncing.
        
        Args:
            file_event: File event to queue
        """
        # Filter out unwanted files
        if not self._should_process_event(file_event):
            self._event_counts['filtered'] += 1
            return
        
        # Use async task scheduling to handle the event
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._handle_event_async(file_event))
        except RuntimeError:
            # No event loop running, can't process async
            self.logger.warning(f"No event loop available for processing event: {file_event.file_path}")
    
    async def _handle_event_async(self, file_event: FileEvent):
        """
        Handle file event asynchronously with debouncing and batching.
        
        Args:
            file_event: File event to handle
        """
        file_key = file_event.file_path
        
        try:
            if self.config.batch_processing:
                await self._handle_with_batching(file_event)
            else:
                await self._handle_with_debouncing(file_event)
                
        except Exception as e:
            self.logger.error(f"Error handling file event for {file_key}: {e}", exc_info=True)
    
    async def _handle_with_debouncing(self, file_event: FileEvent):
        """
        Handle event with debouncing to avoid rapid successive operations.
        
        Args:
            file_event: File event to handle
        """
        file_key = file_event.file_path
        
        # Cancel existing debounce task for this file
        if file_key in self._debounce_tasks:
            self._debounce_tasks[file_key].cancel()
        
        # Store the latest event
        self._pending_events[file_key] = file_event
        
        # Create new debounce task
        self._debounce_tasks[file_key] = asyncio.create_task(
            self._debounced_process(file_key)
        )
    
    async def _handle_with_batching(self, file_event: FileEvent):
        """
        Handle event with batching to process multiple events together.
        
        Args:
            file_event: File event to handle
        """
        file_key = file_event.file_path
        
        # Store event in batch
        self._batch_events[file_key] = file_event
        
        # Start batch processing task if not already running
        if not self._batch_task or self._batch_task.done():
            self._batch_task = asyncio.create_task(self._process_batch())
    
    async def _debounced_process(self, file_key: str):
        """
        Process a single file after debounce delay.
        
        Args:
            file_key: File path key
        """
        try:
            # Wait for debounce delay
            await asyncio.sleep(self.config.debounce_delay_ms / 1000.0)
            
            # Get and process the event
            if file_key in self._pending_events:
                event = self._pending_events.pop(file_key)
                await self._process_single_event(event)
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            self._pending_events.pop(file_key, None)
        except Exception as e:
            self.logger.error(f"Error in debounced processing for {file_key}: {e}")
        finally:
            # Clean up task reference
            self._debounce_tasks.pop(file_key, None)
    
    async def _process_batch(self):
        """Process all events in the current batch."""
        try:
            # Wait for batch delay
            await asyncio.sleep(self.config.batch_delay_ms / 1000.0)
            
            # Process all batched events
            if self._batch_events:
                events_to_process = list(self._batch_events.values())
                self._batch_events.clear()
                
                self.logger.debug(f"Processing batch of {len(events_to_process)} events")
                
                for event in events_to_process:
                    await self._process_single_event(event)
                    
        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
    
    async def _process_single_event(self, file_event: FileEvent):
        """
        Process a single file event.
        
        Args:
            file_event: File event to process
        """
        try:
            self.logger.debug(f"Processing {file_event.event_type} event for: {file_event.file_path}")
            await self.event_callback(file_event)
            self._event_counts['processed'] += 1
            
        except Exception as e:
            self.logger.error(f"Error processing event for {file_event.file_path}: {e}")
    
    def _should_process_event(self, file_event: FileEvent) -> bool:
        """
        Check if an event should be processed based on configuration.
        
        Args:
            file_event: File event to check
            
        Returns:
            True if event should be processed
        """
        # Skip directories
        if file_event.is_directory:
            return False
        
        # For deletion events, we can't check file properties
        if file_event.event_type == 'deleted':
            # Check extension from path
            file_path = Path(file_event.file_path)
            return file_path.suffix.lower() in self.config.watched_extensions
        
        # For other events, check if file should be watched
        try:
            file_path = Path(file_event.file_path)
            return self.config.should_watch_file(file_path)
        except Exception as e:
            self.logger.warning(f"Error checking file {file_event.file_path}: {e}")
            return False
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about processed events.
        
        Returns:
            Dictionary with event statistics
        """
        total_events = sum(self._event_counts.values()) - self._event_counts['processed']
        
        return {
            "event_counts": self._event_counts.copy(),
            "pending_events": len(self._pending_events),
            "active_debounce_tasks": len(self._debounce_tasks),
            "batch_events_queued": len(self._batch_events),
            "batch_task_active": bool(self._batch_task and not self._batch_task.done()),
            "total_events_received": total_events,
            "processing_efficiency": (
                self._event_counts['processed'] / total_events 
                if total_events > 0 else 0.0
            )
        }
    
    async def flush_pending_events(self):
        """Force processing of all pending events."""
        try:
            # Process all pending debounced events
            pending_tasks = list(self._debounce_tasks.values())
            if pending_tasks:
                self.logger.debug(f"Flushing {len(pending_tasks)} pending events")
                await asyncio.gather(*pending_tasks, return_exceptions=True)
            
            # Process any remaining batch events
            if self._batch_events and (not self._batch_task or self._batch_task.done()):
                await self._process_batch()
            
        except Exception as e:
            self.logger.error(f"Error flushing pending events: {e}")
    
    async def cleanup(self):
        """Clean up handler resources."""
        try:
            # Cancel all pending tasks
            for task in self._debounce_tasks.values():
                task.cancel()
            
            if self._batch_task and not self._batch_task.done():
                self._batch_task.cancel()
            
            # Wait for cancellation
            all_tasks = list(self._debounce_tasks.values())
            if self._batch_task:
                all_tasks.append(self._batch_task)
            
            if all_tasks:
                await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # Clear state
            self._pending_events.clear()
            self._debounce_tasks.clear()
            self._batch_events.clear()
            
            self.logger.info("Event handler cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")