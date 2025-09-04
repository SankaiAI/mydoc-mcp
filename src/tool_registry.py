"""
Tool registry system for mydocs-mcp server.

This module manages registration, discovery, and execution of MCP tools.
It provides a framework for registering tools dynamically and executing them
with proper error handling and validation.
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional, Union

from mcp.types import Tool
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from .logging_config import get_logger


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails."""
    pass


class ToolRegistrationError(Exception):
    """Exception raised when tool registration fails."""
    pass


class ValidationError(Exception):
    """Exception raised when tool argument validation fails."""
    pass


class ToolMetadata(BaseModel):
    """Metadata for a registered tool."""
    name: str
    description: str
    handler: Callable
    input_schema: Dict[str, Any]
    is_async: bool = True
    timeout: Optional[float] = None


class ToolRegistry:
    """
    Registry for managing MCP tools.
    
    The registry maintains a collection of available tools, their metadata,
    and provides methods for tool discovery and execution.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self.logger = get_logger(__name__)
        self._tools: Dict[str, ToolMetadata] = {}
        self.logger.info("Tool registry initialized")
    
    def register_tool(
        self,
        name: str,
        description: str,
        handler: Callable,
        input_schema: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> None:
        """
        Register a new tool with the registry.
        
        Args:
            name: Unique tool name
            description: Human-readable description
            handler: Function to execute when tool is called
            input_schema: JSON schema for tool input validation
            timeout: Optional timeout for tool execution
        
        Raises:
            ToolRegistrationError: If tool registration fails
        """
        try:
            # Validate tool name
            if not name or not isinstance(name, str):
                raise ToolRegistrationError("Tool name must be a non-empty string")
            
            if name in self._tools:
                raise ToolRegistrationError(f"Tool '{name}' is already registered")
            
            # Validate handler
            if not callable(handler):
                raise ToolRegistrationError("Tool handler must be callable")
            
            # Check if handler is async
            is_async = asyncio.iscoroutinefunction(handler)
            
            # Validate input schema
            if not isinstance(input_schema, dict):
                raise ToolRegistrationError("Input schema must be a dictionary")
            
            # Create and store tool metadata
            metadata = ToolMetadata(
                name=name,
                description=description,
                handler=handler,
                input_schema=input_schema,
                is_async=is_async,
                timeout=timeout
            )
            
            self._tools[name] = metadata
            
            self.logger.info(f"Tool '{name}' registered successfully")
            self.logger.debug(f"Tool metadata: {metadata}")
            
        except Exception as e:
            error_msg = f"Failed to register tool '{name}': {e}"
            self.logger.error(error_msg)
            raise ToolRegistrationError(error_msg) from e
    
    def unregister_tool(self, name: str) -> bool:
        """
        Remove a tool from the registry.
        
        Args:
            name: Name of tool to remove
        
        Returns:
            True if tool was removed, False if it wasn't found
        """
        if name in self._tools:
            del self._tools[name]
            self.logger.info(f"Tool '{name}' unregistered")
            return True
        else:
            self.logger.warning(f"Attempted to unregister unknown tool '{name}'")
            return False
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
    
    def get_tool_names(self) -> List[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())
    
    def get_available_tools(self) -> List[Tool]:
        """
        Get list of available tools in MCP format.
        
        Returns:
            List of Tool objects for MCP protocol
        """
        tools = []
        
        for metadata in self._tools.values():
            tool = Tool(
                name=metadata.name,
                description=metadata.description,
                inputSchema=metadata.input_schema
            )
            tools.append(tool)
        
        self.logger.debug(f"Generated {len(tools)} tool definitions")
        return tools
    
    def _validate_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool arguments against input schema.
        
        Args:
            tool_name: Name of the tool
            arguments: Arguments to validate
        
        Returns:
            Validated arguments
        
        Raises:
            ValidationError: If arguments are invalid
        """
        metadata = self._tools[tool_name]
        schema = metadata.input_schema
        
        # Basic validation - check required fields
        if "required" in schema:
            required_fields = schema["required"]
            for field in required_fields:
                if field not in arguments:
                    raise ValidationError(f"Missing required argument: {field}")
        
        # Type validation for properties (basic implementation)
        if "properties" in schema:
            properties = schema["properties"]
            for arg_name, arg_value in arguments.items():
                if arg_name in properties:
                    prop_schema = properties[arg_name]
                    if "type" in prop_schema:
                        expected_type = prop_schema["type"]
                        if not self._validate_type(arg_value, expected_type):
                            raise ValidationError(
                                f"Argument '{arg_name}' must be of type {expected_type}, "
                                f"got {type(arg_value).__name__}"
                            )
        
        return arguments
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type against expected JSON schema type."""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        if expected_type not in type_mapping:
            return True  # Unknown type, skip validation
        
        expected_python_type = type_mapping[expected_type]
        return isinstance(value, expected_python_type)
    
    async def execute_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a registered tool.
        
        Args:
            name: Name of tool to execute
            arguments: Arguments to pass to the tool
        
        Returns:
            Tool execution result
        
        Raises:
            ToolExecutionError: If tool execution fails
        """
        if name not in self._tools:
            raise ToolExecutionError(f"Tool '{name}' not found")
        
        metadata = self._tools[name]
        arguments = arguments or {}
        
        self.logger.debug(f"Executing tool '{name}' with arguments: {arguments}")
        
        try:
            # Validate arguments
            validated_args = self._validate_arguments(name, arguments)
            
            # Execute tool with timeout
            if metadata.is_async:
                if metadata.timeout:
                    result = await asyncio.wait_for(
                        metadata.handler(**validated_args),
                        timeout=metadata.timeout
                    )
                else:
                    result = await metadata.handler(**validated_args)
            else:
                # Run sync function in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                if metadata.timeout:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, metadata.handler, **validated_args),
                        timeout=metadata.timeout
                    )
                else:
                    result = await loop.run_in_executor(None, metadata.handler, **validated_args)
            
            self.logger.debug(f"Tool '{name}' executed successfully")
            return result
            
        except ValidationError as e:
            error_msg = f"Invalid arguments for tool '{name}': {e}"
            self.logger.error(error_msg)
            raise ToolExecutionError(error_msg) from e
        
        except asyncio.TimeoutError:
            error_msg = f"Tool '{name}' timed out after {metadata.timeout}s"
            self.logger.error(error_msg)
            raise ToolExecutionError(error_msg)
        
        except Exception as e:
            error_msg = f"Tool '{name}' execution failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ToolExecutionError(error_msg) from e
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a registered tool.
        
        Args:
            name: Tool name
        
        Returns:
            Tool information dictionary or None if not found
        """
        if name not in self._tools:
            return None
        
        metadata = self._tools[name]
        return {
            "name": metadata.name,
            "description": metadata.description,
            "input_schema": metadata.input_schema,
            "is_async": metadata.is_async,
            "timeout": metadata.timeout
        }
    
    async def cleanup(self) -> None:
        """Clean up resources used by the tool registry."""
        self.logger.info("Cleaning up tool registry")
        
        # Clear all registered tools
        self._tools.clear()
        
        self.logger.info("Tool registry cleanup completed")
    
    def __len__(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered using 'in' operator."""
        return name in self._tools
    
    def __iter__(self):
        """Iterate over registered tool names."""
        return iter(self._tools.keys())


# Global tool registry instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def register_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    timeout: Optional[float] = None
) -> Callable:
    """
    Decorator for registering tools with the global registry.
    
    Args:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for input validation
        timeout: Optional execution timeout
    
    Returns:
        Decorator function
    
    Usage:
        @register_tool(
            name="example_tool",
            description="An example tool",
            input_schema={"type": "object", "properties": {"arg": {"type": "string"}}}
        )
        async def example_handler(arg: str) -> str:
            return f"Hello, {arg}!"
    """
    def decorator(handler: Callable) -> Callable:
        registry = get_tool_registry()
        registry.register_tool(name, description, handler, input_schema, timeout)
        return handler
    
    return decorator