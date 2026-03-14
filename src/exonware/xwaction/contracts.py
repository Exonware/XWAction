#exonware/xwaction/contracts.py
"""
XWAction Contracts
Interfaces and protocols for action system.
"""

from __future__ import annotations
from typing import Any, Protocol, runtime_checkable
from dataclasses import dataclass
from .context import ActionContext, ActionResult
from .defs import ActionProfile, ActionHandlerPhase
from exonware.xwschema import XWSchema
from exonware.xwsystem.shared import IObject
from collections.abc import Callable


@runtime_checkable
class IAction(IObject, Protocol):
    """
    Enhanced Interface for COMBINED Action Implementations
    Defines the comprehensive contract that all actions must follow,
    including COMBINED features like OpenAPI compliance, security,
    workflows, monitoring, and more.
    Extends IData (xwdata) so action can be a sub-node in XWData; implementations
    MUST use _data: XWData and delegate IData operations to it (do not re-implement).
    Extends IObject for identity management, timestamps, and metadata.
    """
    # Core Properties
    @property

    def api_name(self) -> str:
        """Get the API name of the action."""
        ...
    @property

    def roles(self) -> list[str]:
        """Get the required roles for this action."""
        ...
    @property

    def in_types(self) -> dict[str, XWSchema]:
        """Get the input type schemas."""
        ...
    @property

    def out_types(self) -> dict[str, XWSchema]:
        """Get the output type schemas."""
        ...
    # COMBINED Properties
    @property

    def operationId(self) -> str | None:
        """Get the OpenAPI operation ID."""
        ...
    @property

    def tags(self) -> list[str]:
        """Get the OpenAPI tags for grouping."""
        ...
    @property

    def summary(self) -> str | None:
        """Get the action summary."""
        ...
    @property

    def description(self) -> str | None:
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

    def workflow_steps(self) -> list[Any] | None:
        """Get workflow steps if defined."""
        ...
    @property

    def monitoring_config(self) -> Any | None:
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
            True if valid, raises XWActionValidationError if not
        """
        ...

    def check_permissions(self, context: ActionContext) -> bool:
        """
        Enhanced permission checking.
        Returns:
            True if allowed, raises XWActionPermissionError if not
        """
        ...
    # COMBINED Methods

    def get_metrics(self) -> dict[str, Any]:
        """
        Get action execution metrics.
        Returns:
            Dictionary with execution statistics
        """
        ...

    def to_openapi(self) -> dict[str, Any]:
        """
        Export action as OpenAPI 3.1 operation.
        Returns:
            OpenAPI operation specification
        """
        ...
    # Standard Export Methods

    def to_native(self) -> dict[str, Any]:
        """
        Export comprehensive action metadata.
        Returns:
            Dictionary with complete action metadata including COMBINED features
        """
        ...

    def to_file(self, path: str, format: str = "json") -> bool:
        """
        Save action to file.
        Args:
            path: File path to save to
            format: File format (json, yaml, etc.)
        Returns:
            True if successful
        """
        ...

    def to_descriptor(self) -> dict[str, Any]:
        """
        Export lightweight descriptor for registry/documentation.
        Returns:
            Dictionary with essential action metadata
        """
        ...
    @staticmethod

    def create(
        func: Callable,
        api_name: str | None = None,
        roles: list[str] | None = None,
        in_types: dict[str, XWSchema] | None = None,
        out_types: dict[str, XWSchema] | None = None,
    ) -> IAction:
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

    def from_native(data: dict[str, Any]) -> IAction:
        """
        Create action from dictionary.
        Args:
            data: Dictionary with action metadata
        Returns:
            Action instance
        """
        ...
    @staticmethod

    def from_file(path: str, format: str = "json") -> IAction:
        """
        Load action from file.
        Args:
            path: File path to load from
            format: File format (json, yaml, etc.)
        Returns:
            Action instance
        """
        ...


class IActionEngine(Protocol):
    """Action Engine Interface."""
    @property

    def name(self) -> str:
        """Get the name of this action engine."""
        ...
    @property

    def priority(self) -> int:
        """Get the priority of this action engine."""
        ...

    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """Check if this action engine can execute the given action."""
        ...

    def execute(self, action: IAction, context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """Execute an action using this action engine."""
        ...


class IActionHandler(Protocol):
    """Action Handler Interface."""
    @property

    def name(self) -> str:
        """Get the name of this action handler."""
        ...
    @property

    def priority(self) -> int:
        """Get the priority of this action handler."""
        ...
    @property

    def supported_phases(self) -> set[ActionHandlerPhase]:
        """Get the phases this action handler supports."""
        ...
    @property

    def async_enabled(self) -> bool:
        """Whether this action handler supports async execution."""
        ...

    def before_execution(self, action: IAction, context: ActionContext, **kwargs) -> bool:
        """Execute before action execution."""
        ...

    def after_execution(self, action: IAction, context: ActionContext, result: Any) -> bool:
        """Execute after successful action execution."""
        ...

    def on_error(self, action: IAction, context: ActionContext, error: Exception) -> bool:
        """Execute when an error occurs during action execution."""
        ...
@dataclass


class AuthzDecision:
    """
    Authorization decision result.
    Provides detailed information about authorization decisions for audit and debugging.
    Similar to OAuth 2.0 authorization decision pattern.
    """
    allowed: bool
    reason: str | None = None
    subject: str | None = None  # User/principal identifier
    scopes: list[str] | None = None
    roles: list[str] | None = None
    permissions: list[str] | None = None
    policy_id: str | None = None
@runtime_checkable


class IActionAuthorizer(Protocol):
    """
    Interface for action authorization.
    Allows xwaction to use authorization without directly importing xwauth.
    Similar to OAuth 2.0 authorization pattern.
    Implementations should be provided by authorization systems (e.g., xwauth)
    and can be set on actions via set_authorizer() method.
    """

    def authorize(
        self,
        action: IAction,
        context: ActionContext
    ) -> AuthzDecision:
        """
        Authorize an action execution.
        Args:
            action: The action to authorize
            context: Execution context with security info
        Returns:
            AuthzDecision with authorization result and metadata
        Raises:
            Only for system errors (token invalid, backend down), not "denied"
            Denied decisions should return AuthzDecision(allowed=False, ...)
        """
        ...


@runtime_checkable
class IActionsProvider(Protocol):
    """
    Interface for providers that expose @XWAction command names.
    Implementations provide get_action_command_names(); print_commands() is offered by AActionsProvider.
    """

    def get_action_command_names(self) -> list[str]:
        """
        Return the list of command names (e.g. cmd_shortcut) from @XWAction-decorated methods.
        Returns:
            Sorted list of command name strings
        """
        ...
