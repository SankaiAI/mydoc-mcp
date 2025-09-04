"""
Base MCP Tool Implementation for mydocs-mcp

This module provides the base classes and interfaces for all MCP tools
in the mydocs-mcp server, ensuring consistent patterns, error handling,
and performance tracking across all tool implementations.
"""

import time
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, ValidationError


class MCPToolError(Exception):
    """Base exception for MCP tool errors."""
    pass


class ToolValidationError(MCPToolError):
    """Exception raised when tool parameter validation fails."""
    pass


class ToolExecutionError(MCPToolError):
    """Exception raised when tool execution fails."""
    pass


@dataclass
class ToolResult:
    """
    Standardized result structure for all MCP tools.
    
    This provides a consistent interface for tool responses,
    including success status, data payload, error information,
    and performance metrics.
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        result = {
            "success": self.success,
            "execution_time_ms": self.execution_time_ms
        }
        
        if self.data is not None:
            result["data"] = self.data
            
        if self.error is not None:
            result["error"] = self.error
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    @classmethod
    def success_result(
        cls,
        data: Dict[str, Any],
        execution_time_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ToolResult':
        """Create a success result."""
        return cls(
            success=True,
            data=data,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {}
        )
    
    @classmethod
    def error_result(
        cls,
        error_message: str,
        execution_time_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ToolResult':
        """Create an error result."""
        return cls(
            success=False,
            error=error_message,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {}
        )


class BaseMCPTool(ABC):
    """
    Abstract base class for all MCP tools in mydocs-mcp.
    
    This class provides the standard interface, validation framework,
    error handling, and performance tracking that all tools should inherit.
    
    Key features:
    - Parameter validation using Pydantic schemas
    - Consistent error handling and logging  
    - Performance tracking and metrics
    - Async execution with timeout support
    - Standardized result formatting
    """
    
    def __init__(
        self,
        database_manager,
        parser_factory,
        logger: Optional[logging.Logger] = None,
        timeout_seconds: float = 30.0
    ):
        """
        Initialize base MCP tool.
        
        Args:
            database_manager: DocumentManager instance for database operations
            parser_factory: ParserFactory instance for document parsing
            logger: Optional logger instance
            timeout_seconds: Default timeout for tool execution
        """
        self.database_manager = database_manager
        self.parser_factory = parser_factory
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.timeout_seconds = timeout_seconds
        
        # Tool metadata
        self.name = self.get_tool_name()
        self.description = self.get_tool_description()
        
        # Performance tracking
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._error_count = 0
        
        self.logger.debug(f"Initialized {self.name} tool")
    
    @abstractmethod
    def get_tool_name(self) -> str:
        """
        Return the MCP tool name.
        
        Returns:
            Tool name string
        """
        pass
    
    @abstractmethod
    def get_tool_description(self) -> str:
        """
        Return the MCP tool description.
        
        Returns:
            Tool description string
        """
        pass
    
    @abstractmethod
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Return the JSON schema for tool parameters.
        
        Returns:
            JSON schema dictionary
        """
        pass
    
    @abstractmethod
    async def _execute_tool(self, validated_params: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool logic with validated parameters.
        
        Args:
            validated_params: Parameters that have passed validation
            
        Returns:
            ToolResult with execution results
        """
        pass
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool parameters against schema.
        
        Args:
            params: Raw parameter dictionary
            
        Returns:
            Validated parameters dictionary
            
        Raises:
            ToolValidationError: If parameter validation fails
        """
        try:
            schema = self.get_parameter_schema()
            
            # Basic JSON schema validation
            validated_params = {}
            
            # Check required fields
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in params:
                    raise ToolValidationError(f"Missing required parameter: {field}")
            
            # Validate properties
            properties = schema.get("properties", {})
            for param_name, param_value in params.items():
                if param_name not in properties:
                    # Allow extra parameters for flexibility
                    validated_params[param_name] = param_value
                    continue
                
                prop_schema = properties[param_name]
                
                # Type validation
                if "type" in prop_schema:
                    expected_type = prop_schema["type"]
                    if not self._validate_type(param_value, expected_type):
                        raise ToolValidationError(
                            f"Parameter '{param_name}' must be of type {expected_type}, "
                            f"got {type(param_value).__name__}"
                        )
                
                # Additional validation (min/max, patterns, etc.)
                self._validate_property_constraints(param_name, param_value, prop_schema)
                
                validated_params[param_name] = param_value
            
            # Apply default values
            for prop_name, prop_schema in properties.items():
                if prop_name not in validated_params and "default" in prop_schema:
                    validated_params[prop_name] = prop_schema["default"]
            
            return validated_params
            
        except ToolValidationError:
            raise
        except Exception as e:
            raise ToolValidationError(f"Parameter validation failed: {str(e)}")
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type against JSON schema type."""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        
        if expected_type not in type_mapping:
            return True  # Unknown type, skip validation
        
        expected_python_type = type_mapping[expected_type]
        return isinstance(value, expected_python_type)
    
    def _validate_property_constraints(
        self,
        param_name: str,
        value: Any,
        prop_schema: Dict[str, Any]
    ) -> None:
        """Validate additional property constraints."""
        # String constraints
        if isinstance(value, str):
            if "minLength" in prop_schema:
                if len(value) < prop_schema["minLength"]:
                    raise ToolValidationError(
                        f"Parameter '{param_name}' must be at least "
                        f"{prop_schema['minLength']} characters long"
                    )
            
            if "maxLength" in prop_schema:
                if len(value) > prop_schema["maxLength"]:
                    raise ToolValidationError(
                        f"Parameter '{param_name}' must be at most "
                        f"{prop_schema['maxLength']} characters long"
                    )
        
        # Number constraints
        if isinstance(value, (int, float)):
            if "minimum" in prop_schema:
                if value < prop_schema["minimum"]:
                    raise ToolValidationError(
                        f"Parameter '{param_name}' must be at least {prop_schema['minimum']}"
                    )
            
            if "maximum" in prop_schema:
                if value > prop_schema["maximum"]:
                    raise ToolValidationError(
                        f"Parameter '{param_name}' must be at most {prop_schema['maximum']}"
                    )
        
        # Array constraints
        if isinstance(value, list):
            if "minItems" in prop_schema:
                if len(value) < prop_schema["minItems"]:
                    raise ToolValidationError(
                        f"Parameter '{param_name}' must have at least "
                        f"{prop_schema['minItems']} items"
                    )
            
            if "maxItems" in prop_schema:
                if len(value) > prop_schema["maxItems"]:
                    raise ToolValidationError(
                        f"Parameter '{param_name}' must have at most "
                        f"{prop_schema['maxItems']} items"
                    )
    
    async def execute(self, params: Optional[Dict[str, Any]] = None) -> ToolResult:
        """
        Main tool execution method with validation, error handling, and metrics.
        
        Args:
            params: Tool parameters dictionary
            
        Returns:
            ToolResult with execution results
        """
        start_time = time.time()
        params = params or {}
        
        try:
            # Validate parameters
            validated_params = self.validate_parameters(params)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_tool(validated_params),
                timeout=self.timeout_seconds
            )
            
            # Add execution time to result
            execution_time_ms = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time_ms
            
            # Update metrics
            self._execution_count += 1
            self._total_execution_time += execution_time_ms
            
            if result.success:
                self.logger.debug(
                    f"Tool {self.name} executed successfully in {execution_time_ms:.2f}ms"
                )
            else:
                self._error_count += 1
                self.logger.warning(
                    f"Tool {self.name} execution failed: {result.error}"
                )
            
            return result
            
        except ToolValidationError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self._error_count += 1
            error_msg = f"Parameter validation failed: {str(e)}"
            self.logger.error(f"Tool {self.name} validation error: {error_msg}")
            
            return ToolResult.error_result(
                error_message=error_msg,
                execution_time_ms=execution_time_ms
            )
        
        except asyncio.TimeoutError:
            execution_time_ms = (time.time() - start_time) * 1000
            self._error_count += 1
            error_msg = f"Tool execution timed out after {self.timeout_seconds} seconds"
            self.logger.error(f"Tool {self.name} timeout: {error_msg}")
            
            return ToolResult.error_result(
                error_message=error_msg,
                execution_time_ms=execution_time_ms
            )
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self._error_count += 1
            error_msg = f"Tool execution failed: {str(e)}"
            self.logger.error(f"Tool {self.name} error: {error_msg}", exc_info=True)
            
            return ToolResult.error_result(
                error_message=error_msg,
                execution_time_ms=execution_time_ms
            )
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        Get comprehensive tool information.
        
        Returns:
            Tool information dictionary
        """
        avg_execution_time = (
            self._total_execution_time / self._execution_count
            if self._execution_count > 0 else 0.0
        )
        
        error_rate = (
            self._error_count / self._execution_count
            if self._execution_count > 0 else 0.0
        )
        
        return {
            "name": self.name,
            "description": self.description,
            "parameter_schema": self.get_parameter_schema(),
            "timeout_seconds": self.timeout_seconds,
            "performance": {
                "execution_count": self._execution_count,
                "total_execution_time_ms": self._total_execution_time,
                "average_execution_time_ms": avg_execution_time,
                "error_count": self._error_count,
                "error_rate": error_rate
            }
        }
    
    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._error_count = 0
        
        self.logger.debug(f"Reset metrics for tool {self.name}")
    
    def __str__(self) -> str:
        """String representation of the tool."""
        return f"{self.name} (executions: {self._execution_count}, errors: {self._error_count})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"{self.__class__.__name__}("
                f"name='{self.name}', "
                f"executions={self._execution_count}, "
                f"errors={self._error_count})")