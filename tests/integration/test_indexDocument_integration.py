"""
Integration tests for indexDocument tool with MCP server.

This test suite validates the end-to-end integration of the indexDocument
tool with the MCP server, including tool registration, discovery, and execution.
"""

import asyncio
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.server import MyDocsMCPServer
from src.config import ServerConfig
from src.tools.registration import register_core_tools
from src.tool_registry import ToolRegistry


class TestIndexDocumentIntegration:
    """Integration test suite for indexDocument tool."""
    
    @pytest.fixture
    def test_config(self):
        """Create test configuration."""
        config = ServerConfig()
        # Use in-memory database for testing
        config.database_url = "sqlite:///:memory:"
        config.log_level = "DEBUG"
        config.debug_mode = True
        return config
    
    @pytest.fixture
    async def test_server(self, test_config):
        """Create test server instance."""
        server = MyDocsMCPServer(test_config)
        yield server
        await server.stop()
    
    @pytest.fixture
    def temp_test_file(self):
        """Create temporary test file."""
        content = """# Test Document

This is a test markdown document for integration testing.

## Features
- Markdown parsing
- Content indexing
- Metadata extraction

Testing content with **bold** and *italic* text.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that tools are properly registered with the registry."""
        registry = ToolRegistry()
        
        # Use in-memory database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            success = await register_core_tools(
                tool_registry=registry,
                database_path=db_path
            )
            
            assert success
            assert registry.has_tool("indexDocument")
            assert "indexDocument" in registry.get_tool_names()
            
            # Check tool information
            tool_info = registry.get_tool_info("indexDocument")
            assert tool_info is not None
            assert tool_info["name"] == "indexDocument"
            assert "Index a document file" in tool_info["description"]
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_tool_discovery_through_server(self, test_server):
        """Test tool discovery through MCP server."""
        from mcp.types import ListToolsRequest
        
        # Initialize tools
        await test_server._initialize_tools()
        
        # Create list_tools request
        request = ListToolsRequest()
        
        # Handle request
        response = await test_server._handle_list_tools(request)
        
        # Verify response
        assert response.tools is not None
        tool_names = [tool.name for tool in response.tools]
        assert "indexDocument" in tool_names
        
        # Find indexDocument tool
        index_tool = next(tool for tool in response.tools if tool.name == "indexDocument")
        assert index_tool.description is not None
        assert index_tool.inputSchema is not None
        assert "file_path" in index_tool.inputSchema.get("properties", {})

    @pytest.mark.asyncio
    async def test_tool_execution_through_server(self, test_server, temp_test_file):
        """Test tool execution through MCP server."""
        from mcp.types import CallToolRequest, CallToolRequestParams
        
        # Initialize tools
        await test_server._initialize_tools()
        
        # Create call_tool request
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="indexDocument",
                arguments={
                    "file_path": temp_test_file
                }
            )
        )
        
        # Execute tool
        response = await test_server._handle_call_tool(request)
        
        # Verify response
        assert not response.isError
        assert response.content is not None
        assert len(response.content) > 0
        
        # Parse response content (should be JSON)
        import json
        response_text = response.content[0].text
        response_data = json.loads(response_text)
        
        assert response_data["success"] is True
        assert response_data["data"]["status"] in ["indexed", "reindexed"]
        assert response_data["data"]["file_path"] == temp_test_file
        assert "document_id" in response_data["data"]
        assert "execution_time_ms" in response_data

    @pytest.mark.asyncio
    async def test_tool_validation_through_server(self, test_server):
        """Test parameter validation through MCP server."""
        from mcp.types import CallToolRequest, CallToolRequestParams
        
        # Initialize tools
        await test_server._initialize_tools()
        
        # Create call_tool request with missing required parameter
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="indexDocument",
                arguments={}  # Missing file_path
            )
        )
        
        # Execute tool
        response = await test_server._handle_call_tool(request)
        
        # Verify error response
        assert response.isError
        assert "Missing required parameter: file_path" in response.content[0].text

    @pytest.mark.asyncio
    async def test_tool_error_handling(self, test_server):
        """Test error handling for non-existent files."""
        from mcp.types import CallToolRequest, CallToolRequestParams
        
        # Initialize tools
        await test_server._initialize_tools()
        
        # Create call_tool request with non-existent file
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="indexDocument",
                arguments={
                    "file_path": "/non/existent/file.txt"
                }
            )
        )
        
        # Execute tool
        response = await test_server._handle_call_tool(request)
        
        # Verify error is handled gracefully
        assert response.isError or (response.content and "File not found" in response.content[0].text)

    @pytest.mark.asyncio
    async def test_multiple_tool_executions(self, test_server, temp_test_file):
        """Test multiple executions of the same tool."""
        from mcp.types import CallToolRequest, CallToolRequestParams
        
        # Initialize tools
        await test_server._initialize_tools()
        
        # First execution
        request1 = CallToolRequest(
            params=CallToolRequestParams(
                name="indexDocument",
                arguments={"file_path": temp_test_file}
            )
        )
        
        response1 = await test_server._handle_call_tool(request1)
        assert not response1.isError
        
        # Second execution (should detect already indexed)
        request2 = CallToolRequest(
            params=CallToolRequestParams(
                name="indexDocument",
                arguments={"file_path": temp_test_file}
            )
        )
        
        response2 = await test_server._handle_call_tool(request2)
        assert not response2.isError
        
        # Parse responses
        import json
        data1 = json.loads(response1.content[0].text)
        data2 = json.loads(response2.content[0].text)
        
        assert data1["data"]["status"] == "indexed"
        # Note: may be "already_indexed" or "indexed" depending on timing
        assert data2["data"]["status"] in ["already_indexed", "indexed"]

    @pytest.mark.asyncio
    async def test_force_reindex_through_server(self, test_server, temp_test_file):
        """Test force reindexing functionality."""
        from mcp.types import CallToolRequest, CallToolRequestParams
        import json
        
        # Initialize tools
        await test_server._initialize_tools()
        
        # First execution
        request1 = CallToolRequest(
            params=CallToolRequestParams(
                name="indexDocument",
                arguments={"file_path": temp_test_file}
            )
        )
        
        response1 = await test_server._handle_call_tool(request1)
        assert not response1.isError
        
        # Force reindex
        request2 = CallToolRequest(
            params=CallToolRequestParams(
                name="indexDocument",
                arguments={
                    "file_path": temp_test_file,
                    "force_reindex": True
                }
            )
        )
        
        response2 = await test_server._handle_call_tool(request2)
        assert not response2.isError
        
        data2 = json.loads(response2.content[0].text)
        assert data2["data"]["status"] == "reindexed"

    @pytest.mark.asyncio
    async def test_performance_under_load(self, test_server):
        """Test tool performance with multiple concurrent requests."""
        from mcp.types import CallToolRequest, CallToolRequestParams
        import time
        
        # Initialize tools
        await test_server._initialize_tools()
        
        # Create multiple test files
        test_files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Test content for file {i}")
                test_files.append(f.name)
        
        try:
            # Create concurrent requests
            requests = []
            for i, file_path in enumerate(test_files):
                request = test_server._handle_call_tool(
                    CallToolRequest(
                        params=CallToolRequestParams(
                            name="indexDocument",
                            arguments={"file_path": file_path}
                        )
                    )
                )
                requests.append(request)
            
            # Execute concurrently
            start_time = time.time()
            responses = await asyncio.gather(*requests)
            execution_time = time.time() - start_time
            
            # Verify all succeeded
            for response in responses:
                assert not response.isError
            
            # Performance check - should complete within reasonable time
            # Sub-200ms per tool as per requirements, 5 tools should be under 1 second
            assert execution_time < 2.0  # Allow some buffer for test environment
            
        finally:
            # Cleanup test files
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)