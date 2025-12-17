#exonware/xwaction/contracts.py
"""
XWAction Contracts
Interfaces and protocols for action system.
"""

from typing import Any, Dict, Optional, List, Callable, Protocol, runtime_checkable
from .context import ActionContext, ActionResult
from .defs import ActionProfile, ActionHandlerPhase

# Import XWSchema conditionally to avoid circular dependencies
try:
    from exonware.xwschema import XWSchema
except ImportError:
    XWSchema = Any  # Fallback for type hints


@runtime_checkable
class iAction(Protocol):
    """
    Enhanced Interface for COMBINED Action Implementations
    
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
    def in_types(self) -> Dict[str, XWSchema]:
        """Get the input type schemas."""
        ...
    
    @property
    def out_types(self) -> Dict[str, XWSchema]:
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
        Save action to file.
        
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
               in_types: Optional[Dict[str, XWSchema]] = None,
               out_types: Optional[Dict[str, XWSchema]] = None) -> 'iAction':
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


class iActionEngine(Protocol):
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
    
    def execute(self, action: 'iAction', context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """Execute an action using this action engine."""
        ...


class iActionHandler(Protocol):
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
    
    def before_execution(self, action: 'iAction', context: ActionContext, **kwargs) -> bool:
        """Execute before action execution."""
        ...
    
    def after_execution(self, action: 'iAction', context: ActionContext, result: Any) -> bool:
        """Execute after successful action execution."""
        ...
    
    def on_error(self, action: 'iAction', context: ActionContext, error: Exception) -> bool:
        """Execute when an error occurs during action execution."""
        ...

