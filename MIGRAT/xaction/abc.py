#!/usr/bin/env python3
"""
🏗️ xAction Abstract Base Class
Defines the contract for all action implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable, Protocol, runtime_checkable
from datetime import datetime
from src.xlib.xdata import xSchema

class ActionContext:
    """Execution context for actions."""
    
    def __init__(self, 
                 actor: Optional[str] = None,
                 source: str = "internal",
                 trace_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.actor = actor  # Who's executing
        self.timestamp = datetime.now()  # When
        self.source = source  # Where from (api, cli, internal)
        self.trace_id = trace_id or self._generate_trace_id()
        self.metadata = metadata or {}
    
    @staticmethod
    def _generate_trace_id() -> str:
        """Generate a simple trace ID."""
        import uuid
        return str(uuid.uuid4())


class ActionResult:
    """Standardized result wrapper."""
    
    def __init__(self, 
                 success: bool,
                 data: Any = None,
                 error: Optional[str] = None,
                 duration: float = 0.0,
                 metadata: Optional[Dict[str, Any]] = None):
        self.success = success
        self.data = data
        self.error = error
        self.duration = duration  # Execution time in seconds
        self.metadata = metadata or {}


@runtime_checkable
class iAction(Protocol):
    """
    🌟 Enhanced Interface for COMBINED Action Implementations
    
    Defines the comprehensive contract that all actions must follow,
    including COMBINED features like OpenAPI compliance, security,
    workflows, monitoring, and more.
    """
    
    # Core Properties
    @property
    def api_name(self) -> str:
        """Get the API name of the action."""
        ...
    
    @property
    def roles(self) -> List[str]:
        """Get the required roles for this action."""
        ...
    
    @property
    def in_types(self) -> Dict[str, xSchema]:
        """Get the input type schemas."""
        ...
    
    @property
    def out_types(self) -> Dict[str, xSchema]:
        """Get the output type schemas."""
        ...
    
    # COMBINED Properties
    @property
    def operationId(self) -> Optional[str]:
        """Get the OpenAPI operation ID."""
        ...
    
    @property
    def tags(self) -> List[str]:
        """Get the OpenAPI tags for grouping."""
        ...
    
    @property
    def summary(self) -> Optional[str]:
        """Get the action summary."""
        ...
    
    @property
    def description(self) -> Optional[str]:
        """Get the action description."""
        ...
    
    @property
    def security_config(self) -> Any:
        """Get the security configuration."""
        ...
    
    @property
    def readonly(self) -> bool:
        """Check if action is read-only."""
        ...
    
    @property
    def audit_enabled(self) -> bool:
        """Check if audit logging is enabled."""
        ...
    
    @property
    def cache_ttl(self) -> int:
        """Get cache TTL in seconds."""
        ...
    
    @property
    def background_execution(self) -> bool:
        """Check if action runs in background."""
        ...
    
    @property
    def workflow_steps(self) -> Optional[List[Any]]:
        """Get workflow steps if defined."""
        ...
    
    @property
    def monitoring_config(self) -> Optional[Any]:
        """Get monitoring configuration."""
        ...
    
    # Core Methods
    def execute(self, context: ActionContext, instance: Any, **kwargs) -> ActionResult:
        """
        Execute the action with comprehensive COMBINED features.
        
        Args:
            context: Execution context with security info
            instance: The entity instance (self in decorated method)
            **kwargs: Action parameters
            
        Returns:
            ActionResult with success/failure and enhanced metadata
        """
        ...
    
    def validate_input(self, **kwargs) -> bool:
        """
        Enhanced input validation with contracts and schemas.
        
        Returns:
            True if valid, raises xActionValidationError if not
        """
        ...
    
    def check_permissions(self, context: ActionContext) -> bool:
        """
        Enhanced permission checking with xAuth integration.
        
        Returns:
            True if allowed, raises xActionPermissionError if not
        """
        ...
    
    # COMBINED Methods
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get action execution metrics.
        
        Returns:
            Dictionary with execution statistics
        """
        ...
    
    def to_openapi(self) -> Dict[str, Any]:
        """
        Export action as OpenAPI 3.1 operation.
        
        Returns:
            OpenAPI operation specification
        """
        ...
    
    # Standard Export Methods
    def to_native(self) -> Dict[str, Any]:
        """
        Export comprehensive action metadata.
        
        Returns:
            Dictionary with complete action metadata including COMBINED features
        """
        ...
    
    def to_file(self, path: str, format: str = "json") -> bool:
        """
        Save action to file using xData.
        
        Args:
            path: File path to save to
            format: File format (json, yaml, etc.)
            
        Returns:
            True if successful
        """
        ...
    
    def to_descriptor(self) -> Dict[str, Any]:
        """
        Export lightweight descriptor for registry/documentation.
        
        Returns:
            Dictionary with essential action metadata
        """
        ...
    
    @staticmethod
    def create(func: Callable, api_name: Optional[str] = None,
               roles: Optional[List[str]] = None,
               in_types: Optional[Dict[str, xSchema]] = None,
               out_types: Optional[Dict[str, xSchema]] = None) -> 'iAction':
        """
        Create an action instance from a function.
        
        Args:
            func: The function to wrap
            api_name: Optional API name
            roles: Optional list of required roles
            in_types: Optional input type schemas
            out_types: Optional output type schemas
            
        Returns:
            Action instance
        """
        ...
    
    @staticmethod
    def from_native(data: Dict[str, Any]) -> 'iAction':
        """
        Create action from dictionary.
        
        Args:
            data: Dictionary with action metadata
            
        Returns:
            Action instance
        """
        ...
    
    @staticmethod
    def from_file(path: str, format: str = "json") -> 'iAction':
        """
        Load action from file.
        
        Args:
            path: File path to load from
            format: File format (json, yaml, etc.)
            
        Returns:
            Action instance
        """
        ...


class aAction(ABC):
    """
    🌟 Enhanced Abstract Base Class for COMBINED Actions
    
    Provides default implementations for COMBINED features while requiring
    subclasses to implement core execution methods.
    """
    
    def __init__(self,
                 api_name: str,
                 func: Callable,
                 roles: Optional[List[str]] = None,
                 in_types: Optional[Dict[str, xSchema]] = None,
                 out_types: Optional[Dict[str, xSchema]] = None):
        # Core properties
        self._api_name = api_name
        self.func = func
        self._roles = roles or ["*"]  # Default to public
        self._in_types = in_types or {}
        self._out_types = out_types or {}
        
        # COMBINED properties with defaults
        self._operationId: Optional[str] = None
        self._tags: List[str] = []
        self._summary: Optional[str] = None
        self._description: Optional[str] = None
        self._security_config: Any = "default"
        self._readonly: bool = False
        self._audit_enabled: bool = False
        self._cache_ttl: int = 0
        self._background_execution: bool = False
        self._workflow_steps: Optional[List[Any]] = None
        self._monitoring_config: Optional[Any] = None
        
        # Initialize metrics
        self._metrics = {"executions": 0, "errors": 0, "total_duration": 0.0}
    
    # Core Properties
    @property
    def api_name(self) -> str:
        """Get the API name of the action."""
        return self._api_name
    
    @property
    def roles(self) -> List[str]:
        """Get the required roles for this action."""
        return self._roles
    
    @property
    def in_types(self) -> Dict[str, xSchema]:
        """Get the input type schemas."""
        return self._in_types
    
    @property
    def out_types(self) -> Dict[str, xSchema]:
        """Get the output type schemas."""
        return self._out_types
    
    # COMBINED Properties
    @property
    def operationId(self) -> Optional[str]:
        """Get the OpenAPI operation ID."""
        return self._operationId
    
    @property
    def tags(self) -> List[str]:
        """Get the OpenAPI tags for grouping."""
        return self._tags
    
    @property
    def summary(self) -> Optional[str]:
        """Get the action summary."""
        return self._summary
    
    @property
    def description(self) -> Optional[str]:
        """Get the action description."""
        return self._description
    
    @property
    def security_config(self) -> Any:
        """Get the security configuration."""
        return self._security_config
    
    @property
    def readonly(self) -> bool:
        """Check if action is read-only."""
        return self._readonly
    
    @property
    def audit_enabled(self) -> bool:
        """Check if audit logging is enabled."""
        return self._audit_enabled
    
    @property
    def cache_ttl(self) -> int:
        """Get cache TTL in seconds."""
        return self._cache_ttl
    
    @property
    def background_execution(self) -> bool:
        """Check if action runs in background."""
        return self._background_execution
    
    @property
    def workflow_steps(self) -> Optional[List[Any]]:
        """Get workflow steps if defined."""
        return self._workflow_steps
    
    @property
    def monitoring_config(self) -> Optional[Any]:
        """Get monitoring configuration."""
        return self._monitoring_config
    
    # Abstract Methods (must be implemented by subclasses)
    @abstractmethod
    def execute(self, context: ActionContext, instance: Any, **kwargs) -> ActionResult:
        """
        Execute the action with comprehensive COMBINED features.
        
        Args:
            context: Execution context with security info
            instance: The entity instance (self in decorated method)
            **kwargs: Action parameters
            
        Returns:
            ActionResult with success/failure and enhanced metadata
        """
        pass
    
    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """
        Enhanced input validation with contracts and schemas.
        
        Returns:
            True if valid, raises xActionValidationError if not
        """
        pass
    
    @abstractmethod
    def check_permissions(self, context: ActionContext) -> bool:
        """
        Enhanced permission checking with xAuth integration.
        
        Returns:
            True if allowed, raises xActionPermissionError if not
        """
        pass
    
    # COMBINED Methods (default implementations)
    def get_metrics(self) -> Dict[str, Any]:
        """Get action execution metrics."""
        avg_duration = (
            self._metrics["total_duration"] / self._metrics["executions"]
            if self._metrics["executions"] > 0 else 0.0
        )
        
        error_rate = (
            self._metrics["errors"] / self._metrics["executions"]
            if self._metrics["executions"] > 0 else 0.0
        )
        
        return {
            "executions": self._metrics["executions"],
            "errors": self._metrics["errors"],
            "total_duration": self._metrics["total_duration"],
            "average_duration": avg_duration,
            "error_rate": error_rate
        }
    
    def to_openapi(self) -> Dict[str, Any]:
        """Export action as OpenAPI 3.1 operation (basic implementation)."""
        return {
            "operationId": self.operationId or self.api_name,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "responses": {
                "200": {"description": "Success"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"}
            }
        }
    
    def _update_metrics(self, duration: float, success: bool):
        """Update execution metrics."""
        self._metrics["executions"] += 1
        self._metrics["total_duration"] += duration
        if not success:
            self._metrics["errors"] += 1
    
    def to_native(self) -> Dict[str, Any]:
        """
        Export enhanced action metadata with COMBINED features.
        
        Returns:
            Dictionary with comprehensive action metadata
        """
        import inspect
        from typing import get_type_hints
        
        # Get function signature and type hints
        sig = inspect.signature(self.func)
        hints = get_type_hints(self.func)
        
        # Extract parameters
        params = {}
        for param in sig.parameters.values():
            if param.name == 'self':
                continue
            
            param_info = {
                "type": hints.get(param.name, Any).__name__,
                "required": param.default == param.empty,
            }
            
            if param.default != param.empty:
                param_info["default"] = param.default
                
            params[param.name] = param_info
        
        # Convert xSchema objects to native format
        in_types_native = {}
        for key, schema in self.in_types.items():
            if hasattr(schema, 'to_native'):
                in_types_native[key] = schema.to_native()
            else:
                in_types_native[key] = schema
        
        out_types_native = {}
        for key, schema in self.out_types.items():
            if hasattr(schema, 'to_native'):
                out_types_native[key] = schema.to_native()
            else:
                out_types_native[key] = schema
        
        # Build enhanced metadata with COMBINED features
        metadata = {
            # Core metadata
            "api_name": self.api_name,
            "description": inspect.getdoc(self.func),
            "roles": self.roles,
            "parameters": params,
            "returns": hints.get('return', Any).__name__,
            "in_types": in_types_native,
            "out_types": out_types_native,
            
            # COMBINED metadata
            "operationId": self.operationId,
            "summary": self.summary,
            "tags": self.tags,
            "security": self.security_config,
            "readonly": self.readonly,
            "audit_enabled": self.audit_enabled,
            "cache_ttl": self.cache_ttl,
            "background_execution": self.background_execution,
            "workflow_steps": self.workflow_steps,
            "monitoring_config": self.monitoring_config,
            "metrics": self.get_metrics()
        }
        
        # Add function qualification for reconstruction
        if self.func:
            metadata["function_module"] = self.func.__module__
            metadata["function_qualname"] = f"{self.func.__module__}.{self.func.__qualname__}"
        
        # Remove None values for cleaner output
        return {k: v for k, v in metadata.items() if v is not None}
    
    def to_file(self, path: str, format: str = "json") -> bool:
        """
        Save action to file using xData.
        
        Args:
            path: File path to save to
            format: File format (json, yaml, etc.)
            
        Returns:
            True if successful
        """
        from src.xlib.xdata import xData
        
        data = self.to_native()
        xdata_instance = xData(data)
        xdata_instance.to_file(path, format_hint=format)
        return True
    
    def to_descriptor(self) -> Dict[str, Any]:
        """
        Export lightweight descriptor for registry/documentation.
        
        Returns:
            Dictionary with lightweight action metadata
        """
        import inspect
        from typing import get_type_hints
        
        # Cache introspection if not already done
        if not hasattr(self, '_signature'):
            self._signature = inspect.signature(self.func)
            self._hints = get_type_hints(self.func)
            self._doc = inspect.getdoc(self.func)
            self._is_async = inspect.iscoroutinefunction(self.func)
        
        params = {}
        for param in self._signature.parameters.values():
            if param.name == 'self':
                continue
            
            param_info = {
                "type": self._hints.get(param.name, Any).__name__,
                "required": param.default == param.empty,
            }
            
            if param.default != param.empty:
                param_info["default"] = param.default
                
            # Merge with type constraints
            if param.name in self.in_types:
                param_info.update(self.in_types[param.name].to_native())
                
            params[param.name] = param_info
        
        return {
            "api_name": self.api_name,
            "description": self._doc,
            "roles": self.roles,
            "is_async": self._is_async,
            "parameters": params,
            "returns": self._hints.get('return', Any).__name__
        } 