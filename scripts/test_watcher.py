#!/usr/bin/env python3
"""
Simple validation script for the file system watcher.

This script tests the basic functionality of the file watcher system
to ensure it can monitor directories and detect file changes.
"""

import asyncio
import tempfile
import time
from pathlib import Path
import logging

from src.watcher import FileWatcher, WatcherConfig
from src.watcher.event_handler import FileEvent


async def mock_index_tool(params):
    """Mock index tool that simulates document indexing."""
    print(f"Mock indexing: {params.get('file_path', 'unknown')}")
    return type('Result', (), {'is_success': True, 'error_message': None})()


class MockIndexTool:
    """Mock index tool for testing."""
    
    async def _execute_tool(self, params):
        """Mock execute tool method."""
        return await mock_index_tool(params)


async def test_file_watcher():
    """Test file watcher functionality."""
    print("🧪 Testing File System Watcher")
    print("=" * 50)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Test directory: {temp_dir}")
        
        # Configure watcher for test directory
        config = WatcherConfig(
            watch_directories=[temp_dir],
            debounce_delay_ms=100,  # Fast for testing
            batch_processing=False
        )
        
        # Create mock components
        mock_tool = MockIndexTool()
        
        # Create watcher
        watcher = FileWatcher(
            config=config,
            index_tool=mock_tool
        )
        
        print(f"⚙️  Watcher configuration:")
        summary = config.get_watch_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        try:
            # Start watcher
            print("\n🚀 Starting watcher...")
            success = await watcher.start()
            
            if not success:
                print("❌ Failed to start watcher")
                return
            
            print("✅ Watcher started successfully")
            
            # Test file operations
            test_file = Path(temp_dir) / "test_document.md"
            
            # Create file
            print(f"\n📝 Creating test file: {test_file.name}")
            test_file.write_text("# Test Document\n\nThis is a test document.")
            
            # Wait for event processing
            await asyncio.sleep(0.3)
            
            # Modify file
            print(f"✏️  Modifying test file: {test_file.name}")
            test_file.write_text("# Modified Test Document\n\nThis document has been modified.")
            
            # Wait for event processing
            await asyncio.sleep(0.3)
            
            # Create another file
            test_file2 = Path(temp_dir) / "another_doc.txt"
            print(f"📝 Creating second test file: {test_file2.name}")
            test_file2.write_text("This is a text document.")
            
            # Wait for event processing
            await asyncio.sleep(0.3)
            
            # Delete file
            print(f"🗑️  Deleting test file: {test_file.name}")
            test_file.unlink()
            
            # Wait for event processing
            await asyncio.sleep(0.3)
            
            # Get statistics
            print(f"\n📊 Watcher statistics:")
            stats = watcher.get_statistics()
            processing_stats = stats.get('processing_stats', {})
            for key, value in processing_stats.items():
                print(f"   {key}: {value}")
            
            # Get health status
            print(f"\n🏥 Health status:")
            health = watcher.get_health_status()
            print(f"   Healthy: {health['healthy']}")
            print(f"   Issues: {health.get('issues', [])}")
            print(f"   Error rate: {health.get('error_rate', 0):.1%}")
            
            print(f"\n✅ File watcher test completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Stop watcher
            print(f"\n🛑 Stopping watcher...")
            await watcher.stop()
            print(f"✅ Watcher stopped")


async def test_event_handler():
    """Test event handler functionality."""
    print("\n🧪 Testing Event Handler")
    print("=" * 50)
    
    events_processed = []
    
    async def test_callback(event):
        """Test callback for event processing."""
        events_processed.append(event)
        print(f"📥 Event processed: {event.event_type} - {Path(event.file_path).name}")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        config = WatcherConfig(
            watch_directories=[temp_dir],
            debounce_delay_ms=50,
            batch_processing=False
        )
        
        # Import here to avoid circular imports during testing
        from src.watcher.event_handler import AsyncFileSystemEventHandler
        
        handler = AsyncFileSystemEventHandler(
            config=config,
            event_callback=test_callback
        )
        
        # Test different event types
        test_file = Path(temp_dir) / "handler_test.md"
        test_file.write_text("# Handler Test")
        
        events = [
            FileEvent('created', str(test_file)),
            FileEvent('modified', str(test_file)),
            FileEvent('moved', str(test_file), old_path=str(test_file.with_suffix('.old'))),
            FileEvent('deleted', str(test_file))
        ]
        
        print(f"🔄 Processing {len(events)} test events...")
        
        for event in events:
            await handler._handle_event_async(event)
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        print(f"📋 Events processed: {len(events_processed)}")
        for event in events_processed:
            print(f"   {event.event_type}: {Path(event.file_path).name}")
        
        # Get handler statistics
        handler_stats = handler.get_event_statistics()
        print(f"\n📊 Handler statistics:")
        for key, value in handler_stats.items():
            print(f"   {key}: {value}")
        
        # Cleanup
        await handler.cleanup()
        print(f"✅ Event handler test completed")


async def main():
    """Main test function."""
    print("🧪 mydocs-mcp File System Watcher Tests")
    print("=" * 60)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        await test_event_handler()
        await test_file_watcher()
        
        print(f"\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)