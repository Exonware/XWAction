#!/usr/bin/env python3
"""
🎯 xAction Facade - Modular Implementation
Production-grade action decorator with comprehensive features.
"""

from typing import Any, Dict, Optional, List, Callable, Union
import inspect
import time
from functools import wraps

from .abc import aAction, iAction
from .core import (
    ActionProfile, ProfileConfig, PROFILE_CONFIGS,
    ActionContext, ActionResult,
    action_executor, action_validator, openapi_generator
)
from .model import ActionRegistry
from .errors import xActionError, xActionValidationError, xActionExecutionError, xActionPermissionError
from src.xlib.xdata.core.exceptions import SchemaValidationError
from src.xlib.xwsystem import get_logger

# Direct import for validation and documentation
from src.xlib.xdata import xSchema

logger = get_logger(__name__)


class xAction(aAction):
    """
    🌟 xAction Decorator
    
    Production-grade action decorator with comprehensive features:
    - Smart inference with profiles and convention-based defaults
    - OpenAPI 3.1 compliance for full API documentation
    - Security integration with xAuth (OAuth2, API keys, MFA, rate limiting)
    - Workflow orchestration with monitoring and rollback
    - Contract validation with xSchema integration
    - Pluggable engine system (Native, FastAPI, Celery, Prefect)
    - Cross-cutting concerns handlers (Validation, Security, Monitoring, Workflow)
    """
    
    def __init__(self,
                 # Core identity (OpenAPI-compliant)
                 operationId: Optional[str] = None,
                 api_name: Optional[str] = None,
                 summary: Optional[str] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 
                 # Smart inference and profiles
                 profile: Union[str, ActionProfile, None] = None,
                 smart_mode: Union[str, bool] = False,
                 
                 # Security (xAuth integration)
                 security: Union[str, List[str], Dict[str, List[str]], None] = None,
                 roles: Optional[List[str]] = None,
                 rate_limit: Optional[str] = None,
                 audit: Optional[bool] = None,
                 mfa_required: bool = False,
                 
                 # Execution control
                 engine: Union[str, List[str], None] = None,
                 handlers: Optional[List[str]] = None,
                 readonly: Optional[bool] = None,
                 idempotent: Optional[bool] = None,
                 cache_ttl: Optional[int] = None,
                 background: Optional[bool] = None,
                 timeout: Optional[float] = None,
                 
                 # Retry and resilience
                 retry: Union[int, Dict[str, Any], None] = None,
                 circuit_breaker: Optional[bool] = None,
                 
                 # Workflow and monitoring
                 steps: Optional[List[Dict[str, Any]]] = None,
                 monitor: Union[Dict[str, Any], None] = None,
                 rollback: Optional[bool] = None,
                 
                 # Contract validation
                 contracts: Union[Dict[str, Any], None] = None,
                 in_types: Optional[Dict[str, xSchema]] = None,
                 out_types: Optional[Dict[str, xSchema]] = None,
                 
                 # Dependencies (FastAPI-style)
                 dependencies: Optional[List[Callable]] = None,
                 
                 # OpenAPI documentation
                 responses: Optional[Dict[int, Dict[str, str]]] = None,
                 examples: Optional[Dict[str, Any]] = None,
                 deprecated: bool = False,
                 
                 # Internal
                 func: Optional[Callable] = None):
        """
        Initialize xAction decorator.
        
        Args:
            operationId: OpenAPI operation ID
            api_name: API name (backward compatibility)
            summary: Action summary
            description: Action description
            tags: OpenAPI tags
            profile: Action profile (query, command, task, workflow, endpoint)
            smart_mode: Enable smart inference
            security: Security configuration
            roles: Required roles
            rate_limit: Rate limiting configuration
            audit: Enable audit logging
            mfa_required: Require MFA
            engine: Execution engine(s)
            handlers: Cross-cutting concerns handlers
            readonly: Read-only operation
            idempotent: Idempotent operation
            cache_ttl: Cache TTL in seconds
            background: Background execution
            timeout: Execution timeout
            retry: Retry configuration
            circuit_breaker: Circuit breaker configuration
            steps: Workflow steps
            monitor: Monitoring configuration
            rollback: Enable rollback
            contracts: Contract validation
            in_types: Input type validation (backward compatibility)
            out_types: Output type validation (backward compatibility)
            dependencies: FastAPI-style dependencies
            responses: OpenAPI responses
            examples: OpenAPI examples
            deprecated: Deprecated flag
            func: Function to decorate
        """
        # Store configuration
        self._operationId = operationId
        self._api_name = api_name
        self._summary = summary
        self._description = description
        self._tags = tags or []
        self._security = security
        self._roles = roles or []
        self._rate_limit = rate_limit
        self._audit = audit
        self._mfa_required = mfa_required
        self._engine = engine
        self._handlers = handlers or []
        self._readonly = readonly
        self._idempotent = idempotent
        self._cache_ttl = cache_ttl
        self._background = background
        self._timeout = timeout
        self._retry = retry
        self._circuit_breaker = circuit_breaker
        self._steps = steps
        self._monitor = monitor
        self._rollback = rollback
        self._contracts = contracts
        self._in_types = in_types
        self._out_types = out_types
        self._dependencies = dependencies
        self._responses = responses
        self._examples = examples
        self._deprecated = deprecated
        self._func = func
        
        # Resolve profile
        self._profile = self._resolve_profile(profile, smart_mode)
        
        # Get profile configuration
        profile_config = PROFILE_CONFIGS.get(self._profile, ProfileConfig())
        
        # Merge configuration
        self._config = self._merge_configuration(profile_config)
        
        # Store combined configuration
        self._store_combined_config(self._config, self._profile)
        
        # Register with registry
        ActionRegistry.register("default", self)
    
    @property
    def operationId(self) -> Optional[str]:
        """Get OpenAPI operation ID."""
        return self._operationId
    
    @property
    def api_name(self) -> str:
        """Get API name."""
        return self._api_name or self._func.__name__ if self._func else "unknown"
    
    @property
    def summary(self) -> Optional[str]:
        """Get action summary."""
        return self._summary
    
    @property
    def description(self) -> Optional[str]:
        """Get action description."""
        return self._description
    
    @property
    def tags(self) -> List[str]:
        """Get OpenAPI tags."""
        return self._tags
    
    @property
    def security_config(self) -> Any:
        """Get security configuration."""
        return self._security
    
    @property
    def roles(self) -> List[str]:
        """Get required roles."""
        return self._roles
    
    @property
    def rate_limit(self) -> Optional[str]:
        """Get rate limit configuration."""
        return self._rate_limit
    
    @property
    def audit_enabled(self) -> bool:
        """Check if audit is enabled."""
        return self._combined_config.get("audit", False) if hasattr(self, '_combined_config') else (self._audit or False)
    
    @property
    def readonly(self) -> bool:
        """Check if action is read-only."""
        return self._readonly or False
    
    @property
    def cache_ttl(self) -> int:
        """Get cache TTL."""
        return self._cache_ttl or 0
    
    @property
    def background_execution(self) -> bool:
        """Check if action is background execution."""
        return self._background or False
    
    @property
    def workflow_steps(self) -> Optional[List[Any]]:
        """Get workflow steps."""
        return self._steps
    
    @property
    def monitoring_config(self) -> Optional[Any]:
        """Get monitoring configuration."""
        return self._monitor
    
    @property
    def contract_config(self) -> Optional[Any]:
        """Get contract configuration."""
        return self._contracts
    
    @property
    def responses(self) -> Dict[int, Dict[str, str]]:
        """Get OpenAPI responses."""
        return self._responses or {}
    
    @property
    def examples(self) -> Dict[str, Any]:
        """Get OpenAPI examples."""
        return self._examples or {}
    
    @property
    def profile(self) -> ActionProfile:
        """Get action profile."""
        return self._profile
    
    @property
    def engines(self) -> List[str]:
        """Get configured engines."""
        if hasattr(self, '_combined_config') and self._combined_config.get("engine"):
            engine_config = self._combined_config["engine"]
            if isinstance(engine_config, str):
                return [engine_config]
            elif isinstance(engine_config, list):
                return engine_config
        return self._engine or ["native"]
    
    @property
    def handlers(self) -> List[str]:
        """Get configured handlers."""
        return self._handlers
    
    @property
    def in_types(self) -> Optional[Dict[str, xSchema]]:
        """Get input type validation."""
        return self._in_types
    
    @property
    def out_types(self) -> Optional[Dict[str, xSchema]]:
        """Get output type validation."""
        return self._out_types
    
    @property
    def func(self) -> Optional[Callable]:
        """Get decorated function."""
        return self._func
    
    @property
    def deprecated(self) -> bool:
        """Check if action is deprecated."""
        return self._deprecated
    
    def _resolve_profile(self, profile: Union[str, ActionProfile, None], 
                        smart_mode: Union[str, bool]) -> ActionProfile:
        """Resolve action profile."""
        if profile:
            if isinstance(profile, str):
                return ActionProfile(profile)
            elif isinstance(profile, ActionProfile):
                return profile
        
        # Default to ACTION profile
        return ActionProfile.ACTION
    
    def _merge_configuration(self, profile_config: ProfileConfig) -> Dict[str, Any]:
        """Merge configuration with profile defaults."""
        config = {
            "operationId": self._operationId,
            "api_name": self._api_name,
            "summary": self._summary,
            "description": self._description,
            "tags": self._tags,
            "security": self._security or profile_config.security,
            "roles": self._roles,
            "rate_limit": self._rate_limit or profile_config.rate_limit,
            "audit": self._audit if self._audit is not None else profile_config.audit,
            "mfa_required": self._mfa_required,
            "engine": self._engine or profile_config.engine,
            "handlers": self._handlers,
            "readonly": self._readonly if self._readonly is not None else profile_config.readonly,
            "idempotent": self._idempotent,
            "cache_ttl": self._cache_ttl or profile_config.cache_ttl,
            "background": self._background if self._background is not None else profile_config.background,
            "timeout": self._timeout or profile_config.timeout,
            "retry": self._retry or profile_config.retry_attempts,
            "circuit_breaker": self._circuit_breaker,
            "steps": self._steps,
            "monitor": self._monitor,
            "rollback": self._rollback,
            "contracts": self._contracts,
            "in_types": self._in_types,
            "out_types": self._out_types,
            "dependencies": self._dependencies,
            "responses": self._responses,
            "examples": self._examples,
            "deprecated": self._deprecated
        }
        
        return config
    
    def _store_combined_config(self, config: Dict[str, Any], profile: ActionProfile):
        """Store combined configuration."""
        self._combined_config = config
        self._profile = profile
    
    def __call__(self, func_or_smart: Union[Callable, str, None] = None):
        """Handle decorator usage."""
        # Handle smart mode shortcut: @xAction("smart")
        if isinstance(func_or_smart, str) and func_or_smart == "smart":
            def smart_decorator(func: Callable):
                return self._create_smart_action(func)
            return smart_decorator
            
        # Handle direct function decoration: @xAction
        if func_or_smart is not None and callable(func_or_smart):
            return self._decorate(func_or_smart)
            
        # Handle parameterized decoration: @xAction(...)
        def decorator(func: Callable):
            return self._decorate(func)
        return decorator
    
    def _create_smart_action(self, func: Callable):
        """Create a smart action with inference."""
        smart_action = xAction(smart_mode="smart", func=func)
        return smart_action._decorate(func)
    
    @classmethod
    def create(cls, func: Callable, api_name: Optional[str] = None,
               roles: Optional[List[str]] = None,
               in_types: Optional[Dict[str, xSchema]] = None,
               out_types: Optional[Dict[str, xSchema]] = None,
               **kwargs) -> iAction:
        """Create an xAction instance from a function."""
        return cls(
            api_name=api_name,
            roles=roles,
            in_types=in_types,
            out_types=out_types,
            func=func,
            **kwargs
        )
    
    def _decorate(self, func: Callable):
        """Decorate a function with xAction functionality."""
        # Store the original function
        self._func = func
        
        # Resolve OpenAPI fields from function
        self._resolve_openapi_fields(func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Direct function call - execute with default context
            context = ActionContext(actor="direct_call", source="decorator")
            # Permissions
            if not self.check_permissions(context):
                raise xActionExecutionError(self.api_name, xActionPermissionError(self.api_name, self.roles, context.metadata.get("roles", [])))
            # Validation
            try:
                from .core.validation import action_validator as _validator
                vres = _validator.validate_inputs(self, kwargs)
                if not vres.valid:
                    raise xActionExecutionError(self.api_name, SchemaValidationError("Action validation failed", errors=vres.errors))
            except Exception as ve:
                if isinstance(ve, xActionExecutionError):
                    raise
            return self._execute_wrapper(func, *args, **kwargs)
        
        def execute_wrapper(context: ActionContext, instance: Any, **kwargs) -> ActionResult:
            """Execute the action with context."""
            return self.execute(context, instance, **kwargs)
        
        # Add action attributes to the wrapper
        wrapper.xaction = self
        wrapper.execute = execute_wrapper
        wrapper._is_action = True
        wrapper.roles = self._roles
        wrapper.api_name = self.api_name
        wrapper.engines = self.engines
        wrapper.to_native = self.to_native
        wrapper.in_types = self._in_types
        
        return wrapper
    
    def _resolve_openapi_fields(self, func: Callable):
        """Resolve OpenAPI fields from function."""
        if not self._operationId:
            self._operationId = func.__name__
        
        if not self._api_name:
            self._api_name = func.__name__
        
        if not self._summary:
            # Use docstring for summary, fallback to function name
            doc = func.__doc__ or ""
            # Get first line of docstring
            first_line = doc.strip().split('\n')[0] if doc.strip() else f"Execute {func.__name__}"
            self._summary = first_line
        
        if not self._description:
            self._description = func.__doc__ or f"Action: {func.__name__}"
    
    def _execute_wrapper(self, func: Callable, *args, **kwargs):
        """Execute the wrapped function."""
        # Create context for metadata
        context = ActionContext(
            actor="user",
            source="direct",
            metadata={
                "action_name": self.api_name,
                "profile": self.profile.value,
                "engines": self.engines,
                "handlers": self.handlers
            }
        )
        
        # Execute the function directly
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            raise xActionError(f"Action execution failed: {str(e)}")
    
    def execute(self, context: ActionContext, instance: Any, **kwargs) -> ActionResult:
        """Execute the action."""
        return action_executor.execute(self, context, instance, **kwargs)
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        result = action_validator.validate_inputs(self, kwargs)
        return result.valid
    
    def check_permissions(self, context: ActionContext) -> bool:
        """Check permissions for the action."""
        # Basic permission check - can be enhanced with xAuth integration
        if not self._roles or "*" in self._roles:
            return True
        
        user_roles = context.metadata.get("roles", [])
        if not user_roles:
            return False
        
        return any(role in user_roles for role in self._roles)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get action metrics."""
        return {
            "action_name": self.api_name,
            "profile": self.profile.value,
            "engines": self.engines,
            "handlers": self.handlers,
            "executor_metrics": action_executor.get_metrics()
        }
    
    def to_openapi(self) -> Dict[str, Any]:
        """Generate OpenAPI specification."""
        return openapi_generator.generate_spec(self)
    
    @classmethod
    def from_native(cls, data: Dict[str, Any]) -> iAction:
        """Create xAction from native data."""
        # Try to resolve function if provided
        func = None
        module_name = data.get("function_module")
        qualname = data.get("function_qualname")
        func_name = data.get("function_name")
        if module_name and (qualname or func_name):
            try:
                import importlib
                mod = importlib.import_module(module_name)
                if qualname:
                    parts = qualname.split(".")
                    obj = mod
                    for p in parts[1:] if parts and parts[0] == module_name else parts:
                        obj = getattr(obj, p)
                    func = obj
                elif func_name:
                    func = getattr(mod, func_name)
            except Exception as e:
                raise ValueError(f"Cannot resolve function {qualname or func_name} in module {module_name}: {e}")
        return cls(
            operationId=data.get("operationId"),
            api_name=data.get("api_name"),
            summary=data.get("summary"),
            description=data.get("description"),
            tags=data.get("tags", []),
            profile=data.get("profile"),
            security=data.get("security"),
            roles=data.get("roles", []),
            rate_limit=data.get("rate_limit"),
            audit=data.get("audit"),
            mfa_required=data.get("mfa_required", False),
            engine=data.get("engine"),
            handlers=data.get("handlers", []),
            readonly=data.get("readonly"),
            idempotent=data.get("idempotent"),
            cache_ttl=data.get("cache_ttl"),
            background=data.get("background"),
            timeout=data.get("timeout"),
            retry=data.get("retry"),
            circuit_breaker=data.get("circuit_breaker"),
            steps=data.get("steps"),
            monitor=data.get("monitor"),
            rollback=data.get("rollback"),
            contracts=data.get("contracts"),
            in_types=data.get("in_types"),
            out_types=data.get("out_types"),
            dependencies=data.get("dependencies"),
            responses=data.get("responses"),
            examples=data.get("examples"),
            deprecated=data.get("deprecated", False),
            func=func
        )
    
    @classmethod
    def from_file(cls, path: str, format: str = "json") -> iAction:
        """Create xAction from file."""
        # Implementation would depend on file format
        logger.warning("from_file not implemented yet")
        return cls()
    
    def to_native(self) -> Dict[str, Any]:
        """Export to native format."""
        # Convert xSchema objects to their native format for serialization
        def convert_xschema(obj):
            if hasattr(obj, 'to_native'):
                return obj.to_native()
            if hasattr(obj, 'to_dict'):
                return obj.to_dict()
            elif isinstance(obj, dict):
                return {k: convert_xschema(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_xschema(item) for item in obj]
            else:
                return obj
        
        # Extract parameters from in_types
        parameters = {}
        if self._in_types:
            type_map = {
                "string": "str",
                "integer": "int",
                "number": "int",
                "boolean": "bool",
                "object": "dict",
                "array": "list"
            }
            # get function annotations to override if needed
            func_hints = {}
            try:
                import inspect
                from typing import get_type_hints
                if self._func:
                    func_hints = get_type_hints(self._func)
            except Exception:
                func_hints = {}
            for param_name, schema in self._in_types.items():
                schema_dict = convert_xschema(schema)
                if not isinstance(schema_dict, dict):
                    schema_dict = {}
                raw_type = schema_dict.get("type")
                if param_name in func_hints:
                    hint = func_hints[param_name]
                    hint_name = getattr(hint, "__name__", str(hint))
                    mapped_type = hint_name
                else:
                    raw = raw_type or "string"
                    mapped_type = type_map.get(raw, str(raw))
                required_list = schema_dict.get("required", []) or []
                parameters[param_name] = {
                    "type": mapped_type,
                    "required": param_name in required_list,
                    "description": schema_dict.get("description", "")
                }
        
        # compute returns from function hints
        returns_type = "Any"
        try:
            import inspect
            from typing import get_type_hints
            if self._func:
                hints = get_type_hints(self._func)
                ret = hints.get('return')
                if ret is not None:
                    returns_type = getattr(ret, "__name__", str(ret))
        except Exception:
            pass

        result = {
            "operationId": self._operationId,
            "api_name": self._api_name,
            "summary": self._summary,
            "description": self._description or "",
            "tags": self._tags,
            "profile": self._profile.value,
            "security": self._security,
            "roles": self._roles,
            "rate_limit": self._rate_limit,
            "audit": self._audit,
            "mfa_required": self._mfa_required,
            "engine": self._engine,
            "handlers": self._handlers,
            "readonly": self._readonly,
            "idempotent": self._idempotent,
            "cache_ttl": self._cache_ttl,
            "background": self._background,
            "timeout": self._timeout,
            "retry": self._retry,
            "circuit_breaker": self._circuit_breaker,
            "steps": self._steps,
            "monitor": self._monitor,
            "rollback": self._rollback,
            "contracts": self._contracts,
            "in_types": convert_xschema(self._in_types),
            "out_types": convert_xschema(self._out_types),
            "dependencies": self._dependencies,
            "responses": self._responses,
            "examples": self._examples,
            "deprecated": self._deprecated,
            "engines": self.engines,
            "parameters": parameters,
            "returns": returns_type
        }
        # Remove None values for TOML safety
        return {k: v for k, v in result.items() if v is not None}


# Utility functions
def register_action_profile(name: str, config: ProfileConfig):
    """Register a new action profile."""
    from .core.config import register_profile
    register_profile(name, config)


def get_action_profiles() -> Dict[str, ProfileConfig]:
    """Get all action profiles."""
    from .core.config import get_all_profiles
    return get_all_profiles()


def create_smart_action(func: Callable, **overrides) -> xAction:
    """Create a smart action with overrides."""
    return xAction(smart_mode="smart", func=func, **overrides)
