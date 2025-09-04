"""
Test suite for file system watcher functionality.

This module provides comprehensive tests for the file system watcher,
including configuration, event handling, and integration with the indexing system.
"""

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import List, Optional
from unittest.mock import Mock, AsyncMock, patch
import pytest
import pytest_asyncio

from src.watcher.config import WatcherConfig, create_watcher_config, load_watcher_config_from_env
from src.watcher.event_handler import AsyncFileSystemEventHandler, FileEvent
from src.watcher.file_watcher import FileWatcher
from src.watcher import create_default_watcher


class TestWatcherConfig:
    """Test watcher configuration functionality."""
    
    def test_default_config_creation(self):
        """Test creating default configuration."""
        config = WatcherConfig()
        
        assert isinstance(config.watched_extensions, set)
        assert '.md' in config.watched_extensions
        assert '.txt' in config.watched_extensions
        assert config.debounce_delay_ms > 0
        assert config.enable_recursive is True
        assert len(config.ignore_patterns) > 0
    
    def test_config_with_overrides(self):
        """Test configuration with custom overrides."""
        custom_dirs = ['/test/dir1', '/test/dir2']
        custom_extensions = {'.md', '.rst'}
        
        config = WatcherConfig(
            watch_directories=custom_dirs,
            watched_extensions=custom_extensions,
            debounce_delay_ms=1000
        )
        
        assert config.debounce_delay_ms == 1000
        assert config.watched_extensions == {'.md', '.rst'}
        # Note: watch_directories will be validated and may be filtered
    
    def test_extension_normalization(self):
        """Test that file extensions are normalized correctly."""
        config = WatcherConfig(
            watched_extensions={'md', '.txt', 'RST'}
        )
        
        expected = {'.md', '.txt', '.rst'}
        assert config.watched_extensions == expected
    
    def test_should_watch_file(self):
        """Test file watching decision logic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            md_file = temp_path / "test.md"
            txt_file = temp_path / "test.txt"
            py_file = temp_path / "test.py"
            tmp_file = temp_path / "test.tmp"
            
            for file_path in [md_file, txt_file, py_file, tmp_file]:
                file_path.write_text("test content")
            
            config = WatcherConfig()
            
            # Should watch .md and .txt files
            assert config.should_watch_file(md_file)
            assert config.should_watch_file(txt_file)
            
            # Should not watch .py files
            assert not config.should_watch_file(py_file)
            
            # Should not watch temporary files
            assert not config.should_watch_file(tmp_file)
    
    @patch.dict(os.environ, {
        'MYDOCS_WATCH_DIRS': '/home/user/docs;/home/user/notes',
        'MYDOCS_WATCH_EXTENSIONS': '.md,.txt,.rst',
        'MYDOCS_DEBOUNCE_DELAY_MS': '750',
        'MYDOCS_RECURSIVE_WATCH': 'false'
    })
    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        config = load_watcher_config_from_env()
        
        # Check that extensions were parsed correctly
        assert '.md' in config.watched_extensions
        assert '.txt' in config.watched_extensions
        assert '.rst' in config.watched_extensions
        
        assert config.debounce_delay_ms == 750
        assert config.enable_recursive is False


class TestAsyncFileSystemEventHandler:
    """Test async file system event handler."""
    
    @pytest_asyncio.fixture
    async def mock_callback(self):
        """Create mock async callback."""
        return AsyncMock()
    
    @pytest_asyncio.fixture
    def handler(self, mock_callback):
        """Create event handler with mock callback."""
        config = WatcherConfig(debounce_delay_ms=100)
        return AsyncFileSystemEventHandler(
            config=config,
            event_callback=mock_callback
        )
    
    def test_handler_initialization(self, handler):
        """Test handler initialization."""
        assert handler.config is not None
        assert handler.event_callback is not None
        assert len(handler._event_counts) > 0
    
    @pytest.mark.asyncio
    async def test_event_processing_with_debouncing(self, handler, mock_callback):
        """Test event processing with debouncing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("test content")
            
            # Create file event
            file_event = FileEvent(
                event_type='created',
                file_path=str(test_file)
            )
            
            # Process event
            await handler._handle_event_async(file_event)
            
            # Wait for debouncing
            await asyncio.sleep(0.2)
            
            # Verify callback was called
            mock_callback.assert_called_once()
            call_args = mock_callback.call_args[0][0]
            assert call_args.event_type == 'created'
            assert call_args.file_path == str(test_file)
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, mock_callback):
        """Test batch event processing."""
        config = WatcherConfig(
            batch_processing=True,
            batch_delay_ms=100
        )
        handler = AsyncFileSystemEventHandler(
            config=config,
            event_callback=mock_callback
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple events
            events = []
            for i in range(3):
                test_file = Path(temp_dir) / f"test{i}.md"
                test_file.write_text("test content")
                events.append(FileEvent(
                    event_type='created',
                    file_path=str(test_file)
                ))
            
            # Process all events
            for event in events:
                await handler._handle_event_async(event)
            
            # Wait for batch processing
            await asyncio.sleep(0.2)
            
            # Verify all events were processed
            assert mock_callback.call_count == 3
    
    def test_event_filtering(self, handler):
        """Test event filtering logic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            md_file = temp_path / "test.md"
            py_file = temp_path / "test.py"
            tmp_file = temp_path / "test.tmp"
            
            for file_path in [md_file, py_file, tmp_file]:
                file_path.write_text("test content")
            
            # Test events
            md_event = FileEvent('created', str(md_file))
            py_event = FileEvent('created', str(py_file))
            tmp_event = FileEvent('created', str(tmp_file))
            
            # Should process .md files
            assert handler._should_process_event(md_event)
            
            # Should not process .py files
            assert not handler._should_process_event(py_event)
            
            # Should not process temporary files
            assert not handler._should_process_event(tmp_event)
    
    @pytest.mark.asyncio
    async def test_cleanup(self, handler):
        """Test handler cleanup."""
        # Add some pending events
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("test content")
            
            event = FileEvent('created', str(test_file))
            await handler._handle_event_async(event)
            
            # Cleanup should not raise errors
            await handler.cleanup()
            
            # Verify state is cleaned
            assert len(handler._pending_events) == 0
            assert len(handler._debounce_tasks) == 0


class TestFileWatcher:
    """Test main file watcher functionality."""
    
    @pytest_asyncio.fixture
    async def temp_watch_dir(self):
        """Create temporary directory for watching."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest_asyncio.fixture
    def mock_index_tool(self):
        """Create mock index tool."""
        mock_tool = AsyncMock()
        mock_tool._execute_tool.return_value = Mock(is_success=True)
        return mock_tool
    
    @pytest_asyncio.fixture
    def mock_database_manager(self):
        """Create mock database manager."""
        mock_db = AsyncMock()
        mock_db.doc_queries.get_document_by_path.return_value = None
        mock_db.doc_queries.delete_document_by_path.return_value = True
        mock_db.doc_queries.update_document_path.return_value = True
        return mock_db
    
    def test_watcher_initialization(self, temp_watch_dir, mock_index_tool, mock_database_manager):
        """Test file watcher initialization."""
        config = WatcherConfig(watch_directories=[temp_watch_dir])
        
        watcher = FileWatcher(
            config=config,
            index_tool=mock_index_tool,
            database_manager=mock_database_manager
        )
        
        assert watcher.config == config
        assert watcher.index_tool == mock_index_tool
        assert watcher.database_manager == mock_database_manager
        assert not watcher.is_watching
    
    @pytest.mark.asyncio
    async def test_watcher_start_stop(self, temp_watch_dir, mock_index_tool, mock_database_manager):
        """Test starting and stopping the watcher."""
        config = WatcherConfig(watch_directories=[temp_watch_dir])
        
        watcher = FileWatcher(
            config=config,
            index_tool=mock_index_tool,
            database_manager=mock_database_manager
        )
        
        # Start watcher
        success = await watcher.start()
        assert success
        assert watcher.is_watching
        assert watcher.start_time is not None
        
        # Stop watcher
        success = await watcher.stop()
        assert success
        assert not watcher.is_watching
    
    @pytest.mark.asyncio
    async def test_file_created_handling(self, temp_watch_dir, mock_index_tool, mock_database_manager):
        """Test handling file creation events."""
        config = WatcherConfig(watch_directories=[temp_watch_dir])
        watcher = FileWatcher(
            config=config,
            index_tool=mock_index_tool,
            database_manager=mock_database_manager
        )
        
        # Create test file
        test_file = Path(temp_watch_dir) / "test.md"
        test_file.write_text("# Test Document\n\nThis is a test.")
        
        # Handle creation event
        event = FileEvent('created', str(test_file))
        action = await watcher._handle_file_created(event)
        
        assert action == 'indexed'
        mock_index_tool._execute_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_file_modified_handling(self, temp_watch_dir, mock_index_tool, mock_database_manager):
        """Test handling file modification events."""
        config = WatcherConfig(watch_directories=[temp_watch_dir])
        watcher = FileWatcher(
            config=config,
            index_tool=mock_index_tool,
            database_manager=mock_database_manager
        )
        
        # Create test file
        test_file = Path(temp_watch_dir) / "test.md"
        test_file.write_text("# Modified Document\n\nThis was modified.")
        
        # Handle modification event
        event = FileEvent('modified', str(test_file))
        action = await watcher._handle_file_modified(event)
        
        assert action == 'indexed'
        mock_index_tool._execute_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_file_deleted_handling(self, temp_watch_dir, mock_index_tool, mock_database_manager):
        """Test handling file deletion events."""
        config = WatcherConfig(watch_directories=[temp_watch_dir])
        watcher = FileWatcher(
            config=config,
            index_tool=mock_index_tool,
            database_manager=mock_database_manager
        )
        
        # Handle deletion event
        event = FileEvent('deleted', '/path/to/deleted/file.md')
        action = await watcher._handle_file_deleted(event)
        
        assert action == 'deleted'
        mock_database_manager.doc_queries.delete_document_by_path.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_file_moved_handling(self, temp_watch_dir, mock_index_tool, mock_database_manager):
        """Test handling file move events."""
        config = WatcherConfig(watch_directories=[temp_watch_dir])
        watcher = FileWatcher(
            config=config,
            index_tool=mock_index_tool,
            database_manager=mock_database_manager
        )
        
        # Create test file at new location
        new_file = Path(temp_watch_dir) / "moved.md"
        new_file.write_text("# Moved Document")
        
        # Mock existing document
        mock_doc = Mock()
        mock_doc.id = 1
        mock_database_manager.doc_queries.get_document_by_path.return_value = mock_doc
        
        # Handle move event
        event = FileEvent('moved', str(new_file), old_path='/old/path.md')
        action = await watcher._handle_file_moved(event)
        
        assert action == 'moved'
        mock_database_manager.doc_queries.update_document_path.assert_called_once()
    
    def test_statistics_tracking(self, temp_watch_dir, mock_index_tool, mock_database_manager):
        """Test statistics tracking."""
        config = WatcherConfig(watch_directories=[temp_watch_dir])
        watcher = FileWatcher(
            config=config,
            index_tool=mock_index_tool,
            database_manager=mock_database_manager
        )
        
        stats = watcher.get_statistics()
        
        assert 'is_watching' in stats
        assert 'watched_directories' in stats
        assert 'processing_stats' in stats
        assert isinstance(stats['processing_stats'], dict)
    
    def test_health_status(self, temp_watch_dir, mock_index_tool, mock_database_manager):
        """Test health status checking."""
        config = WatcherConfig(watch_directories=[temp_watch_dir])
        watcher = FileWatcher(
            config=config,
            index_tool=mock_index_tool,
            database_manager=mock_database_manager
        )
        
        health = watcher.get_health_status()
        
        assert 'healthy' in health
        assert 'issues' in health
        assert 'error_rate' in health
        assert isinstance(health['issues'], list)
    
    @pytest.mark.asyncio
    async def test_manual_scan(self, temp_watch_dir, mock_index_tool, mock_database_manager):
        """Test manual directory scanning."""
        config = WatcherConfig(watch_directories=[temp_watch_dir])
        watcher = FileWatcher(
            config=config,
            index_tool=mock_index_tool,
            database_manager=mock_database_manager
        )
        
        # Create test files
        for i in range(3):
            test_file = Path(temp_watch_dir) / f"test{i}.md"
            test_file.write_text(f"# Test Document {i}")
        
        # Run manual scan
        results = await watcher.manual_scan(temp_watch_dir)
        
        assert results['scanned_directories'] == 1
        assert results['files_found'] == 3
        assert results['scan_time_seconds'] > 0


class TestWatcherIntegration:
    """Test watcher integration with other components."""
    
    def test_create_default_watcher(self):
        """Test creating default watcher."""
        watcher = create_default_watcher()
        
        assert isinstance(watcher, FileWatcher)
        assert watcher.config is not None
        assert len(watcher.config.watch_directories) >= 0
    
    @pytest.mark.asyncio
    async def test_watcher_with_real_files(self):
        """Test watcher with actual file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock components
            mock_index_tool = AsyncMock()
            mock_index_tool._execute_tool.return_value = Mock(is_success=True)
            
            mock_db = AsyncMock()
            mock_db.doc_queries.get_document_by_path.return_value = None
            
            config = WatcherConfig(
                watch_directories=[temp_dir],
                debounce_delay_ms=50  # Fast for testing
            )
            
            watcher = FileWatcher(
                config=config,
                index_tool=mock_index_tool,
                database_manager=mock_db
            )
            
            # Start watcher
            await watcher.start()
            
            try:
                # Create a file
                test_file = Path(temp_dir) / "test.md"
                test_file.write_text("# Test Document")
                
                # Wait for event processing
                await asyncio.sleep(0.2)
                
                # Modify the file
                test_file.write_text("# Modified Test Document")
                
                # Wait for event processing
                await asyncio.sleep(0.2)
                
                # The mock should have been called
                assert mock_index_tool._execute_tool.call_count >= 1
                
            finally:
                await watcher.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_watcher(self, temp_watch_dir):
        """Test error handling in watcher operations."""
        # Mock tool that raises exceptions
        mock_index_tool = AsyncMock()
        mock_index_tool._execute_tool.side_effect = Exception("Indexing failed")
        
        config = WatcherConfig(watch_directories=[temp_watch_dir])
        watcher = FileWatcher(
            config=config,
            index_tool=mock_index_tool
        )
        
        # Create test file
        test_file = Path(temp_watch_dir) / "test.md"
        test_file.write_text("# Test Document")
        
        # Handle event - should not raise exception
        event = FileEvent('created', str(test_file))
        action = await watcher._handle_file_created(event)
        
        # Should handle error gracefully
        assert action is None  # Error case
        assert watcher.stats['indexing_errors'] > 0
    
    def test_config_environment_integration(self):
        """Test configuration integration with environment."""
        with patch.dict(os.environ, {
            'MYDOCS_WATCH_DIRS': '/test/dir1;/test/dir2',
            'MYDOCS_DEBOUNCE_DELAY_MS': '500'
        }):
            config = load_watcher_config_from_env()
            
            # Environment values should be loaded
            assert config.debounce_delay_ms == 500
            # Directories will be validated - may not match exactly if paths don't exist


@pytest.mark.integration
class TestFullWatcherWorkflow:
    """Integration tests for complete watcher workflow."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end watcher workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up components
            events_processed = []
            
            async def mock_callback(event):
                events_processed.append(event)
            
            config = WatcherConfig(
                watch_directories=[temp_dir],
                debounce_delay_ms=50,
                batch_processing=False
            )
            
            handler = AsyncFileSystemEventHandler(
                config=config,
                event_callback=mock_callback
            )
            
            # Create files and trigger events
            test_files = []
            for i in range(3):
                file_path = Path(temp_dir) / f"test{i}.md"
                file_path.write_text(f"# Test Document {i}")
                test_files.append(file_path)
                
                # Create event
                event = FileEvent('created', str(file_path))
                await handler._handle_event_async(event)
            
            # Wait for processing
            await asyncio.sleep(0.2)
            
            # Verify all events were processed
            assert len(events_processed) == 3
            
            for i, event in enumerate(events_processed):
                assert event.event_type == 'created'
                assert f'test{i}.md' in event.file_path
            
            # Cleanup
            await handler.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])