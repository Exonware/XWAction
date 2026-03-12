#exonware/xwaction/base.py
"""
XWAction Abstract Base Class
Defines the contract for all action implementations.
This module fully reuses ecosystem libraries:
- xwschema: For schema definitions (XWSchema)
- xwdata: For serialization and file I/O (XWData)
  - XWData.save()/load() internally use xwsystem serialization registry
  - This provides format-agnostic serialization with automatic format detection
- xwsystem: Used indirectly through xwdata for serialization
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
from datetime import datetime
from .context import ActionContext, ActionResult
from .contracts import IAction, IActionsProvider
# Fully reuse xwschema for schema definitions
from exonware.xwschema import XWSchema
# Fully reuse xwdata for serialization and file I/O
from exonware.xwdata import XWData
# Extend XWObject for identity management
from exonware.xwsystem.shared import XWObject


class AAction(XWObject, ABC):
    """
    Enhanced Abstract Base Class for COMBINED Actions
    Provides default implementations for COMBINED features while requiring
    subclasses to implement core execution methods.
    Extends XWObject for identity management, timestamps, and metadata.
    """

    def __init__(self,
                 api_name: str,
                 func: Callable,
                 roles: Optional[list[str]] = None,
                 in_types: Optional[dict[str, XWSchema]] = None,
                 out_types: Optional[dict[str, XWSchema]] = None):
        super().__init__(object_id=api_name)
        now = datetime.now()
        self._created_at = now
        self._updated_at = now
        # Core properties
        self._api_name = api_name
        self.func = func
        self._roles = roles or ["*"]  # Default to public
        self._in_types = in_types or {}
        self._out_types = out_types or {}
        # COMBINED properties with defaults
        self._operationId: Optional[str] = None
        self._tags: list[str] = []
        self._summary: Optional[str] = None
        self._description: Optional[str] = None
        self._security_config: Any = "default"
        self._readonly: bool = False
        self._audit_enabled: bool = False
        self._cache_ttl: int = 0
        self._background_execution: bool = False
        self._workflow_steps: Optional[list[Any]] = None
        self._monitoring_config: Optional[Any] = None
        # Initialize metrics
        self._metrics = {"executions": 0, "errors": 0, "total_duration": 0.0}
        # IData engine: all IData ops delegate to _data (do not re-implement)
        self._data = XWData.from_native(self._build_native_for_data())

    def _build_native_for_data(self) -> dict[str, Any]:
        """Build native dict for _data (same shape as to_native(), used by _data)."""
        in_types_native = {}
        if self._in_types:
            for key, schema in self._in_types.items():
                if hasattr(schema, 'to_native'):
                    in_types_native[key] = schema.to_native()
                else:
                    in_types_native[key] = schema
        out_types_native = {}
        if self._out_types:
            for key, schema in self._out_types.items():
                if hasattr(schema, 'to_native'):
                    out_types_native[key] = schema.to_native()
                else:
                    out_types_native[key] = schema
        return {
            "api_name": self._api_name,
            "roles": self._roles,
            "in_types": in_types_native,
            "out_types": out_types_native,
            "operationId": self._operationId,
            "tags": self._tags,
            "summary": self._summary,
            "description": self._description,
            "readonly": self._readonly,
            "audit_enabled": self._audit_enabled,
            "cache_ttl": self._cache_ttl,
            "background_execution": self._background_execution,
            "metrics": self._metrics,
        }
    # Core Properties
    @property

    def api_name(self) -> str:
        """Get the API name of the action."""
        return self._api_name
    @property

    def roles(self) -> list[str]:
        """Get the required roles for this action."""
        return self._roles
    @property

    def in_types(self) -> dict[str, XWSchema]:
        """Get the input type schemas."""
        return self._in_types
    @property

    def out_types(self) -> dict[str, XWSchema]:
        """Get the output type schemas."""
        return self._out_types
    # COMBINED Properties
    @property

    def operationId(self) -> Optional[str]:
        """Get the OpenAPI operation ID."""
        return self._operationId
    @property

    def tags(self) -> list[str]:
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

    def workflow_steps(self) -> Optional[list[Any]]:
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
            True if valid, raises XWActionValidationError if not
        """
        pass
    @abstractmethod

    def check_permissions(self, context: ActionContext) -> bool:
        """
        Enhanced permission checking.
        Returns:
            True if allowed, raises XWActionPermissionError if not
        """
        pass
    # COMBINED Methods (default implementations)

    def get_metrics(self) -> dict[str, Any]:
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

    def to_openapi(self) -> dict[str, Any]:
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

    def _full_native_dict(self) -> dict[str, Any]:
        """Build full native dict (same as to_native(); used to sync _data). Do not re-implement."""
        import inspect
        from typing import get_type_hints
        if hasattr(self, '_signature') and self._signature is not None:
            sig = self._signature
        else:
            sig = inspect.signature(self.func)
        if hasattr(self, '_type_hints') and self._type_hints:
            hints = self._type_hints
        else:
            hints = get_type_hints(self.func)
        params = {}
        for param in sig.parameters.values():
            if param.name == 'self':
                continue
            param_info = {"type": hints.get(param.name, Any).__name__, "required": param.default == param.empty}
            if param.default != param.empty:
                param_info["default"] = param.default
            params[param.name] = param_info
        in_types_native = {}
        if self.in_types:
            for key, schema in self.in_types.items():
                in_types_native[key] = schema.to_native() if hasattr(schema, 'to_native') else schema
        out_types_native = {}
        if self.out_types:
            for key, schema in self.out_types.items():
                out_types_native[key] = schema.to_native() if hasattr(schema, 'to_native') else schema
        description = getattr(self, '_doc', None) or inspect.getdoc(self.func)
        metadata = {
            "api_name": self.api_name,
            "description": description,
            "roles": self.roles,
            "parameters": params,
            "returns": hints.get('return', Any).__name__,
        }
        if in_types_native:
            metadata["in_types"] = in_types_native
        if out_types_native:
            metadata["out_types"] = out_types_native
        if self.operationId:
            metadata["operationId"] = self.operationId
        if self.summary:
            metadata["summary"] = self.summary
        if self.tags:
            metadata["tags"] = self.tags
        if self.security_config:
            metadata["security"] = self.security_config
        metadata["readonly"] = self.readonly
        metadata["audit_enabled"] = self.audit_enabled
        if self.cache_ttl:
            metadata["cache_ttl"] = self.cache_ttl
        metadata["background_execution"] = self.background_execution
        if self.workflow_steps:
            metadata["workflow_steps"] = self.workflow_steps
        if self.monitoring_config:
            metadata["monitoring_config"] = self.monitoring_config
        metadata["metrics"] = self.get_metrics()
        if self.func:
            metadata["function_module"] = self.func.__module__
            metadata["function_qualname"] = f"{self.func.__module__}.{self.func.__qualname__}"
        return {k: v for k, v in metadata.items() if v is not None}

    def to_native(self) -> dict[str, Any]:
        """Export action metadata (delegate to _data; sync _data from attributes first). Do not re-implement."""
        self._data = XWData.from_native(self._full_native_dict())
        return self._data.to_native()

    def get_metadata(self) -> dict[str, Any]:
        """Get metadata (delegate to _data)."""
        return self._data.get_metadata()

    def get_format(self) -> Optional[str]:
        """Get format (delegate to _data)."""
        return self._data.get_format()

    async def get(self, path: str, default: Any = None) -> Any:
        """IData.get (delegate to _data)."""
        return await self._data.get(path, default)

    async def set(self, path: str, value: Any) -> IAction:
        """IData.set (delegate to _data)."""
        self._data = await self._data.set(path, value)
        return self

    async def delete(self, path: str) -> IAction:
        """IData.delete (delegate to _data)."""
        self._data = await self._data.delete(path)
        return self

    async def exists(self, path: str) -> bool:
        """IData.exists (delegate to _data)."""
        return await self._data.exists(path)

    async def serialize(self, format: str | Any, **opts) -> str | bytes:
        """IData.serialize (delegate to _data)."""
        return await self._data.serialize(format, **opts)

    async def save(self, path: str | Any, format: Optional[str] = None, **opts) -> IAction:
        """IData.save (delegate to _data)."""
        await self._data.save(path, format=format, **opts)
        return self

    async def merge(self, other: Any, strategy: str = 'deep') -> IAction:
        """IData.merge (delegate to _data)."""
        if other is not None and hasattr(other, '_data'):
            self._data = await self._data.merge(other._data, strategy=strategy)
        return self

    async def transform(self, transformer: Any) -> IAction:
        """IData.transform (delegate to _data)."""
        self._data = await self._data.transform(transformer)
        return self

    def to_format(self, format: str | Any, **opts) -> str | bytes:
        """IData.to_format (delegate to _data)."""
        return self._data.to_format(format, **opts)

    def to_file(self, path: str, format: str = "json") -> bool:
        """Save action to file (delegate to _data). Do not re-implement."""
        self._data = XWData.from_native(self._full_native_dict())
        self._data.to_file(path, format_hint=format)
        return True

    def to_descriptor(self) -> dict[str, Any]:
        """
        Export lightweight descriptor for registry/documentation.
        Returns:
            Dictionary with lightweight action metadata
        """
        import inspect
        from typing import get_type_hints
        # Use cached introspection if available (set by facade during decoration)
        if not hasattr(self, '_signature') or self._signature is None:
            self._signature = inspect.signature(self.func)
        if not hasattr(self, '_hints') or not self._hints:
            self._hints = get_type_hints(self.func)
        if not hasattr(self, '_doc'):
            self._doc = inspect.getdoc(self.func)
        if not hasattr(self, '_is_async'):
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
                schema = self.in_types[param.name]
                if hasattr(schema, 'to_native'):
                    param_info.update(schema.to_native())
            params[param.name] = param_info
        descriptor = {
            "api_name": self.api_name,
            "description": self._doc,
            "roles": self.roles,
            "is_async": getattr(self, '_is_async', False),
            "parameters": params,
            "returns": self._hints.get('return', Any).__name__
        }
        # Add optional fields if they exist
        if self.operationId:
            descriptor["operationId"] = self.operationId
        if hasattr(self, 'cmd_shortcut') and getattr(self, 'cmd_shortcut', None):
            descriptor["cmd_shortcut"] = self.cmd_shortcut
        return descriptor
    # ============================================================================
    # XWObject Implementation (required abstract methods)
    # ============================================================================
    @property

    def id(self) -> str:
        """Get the unique object identifier (api_name)."""
        return self._id
    @property

    def created_at(self) -> datetime:
        """Get the creation timestamp."""
        return self._created_at
    @property

    def updated_at(self) -> datetime:
        """Get the last update timestamp."""
        return self._updated_at

    def to_dict(self) -> dict[str, Any]:
        """
        Export action as dictionary.
        Includes XWObject fields (id, uid, created_at, updated_at, title, description)
        and action-specific data.
        """
        result = {
            "id": self.id,
            "uid": self.uid,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "api_name": self.api_name,
            "operationId": self.operationId,
        }
        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        if self.summary:
            result["summary"] = self.summary
        if self.tags:
            result["tags"] = self.tags
        return result

    def save(self, *args, **kwargs) -> None:
        """
        Save action metadata to storage.
        This saves the action definition metadata (id, uid, timestamps, etc.).
        """
        # Update timestamp before saving
        self._updated_at = datetime.now()
        # Action metadata persistence would be implemented here
        from exonware.xwsystem import get_logger
        logger = get_logger(__name__)
        logger.debug(f"Saving action metadata: {self.api_name}")

    def load(self, *args, **kwargs) -> None:
        """
        Load action metadata from storage.
        This loads the action definition metadata.
        """
        # Action metadata loading would be implemented here
        from exonware.xwsystem import get_logger
        logger = get_logger(__name__)
        logger.debug(f"Loading action metadata: {self.api_name}")


class AActionsProvider(IActionsProvider, ABC):
    """
    Abstract base for providers that expose @XWAction command names.
    Subclasses implement get_action_command_names(); print_commands() prints them to the console.
    """

    @abstractmethod
    def get_action_command_names(self) -> list[str]:
        """
        Return the list of command names (e.g. cmd_shortcut) from @XWAction-decorated methods.
        Returns:
            Sorted list of command name strings
        """
        pass

    def print_commands(self) -> None:
        """Print all action command names to the console (one per line, with leading /)."""
        for cmd in self.get_action_command_names():
            print(f"  /{cmd}")
