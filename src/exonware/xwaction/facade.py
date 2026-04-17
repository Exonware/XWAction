#exonware/xwaction/facade.py
"""
XWAction Facade - Modular Implementation
Production-grade action decorator with comprehensive features.
This module fully reuses ecosystem libraries:
- xwschema: For validation (XWSchema, XWSchemaValidationError)
- xwsystem: For logging (get_logger)
- xwdata: Used in engines and handlers for serialization
"""

from __future__ import annotations
from collections.abc import Callable
_UT_MISSING = object()
try:
    from types import UnionType as _UnionType
except ImportError:  # Python < 3.10
    _UnionType = _UT_MISSING  # type: ignore[misc, assignment]

from typing import Any, Union, get_args, get_origin, get_type_hints
import inspect
import time
from datetime import datetime
from functools import wraps
from .base import AAction
from exonware.xwsystem.shared import XWObject
from .contracts import IAction, IActionAuthorizer, AuthzDecision
from .defs import ActionProfile, ParamInfo, ActionParameter  # Enums and types from defs.py
from .config import ProfileConfig, PROFILE_CONFIGS  # Config from config.py
from .context import ActionContext, ActionResult  # Context from context.py
from .core import (
    action_executor, action_validator, openapi_generator
)
from .core.validation import coerce_explicit_none_to_defaults
from .registry import ActionRegistry
from .errors import (
    XWActionError, XWActionValidationError, XWActionExecutionError, 
    XWActionPermissionError
)
# Fully reuse xwschema for validation
from exonware.xwschema import XWSchema, XWSchemaValidationError
# Fully reuse xwsystem for logging
from exonware.xwsystem import get_logger
logger = get_logger(__name__)


class XWAction(AAction, XWObject):
    """
    XWAction Decorator
    Production-grade action decorator with comprehensive features.
    Fully reuses ecosystem libraries:
    - xwschema: For validation (XWSchema.validate_sync())
    - xwdata: For serialization in engines/handlers (XWData.from_native(), to_native())
      - XWData internally uses xwsystem serialization registry
    - xwsystem: For logging (get_logger)
    - Extends XWObject for identity management, timestamps, and metadata
    Features:
    - Smart inference with profiles and convention-based defaults
    - OpenAPI 3.1 compliance for full API documentation
    - Security integration (OAuth2, API keys, MFA, rate limiting)
    - Workflow orchestration with monitoring and rollback
    - Contract validation with XWSchema integration (fully reuses xwschema)
    - Pluggable engine system (Native, FastAPI, Celery, Prefect)
    - Cross-cutting concerns handlers (Validation, Security, Monitoring, Workflow)
    """

    def __init__(self,
                 # Core identity (OpenAPI-compliant)
                 operationId: str | None = None,
                 api_name: str | None = None,
                 cmd_shortcut: str | None = None,
                 summary: str | None = None,
                 description: str | None = None,
                 tags: list[str] | None = None,
                 # Smart inference and profiles
                 profile: str | ActionProfile | None = None,
                 smart_mode: str | bool = False,
                 # Security
                 security: str | list[str] | dict[str, list[str]] | None = None,
                 roles: list[str] | None = None,
                 rate_limit: str | None = None,
                 audit: bool | None = None,
                 mfa_required: bool = False,
                # Execution control
                engine: str | list[str] | None = None,
                handlers: list[str] | None = None,
                readonly: bool | None = None,
                idempotent: bool | None = None,
                cache_ttl: int | None = None,
                background: bool | None = None,
                timeout: float | None = None,
                method: str | None = None,  # HTTP method for web APIs (GET, POST, PUT, PATCH, DELETE)
                 # Retry and resilience
                 retry: int | dict[str, Any] | None = None,
                 circuit_breaker: bool | None = None,
                 # Workflow and monitoring
                 steps: list[dict[str, Any]] | None = None,
                 monitor: dict[str, Any] | None = None,
                 rollback: bool | None = None,
                 # Streaming (for engines that support streaming responses)
                 stream: bool = False,
                 stream_type: str | None = None,
                 stream_chunk_bytes: int | None = None,
                 stream_flush_interval: float | None = None,
                 # Contract validation
                 contracts: dict[str, Any] | None = None,
                 in_types: dict[str, XWSchema] | None = None,
                 out_types: dict[str, XWSchema] | None = None,
                 parameters: list[ActionParameter] | None = None,
                 context_params: tuple[str, ...] | frozenset[str] | None = None,
                 # Dependencies (FastAPI-style)
                 dependencies: list[Callable] | None = None,
                 # OpenAPI documentation
                 responses: dict[int, dict[str, str]] | None = None,
                 examples: dict[str, Any] | None = None,
                 deprecated: bool = False,
                 # Internal
                 func: Callable | None = None):
        """
        Initialize XWAction decorator.
        Args:
            operationId: OpenAPI operation ID
            api_name: API name
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
            method: HTTP method for web APIs (GET, POST, PUT, PATCH, DELETE)
            retry: Retry configuration
            circuit_breaker: Circuit breaker configuration
            steps: Workflow steps
            monitor: Monitoring configuration
            rollback: Enable rollback
            contracts: Contract validation
            in_types: Input type validation (or derived from parameters when parameters is given and in_types is empty)
            out_types: Output type validation
            parameters: Optional list of ActionParameter (name, param_type, required). When provided and in_types is empty, in_types is built from it. Reused by xwbots and OpenAPI. Prefer markers from :mod:`exonware.xwschema.types_basic` (e.g. ``import exonware.xwschema.types_basic as param``) or :mod:`exonware.xwschema.types_base`; plain ``str`` infers a built-in kind from the parameter name when there are no explicit constraints.
            context_params: Param names to skip validation (framework-injected, e.g. session, message, context). Overrides default.
            dependencies: FastAPI-style dependencies
            responses: OpenAPI responses
            examples: OpenAPI examples
            deprecated: Deprecated flag
            func: Function to decorate
        """
        # Store configuration
        self._operationId = operationId
        self._api_name = api_name
        self._cmd_shortcut = cmd_shortcut
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
        self._method = method
        self._retry = retry
        self._circuit_breaker = circuit_breaker
        self._steps = steps
        self._monitor = monitor
        self._rollback = rollback
        # Streaming configuration
        self._stream = stream
        self._stream_type = stream_type or ("ndjson" if stream else None)
        self._stream_chunk_bytes = stream_chunk_bytes
        self._stream_flush_interval = stream_flush_interval
        self._contracts = contracts
        self._in_types = in_types or {}
        self._out_types = out_types or {}
        self._context_params: frozenset[str] | None = (
            frozenset(context_params) if context_params is not None else None
        )
        self._action_parameters: list[ActionParameter] = []
        if parameters:
            self._action_parameters = list(parameters)
            if not self._in_types:
                # Build in_types from ActionParameter list (full XWSchema/JSON Schema support)
                for ap in self._action_parameters:
                    if ap.schema is not None:
                        self._in_types[ap.name] = XWSchema(ap.schema)
                    else:
                        schema_dict = ap.to_schema_dict()
                        if getattr(ap.param_type, "__kind_id__", None) is None:
                            for key in ("description", "default", "enum", "pattern", "minLength", "maxLength", "minimum", "maximum", "example", "format"):
                                val = getattr(ap, key, None)
                                if val is not None:
                                    schema_dict[key] = val
                        self._in_types[ap.name] = XWSchema(schema_dict)
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
        # Initialize XWObject first (generates uid)
        XWObject.__init__(self, object_id=self._api_name or (self._func.__name__ if self._func else "unknown"))
        # Set timestamps
        now = datetime.now()
        self._created_at = now
        self._updated_at = now
        # Initialize base class (AAction)
        # Note: Base class just stores func, it doesn't inspect it during __init__
        # We'll update self.func when the real function is available in _decorate()
        api_name_for_base = self._api_name or (self._func.__name__ if self._func else "unknown")
        # Use provided func or a minimal placeholder (base class only stores it, doesn't use it)
        base_func = func if func is not None else (lambda: None)
        AAction.__init__(
            self,
            api_name=api_name_for_base,
            func=base_func,
            roles=self._roles,
            in_types=self._in_types,
            out_types=self._out_types
        )
        # Update base class func attribute if we have the real function now
        # (This ensures consistency if func was provided during initialization)
        if func is not None:
            self.func = func
        # Store id for XWObject compatibility
        self._id = api_name_for_base
        # IMPORTANT: base init uses the same internal attribute names (`_api_name`, `_roles`, ...)
        # Restore this facade's configuration so properties like `api_name` resolve correctly.
        self._api_name = api_name
        self._operationId = operationId
        self._cmd_shortcut = cmd_shortcut
        self._tags = tags or []
        self._summary = summary
        self._description = description
        self._roles = roles or []
        if not self._action_parameters:
            self._in_types = in_types or {}
        self._out_types = out_types or {}
        self._readonly = readonly
        self._cache_ttl = cache_ttl
        self._authorizer: IActionAuthorizer | None = None  # Authorization provider
        # Register with registry
        ActionRegistry.register("default", self)
    @property

    def operationId(self) -> str | None:
        """Get OpenAPI operation ID."""
        return self._operationId
    @property

    def api_name(self) -> str:
        """Get API name."""
        return self._api_name or (self._func.__name__ if self._func else "unknown")
    @property

    def cmd_shortcut(self) -> str | None:
        """Get bot command shortcut name."""
        return self._cmd_shortcut
    @property

    def summary(self) -> str | None:
        """Get action summary."""
        return self._summary
    @property

    def description(self) -> str | None:
        """Get action description."""
        return self._description
    @property

    def tags(self) -> list[str]:
        """Get OpenAPI tags."""
        return self._tags
    @property

    def security_config(self) -> Any:
        """Get security configuration."""
        return self._security
    @property

    def roles(self) -> list[str]:
        """Get required roles."""
        return self._roles
    @property

    def rate_limit(self) -> str | None:
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

    def workflow_steps(self) -> list[Any] | None:
        """Get workflow steps."""
        return self._steps
    @property

    def monitoring_config(self) -> Any | None:
        """Get monitoring configuration."""
        return self._monitor
    @property

    def contract_config(self) -> Any | None:
        """Get contract configuration."""
        return self._contracts
    @property

    def responses(self) -> dict[int, dict[str, str]]:
        """Get OpenAPI responses."""
        return self._responses or {}
    @property

    def examples(self) -> dict[str, Any]:
        """Get OpenAPI examples."""
        return self._examples or {}
    @property

    def profile(self) -> ActionProfile:
        """Get action profile."""
        return self._profile
    @property

    def engines(self) -> list[str]:
        """Get configured engines."""
        if hasattr(self, '_combined_config') and self._combined_config.get("engine"):
            engine_config = self._combined_config["engine"]
            if isinstance(engine_config, str):
                return [engine_config]
            elif isinstance(engine_config, list):
                return engine_config
        return self._engine or ["native"]
    @property

    def handlers(self) -> list[str]:
        """Get configured handlers."""
        return self._handlers
    @property

    def stream(self) -> bool:
        """Check if action is configured for streaming responses."""
        return bool(getattr(self, "_stream", False))
    @property

    def stream_type(self) -> str | None:
        """Get configured stream type (e.g., ndjson, sse, raw)."""
        return getattr(self, "_stream_type", None)
    @property

    def stream_chunk_bytes(self) -> int | None:
        """Get configured preferred chunk size in bytes for streaming engines."""
        return getattr(self, "_stream_chunk_bytes", None)
    @property

    def stream_flush_interval(self) -> float | None:
        """Get configured preferred flush interval in seconds for streaming engines."""
        return getattr(self, "_stream_flush_interval", None)
    @property

    def in_types(self) -> dict[str, XWSchema] | None:
        """Get input type validation."""
        return self._in_types
    @property

    def out_types(self) -> dict[str, XWSchema] | None:
        """Get output type validation."""
        return self._out_types
    @property
    def context_params(self) -> frozenset[str] | None:
        """Get context param names to skip validation (framework-injected). None = use default."""
        return getattr(self, '_context_params', None)
    @property

    def action_parameters(self) -> list[ActionParameter]:
        """Get declarative action parameters (when set via parameters=). Used by OpenAPI and xwbots."""
        return getattr(self, '_action_parameters', [])
    @property

    def func(self) -> Callable | None:
        """Get decorated function."""
        return self._func
    @func.setter

    def func(self, value: Callable | None) -> None:
        """Set decorated function (required for base class initialization)."""
        self._func = value
    @property

    def deprecated(self) -> bool:
        """Check if action is deprecated."""
        return self._deprecated
    @property

    def is_async(self) -> bool:
        """Check if function is async (coroutine)."""
        return getattr(self, '_is_async', False)
    @property

    def is_generator(self) -> bool:
        """Check if function is a generator."""
        return getattr(self, '_is_generator', False)
    @property

    def is_async_generator(self) -> bool:
        """Check if function is an async generator."""
        return getattr(self, '_is_async_generator', False)
    @property

    def function_module(self) -> str | None:
        """Get the module where the function is defined."""
        return getattr(self, '_function_module', None)
    @property

    def function_qualname(self) -> str | None:
        """Get the qualified name of the function."""
        return getattr(self, '_function_qualname', None)
    @property

    def source_file(self) -> str | None:
        """Get the source file path where the function is defined."""
        return getattr(self, '_source_file', None)
    @property

    def source_line(self) -> int | None:
        """Get the line number where the function is defined."""
        return getattr(self, '_source_line', None)
    @property

    def signature(self) -> inspect.Signature | None:
        """Get the cached function signature object."""
        return getattr(self, '_signature', None)
    @property

    def signature_string(self) -> str | None:
        """Get the string representation of the function signature."""
        return getattr(self, '_signature_string', None)
    @property

    def parameters(self) -> dict[str, ParamInfo]:
        """Get parameter metadata extracted from function signature."""
        return getattr(self, '_parameters', {})
    @property

    def return_type(self) -> type | None:
        """Get the return type annotation."""
        return getattr(self, '_return_type', None)

    def _resolve_profile(self, profile: str | ActionProfile | None, 
                        smart_mode: str | bool) -> ActionProfile:
        """Resolve action profile."""
        if profile:
            if isinstance(profile, str):
                try:
                    return ActionProfile(profile)
                except ValueError:
                    return ActionProfile.ACTION
            elif isinstance(profile, ActionProfile):
                return profile
        # Default to ACTION profile
        return ActionProfile.ACTION

    def _merge_configuration(self, profile_config: ProfileConfig) -> dict[str, Any]:
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

    def _store_combined_config(self, config: dict[str, Any], profile: ActionProfile):
        """Store combined configuration."""
        self._combined_config = config
        self._profile = profile

    def __call__(self, func_or_smart: Callable | str | None = None):
        """Handle decorator usage."""
        # Handle smart mode shortcut: @XWAction("smart")
        if isinstance(func_or_smart, str) and func_or_smart == "smart":
            def smart_decorator(func: Callable):
                return self._create_smart_action(func)
            return smart_decorator
        # Handle direct function decoration: @XWAction
        if func_or_smart is not None and callable(func_or_smart):
            return self._decorate(func_or_smart)
        # Handle parameterized decoration: @XWAction(...)
        def decorator(func: Callable):
            return self._decorate(func)
        return decorator

    def _create_smart_action(self, func: Callable):
        """Create a smart action with inference."""
        smart_action = XWAction(smart_mode="smart", func=func)
        return smart_action._decorate(func)
    @classmethod

    def create(cls, func: Callable, api_name: str | None = None,
               roles: list[str] | None = None,
               in_types: dict[str, XWSchema] | None = None,
               out_types: dict[str, XWSchema] | None = None,
               **kwargs) -> IAction:
        """Create an XWAction instance from a function."""
        return cls(
            api_name=api_name,
            roles=roles,
            in_types=in_types,
            out_types=out_types,
            func=func,
            **kwargs
        )

    def _decorate(self, func: Callable):
        """Decorate a function with XWAction functionality."""
        # Store the original function
        self._func = func
        # Update base class func attribute to ensure consistency
        self.func = func
        # Inspect function signature and collect metadata
        self._inspect_function_signature(func)
        # Resolve OpenAPI fields from function
        self._resolve_openapi_fields(func)
        # Auto-populate in_types/out_types if not provided
        # This ensures schemas are synced with function signature
        if not self._in_types:
            self._in_types = self._auto_populate_in_types()
            logger.debug(f"[{self.api_name}] Auto-populated in_types from function signature")
        if not self._out_types:
            self._out_types = self._auto_populate_out_types()
            if self._out_types:
                logger.debug(f"[{self.api_name}] Auto-populated out_types from return type annotation")
        # Validate signature mismatches and log warnings
        # This ensures existing schemas match the function signature
        mismatches = self._validate_signature_mismatches()
        if mismatches:
            for warning in mismatches:
                logger.warning(f"[{self.api_name}] {warning}")
        @wraps(func)
        def wrapper(*args, **kwargs):
            # #region agent log
            from exonware.xwsystem.io.serialization import JsonSerializer
            import time
            try:
                with open(r'd:\OneDrive\DEV\exonware\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(JsonSerializer().encode({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"facade.py:541","message":"Wrapper called","data":{"args_count":len(args),"kwargs_keys":list(kwargs.keys()),"first_arg_type":str(type(args[0])) if args else None,"first_arg_has_actions":hasattr(args[0],'_actions') if args else None},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            # Use context from kwargs if provided (e.g. from bot command handler with user_roles)
            if 'context' in kwargs and isinstance(kwargs.get('context'), dict):
                ctx_dict = kwargs['context']
                roles = ctx_dict.get('user_roles') or ctx_dict.get('roles') or []
                actor = ctx_dict.get('username') or ctx_dict.get('user_id') or ctx_dict.get('telegram_username') or 'direct_call'
                context = ActionContext(actor=actor, source="command", metadata={"roles": roles})
            else:
                context = ActionContext(actor="direct_call", source="decorator")
            # kwargs_for_bind: exclude 'context' if func doesn't accept it (bind would raise TypeError)
            sig = inspect.signature(func)
            kwargs_for_bind = dict(kwargs)
            if 'context' in kwargs_for_bind and 'context' not in sig.parameters:
                kwargs_for_bind.pop('context', None)
            # Convert positional args to kwargs for validation
            # Use inspect.signature().bind() for reliable argument mapping
            # This properly handles 'self' and other bound parameters without fragile heuristics
            validation_kwargs = dict(kwargs_for_bind)  # Start with explicit kwargs
            if args and self._in_types:
                try:
                    # Use bind() to properly map positional args to parameter names
                    # This automatically handles 'self' and other bound parameters correctly
                    bound = sig.bind(*args, **kwargs_for_bind)
                    bound.apply_defaults()
                    # Convert BoundArguments to dict, excluding 'self' if present
                    bound_kwargs = bound.arguments
                    bound_kwargs.pop('self', None)  # Remove 'self' if it was bound
                    # Merge with explicit kwargs (explicit kwargs take precedence)
                    for param_name, param_value in bound_kwargs.items():
                        if param_name not in validation_kwargs:  # Don't override explicit kwargs
                            validation_kwargs[param_name] = param_value
                except TypeError as e:
                    # bind() can fail if args don't match signature (e.g., wrong number of args)
                    # Fall back to manual mapping for edge cases
                    logger.debug(f"Could not bind arguments for validation: {e}, falling back to manual mapping")
                    try:
                        param_names = list(sig.parameters.keys())
                        # Skip 'self' from param names if present
                        if param_names and param_names[0] == 'self':
                            param_names = param_names[1:]
                            args_to_map = args[1:] if args else []
                        else:
                            args_to_map = list(args)
                        # Map positional args to parameter names
                        for i, arg_value in enumerate(args_to_map):
                            if i < len(param_names):
                                param_name = param_names[i]
                                if param_name not in validation_kwargs:
                                    validation_kwargs[param_name] = arg_value
                    except Exception as e2:
                        logger.debug(f"Could not convert args to kwargs for validation: {e2}")
                        # If all conversion fails, use original kwargs for validation
                        validation_kwargs = kwargs_for_bind
                except Exception as e:
                    logger.debug(f"Could not convert args to kwargs for validation: {e}")
                    # If conversion fails, use original kwargs for validation
                    validation_kwargs = kwargs
            coerce_explicit_none_to_defaults(self, validation_kwargs)
            # Permissions
            # #region agent log
            try:
                with open(r'd:\OneDrive\DEV\exonware\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(JsonSerializer().encode({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"facade.py:590","message":"Permission check","data":{"action_name":self.api_name,"required_roles":self._roles,"context_roles":context.metadata.get("roles",[]),"has_permission":self.check_permissions(context)},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            if not self.check_permissions(context):
                raise XWActionExecutionError(
                    self.api_name, 
                    XWActionPermissionError(
                        self.api_name, 
                        required=self.roles, 
                        actual=context.metadata.get("roles", [])
                    )
                )
            # Validation - use validation_kwargs (includes converted positional args)
            try:
                validation_result = action_validator.validate_inputs(self, validation_kwargs)
                if not validation_result.valid:
                    raise XWActionExecutionError(
                        self.api_name, 
                        XWSchemaValidationError(
                            "Action validation failed",
                            context={"issues": [{"message": err} for err in validation_result.errors]},
                        )
                    )
            except Exception as ve:
                if isinstance(ve, XWActionExecutionError):
                    raise
            # #region agent log
            try:
                with open(r'd:\OneDrive\DEV\exonware\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(JsonSerializer().encode({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"facade.py:603","message":"About to call _execute_wrapper","data":{"args_count":len(args),"kwargs_keys":list(kwargs.keys()),"first_arg_type":str(type(args[0])) if args else None},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            # Remove context from kwargs if func doesn't accept it (avoid TypeError)
            kwargs_for_call = dict(kwargs)
            if 'context' in kwargs_for_call:
                sig = inspect.signature(func)
                if 'context' not in sig.parameters:
                    kwargs_for_call.pop('context', None)
            coerce_explicit_none_to_defaults(self, kwargs_for_call)
            return self._execute_wrapper(func, *args, **kwargs_for_call)
        def execute_wrapper(context: ActionContext, instance: Any, **kwargs) -> ActionResult:
            """Execute the action with context."""
            return self.execute(context, instance, **kwargs)
        # Add action attributes to the wrapper
        wrapper.xwaction = self
        wrapper.execute = execute_wrapper
        wrapper._is_action = True
        wrapper.roles = self._roles
        wrapper.api_name = self.api_name
        wrapper.engines = self.engines
        wrapper.to_native = self.to_native
        wrapper.in_types = self._in_types
        wrapper._action_parameters = getattr(self, '_action_parameters', [])
        wrapper.context_params = self._context_params
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

    def _inspect_function_signature(self, func: Callable) -> None:
        """
        Inspect and cache comprehensive function signature information.
        This method collects all available function metadata including:
        - Full signature object
        - Resolved type hints
        - Parameter metadata (name, type, default, required, kind)
        - Return type annotation
        - Async detection
        - Function location (module, qualname, source file, line number)
        Args:
            func: Function to inspect
        """
        try:
            # Cache signature object
            self._signature = inspect.signature(func)
            # Cache type hints (resolved)
            try:
                self._type_hints = get_type_hints(func, include_extras=True)
            except Exception as e:
                logger.debug(f"Could not resolve type hints for {func.__name__}: {e}")
                self._type_hints = {}
            # Extract and cache parameter metadata
            self._parameters = self._extract_parameters(func)
            # Extract and cache return type
            self._return_type = self._extract_return_type()
            # Detect async function
            self._is_async = inspect.iscoroutinefunction(func)
            self._is_generator = inspect.isgeneratorfunction(func)
            self._is_async_generator = inspect.isasyncgenfunction(func)
            # Cache function location information
            self._function_module = func.__module__
            self._function_qualname = getattr(func, '__qualname__', func.__name__)
            try:
                self._source_file = inspect.getfile(func)
                source_lines, self._source_line = inspect.getsourcelines(func)
            except (OSError, TypeError):
                self._source_file = None
                self._source_line = None
            # Cache signature string representation
            self._signature_string = str(self._signature)
        except Exception as e:
            logger.warning(f"Failed to inspect signature for {func.__name__}: {e}")
            # Set defaults on failure
            self._signature = None
            self._type_hints = {}
            self._parameters = {}
            self._return_type = None
            self._is_async = False
            self._is_generator = False
            self._is_async_generator = False
            self._function_module = getattr(func, '__module__', None)
            self._function_qualname = getattr(func, '__qualname__', func.__name__)
            self._source_file = None
            self._source_line = None
            self._signature_string = None

    def _extract_parameters(self, func: Callable) -> dict[str, ParamInfo]:
        """
        Extract parameter metadata from function signature.
        Args:
            func: Function to extract parameters from
        Returns:
            Dictionary mapping parameter names to ParamInfo objects
        """
        parameters: dict[str, ParamInfo] = {}
        if not hasattr(self, '_signature') or self._signature is None:
            return parameters
        for param_name, param in self._signature.parameters.items():
            # Skip 'self' parameter for methods
            if param_name == 'self':
                continue
            # Get type annotation (resolved)
            param_type = self._type_hints.get(param_name, Any)
            # Get default value
            has_default = param.default is not inspect.Parameter.empty
            default_value = param.default if has_default else None
            # Create ParamInfo
            param_info = ParamInfo(
                name=param_name,
                type=param_type,
                default=default_value,
                has_default=has_default,
                required=True,  # Will be computed in __post_init__
                kind=param.kind
            )
            # Recompute required status (ParamInfo.__post_init__ handles this)
            param_info.__post_init__()
            parameters[param_name] = param_info
        return parameters

    def _extract_return_type(self) -> type | None:
        """Extract return type annotation from function."""
        if not hasattr(self, '_type_hints') or not self._type_hints:
            return None
        return self._type_hints.get('return', None)

    def _validate_signature_mismatches(self) -> list[str]:
        """
        Validate function signature against declared in_types/out_types.
        Detects and warns about:
        - Parameters in signature but not in in_types
        - Parameters in in_types but not in signature
        - Type mismatches between function annotation and in_types
        - Required/optional mismatches
        Returns:
            List of warning messages
        """
        warnings: list[str] = []
        if not hasattr(self, '_parameters') or not self._parameters:
            return warnings
        # Get declared parameter names from in_types
        declared_params = set(self._in_types.keys()) if self._in_types else set()
        signature_params = set(self._parameters.keys())
        # Check for parameters in signature but not declared in in_types
        # Root cause fixed: Exclude **kwargs (VAR_KEYWORD) and *args (VAR_POSITIONAL) parameters from validation
        # These are variable arguments that accept any additional parameters
        # and should not be in in_types validation
        for param_name in signature_params - declared_params:
            param_info = self._parameters[param_name]
            # Skip **kwargs parameters - they're meant to accept variable keyword arguments
            if hasattr(param_info, 'kind') and param_info.kind == inspect.Parameter.VAR_KEYWORD:
                continue
            # Skip *args parameters - they're meant to accept variable positional arguments
            if hasattr(param_info, 'kind') and param_info.kind == inspect.Parameter.VAR_POSITIONAL:
                continue
            warnings.append(
                f"Parameter '{param_name}' exists in function signature but is not declared in in_types. "
                f"Type: {param_info.type}, Required: {param_info.required}"
            )
        # Check for parameters in in_types but not in signature
        for param_name in declared_params - signature_params:
            warnings.append(
                f"Parameter '{param_name}' declared in in_types but not found in function signature"
            )
        # Validate type and required/optional consistency for common parameters
        for param_name in signature_params & declared_params:
            param_info = self._parameters[param_name]
            declared_schema = self._in_types[param_name]
            # Type validation: Ensure schema type matches function signature type
            # This ensures XWSchema accurately represents the function signature
            schema_dict = declared_schema.to_native() if hasattr(declared_schema, 'to_native') else {}
            if isinstance(schema_dict, dict):
                schema_type = schema_dict.get("type")
                # Generate expected schema from function type to compare
                expected_schema_dict = self._type_to_schema_dict(param_info.type, param_info.required)
                expected_schema_type = expected_schema_dict.get("type")
                # Check for type mismatch
                if schema_type and expected_schema_type and schema_type != expected_schema_type:
                    # Allow some flexibility:
                    # - integer/number are compatible
                    # - any/object are compatible (both represent untyped values)
                    # - object/any are compatible (complex types map to object, schema may use any)
                    # - session/object: schema may declare "session" (param name) while signature has requests.Session -> object
                    compatible_pairs = [
                        ('integer', 'number'), ('number', 'integer'),
                        ('any', 'object'), ('object', 'any'),
                        ('session', 'object'), ('object', 'session'),
                    ]
                    is_compatible = any(
                        (schema_type == pair[0] and expected_schema_type == pair[1]) or
                        (schema_type == pair[1] and expected_schema_type == pair[0])
                        for pair in compatible_pairs
                    )
                    if not is_compatible:
                        warnings.append(
                            f"Parameter '{param_name}' type mismatch: function signature expects {expected_schema_type}, "
                            f"but schema declares {schema_type}. Schema may not accurately represent function signature."
                        )
        # Return type validation
        if self._return_type and self._out_types:
            # Basic check: if out_types is declared, function should have return type
            # More sophisticated validation could be added here
            pass
        return warnings

    def _auto_populate_in_types(self) -> dict[str, XWSchema]:
        """
        Auto-populate in_types from function signature when not provided.
        Reuses XWSchema.extract_parameters for consistency and caching.
        Returns:
            Dictionary of parameter names to XWSchema objects
        """
        if not self._func:
            return {}
        # Reuse XWSchema.extract_parameters (includes caching and deadlock prevention)
        in_schemas, _ = XWSchema.extract_parameters(self._func)
        # Convert list to dict with parameter names extracted directly from function signature
        auto_in_types: dict[str, XWSchema] = {}
        # Extract parameter names directly from function signature (not from _parameters)
        try:
            sig = inspect.signature(self._func)
            param_names = [
                name for name, param in sig.parameters.items()
                if name not in ('self', 'cls')
            ]
            # Map schemas to parameter names
            # XWSchema.extract_parameters should return schemas in the same order as parameters
            # (excluding 'self' and 'cls')
            for i, schema in enumerate(in_schemas):
                if i < len(param_names):
                    auto_in_types[param_names[i]] = schema
        except Exception as e:
            # Fallback: try to use _parameters if available
            if hasattr(self, '_parameters') and self._parameters:
                param_names = [name for name in self._parameters.keys() if name not in ('self', 'cls')]
                for i, schema in enumerate(in_schemas):
                    if i < len(param_names):
                        auto_in_types[param_names[i]] = schema
            else:
                # Last resort: log warning but don't fail
                logger.debug(f"[{self.api_name}] Could not extract parameter names for auto-population: {e}")
        # Enrich plain ``str`` parameters using :data:`exonware.xwschema.types_base.param_name_to_kind`
        # (same idea as :meth:`ActionParameter.to_schema_dict` for ``param_type=str``).
        try:
            from exonware.xwschema.types_base import kind_for_param_name, schema_fragment
        except ImportError:
            return auto_in_types

        def _annotation_is_plain_str(tp: Any) -> bool:
            if tp is str:
                return True
            o = get_origin(tp)
            if o is Union or (_UnionType is not _UT_MISSING and o is _UnionType):
                args = [a for a in (get_args(tp) or ()) if a is not type(None)]
                return len(args) == 1 and args[0] is str
            return False

        def _plain_string_schema_dict(d: dict[str, Any]) -> bool:
            if d.get("type") != "string":
                return False
            return not any(
                d.get(k)
                for k in ("pattern", "format", "enum", "minLength", "maxLength", "oneOf", "allOf", "anyOf")
            )

        enriched: dict[str, XWSchema] = {}
        for pname, sch in auto_in_types.items():
            pinfo = (self._parameters or {}).get(pname)
            native: dict[str, Any] = {}
            if hasattr(sch, "to_native"):
                raw = sch.to_native()
                if isinstance(raw, dict):
                    native = raw
            if pinfo is not None and _annotation_is_plain_str(pinfo.type) and _plain_string_schema_dict(native):
                kid = kind_for_param_name(pname)
                if kid:
                    try:
                        frag = schema_fragment(kid)
                        merged = {**native, **frag}
                        enriched[pname] = XWSchema(merged)
                        continue
                    except KeyError:
                        pass
            enriched[pname] = sch
        return enriched

    def _auto_populate_out_types(self) -> dict[str, XWSchema]:
        """
        Auto-populate out_types from return type annotation when not provided.
        Reuses XWSchema.extract_parameters for consistency and caching.
        Returns:
            Dictionary with schema for return type
        """
        if not self._func:
            return {}
        # Reuse XWSchema.extract_parameters (includes caching and deadlock prevention)
        _, out_schemas = XWSchema.extract_parameters(self._func)
        # Convert list to dict
        if out_schemas and len(out_schemas) > 0:
            return {"return": out_schemas[0]}
        return {}

    def _type_to_schema_dict(self, param_type: Any, required: bool = True, _depth: int = 0) -> dict[str, Any]:
        """
        Convert Python type annotation to XWSchema dictionary.
        Root cause fixed: requests.Session and similar non-serializable types
        were not properly converted to "object" type in schema, causing type
        mismatch warnings.
        Priority alignment:
        - Usability (#2): Accurate schemas improve API documentation and reduce warnings
        - Maintainability (#3): Proper type mapping reduces validation confusion
        Note: The 'required' parameter is for documentation purposes. In JSON Schema,
        required status is handled at the object level (in a "required" array), not
        in individual property schemas. For individual parameter schemas, required
        status is tracked separately via ParamInfo.required.
        Args:
            param_type: Type annotation from function signature
            required: Whether the type is required (used for documentation/logging)
            _depth: Internal recursion depth counter (prevents infinite recursion)
        Returns:
            Schema dictionary compatible with XWSchema that represents the same type
        """
        # Prevent infinite recursion with depth limit
        MAX_RECURSION_DEPTH = 50
        if _depth > MAX_RECURSION_DEPTH:
            logger.warning(f"Recursion depth limit reached in _type_to_schema_dict for type {param_type}, using 'object' fallback")
            return {"type": "object"}
        tid = getattr(param_type, "__kind_id__", None)
        if isinstance(tid, str) and tid.strip():
            from exonware.xwschema.types_base import kind_for

            spec = kind_for(tid.strip())
            if spec is not None:
                # XWSchema (and catalog kinds) expose JSON Schema fragments via ``to_native()``.
                return dict(spec.to_native())
        schema: dict[str, Any] = {}
        # Handle None type
        if param_type is None or param_type is type(None):
            schema["type"] = "null"
            return schema
        # Handle generic types (List, Dict, Union, Optional, etc.)
        origin = getattr(param_type, '__origin__', None)
        args = getattr(param_type, '__args__', None)
        # Check origin name for compatibility with both typing and built-in generics
        origin_name = None
        if hasattr(origin, '__name__'):
            origin_name = origin.__name__
        elif hasattr(origin, '__qualname__'):
            origin_name = origin.__qualname__.split('.')[-1]
        if origin is not None and origin_name:
            # Handle list[T] or list[T]
            if origin_name in ('list', 'List'):
                schema["type"] = "array"
                if args and len(args) > 0:
                    item_type = args[0]
                    # Recursively convert item type to ensure nested types are synced
                    schema["items"] = self._type_to_schema_dict(item_type, required=True, _depth=_depth + 1)
                else:
                    schema["items"] = {}
            # Handle dict[K, V] or dict[K, V]
            elif origin_name in ('dict', 'Dict'):
                schema["type"] = "object"
                # For dict types, we create a generic object schema
                # Could extract key/value types from args if needed for more specific validation
            # Handle Union/Optional
            elif origin_name in ('Union', 'Optional'):
                # For Optional/Union, extract the first non-None type
                # This ensures the schema represents the actual type, not the Optional wrapper
                non_none_args = [arg for arg in args if arg is not type(None)] if args else []
                if non_none_args:
                    # Recursively convert the underlying type
                    schema = self._type_to_schema_dict(non_none_args[0], required=False, _depth=_depth + 1)
                else:
                    schema["type"] = "object"  # Fallback
        # Handle built-in types and special types - map Python types to JSON Schema types
        elif hasattr(param_type, '__name__'):
            type_name = param_type.__name__
            module = getattr(param_type, '__module__', '')
            # ⚠️ ROOT CAUSE FIX: Handle requests.Session and similar non-serializable types
            # These should map to "object" type in JSON Schema, not string type
            # This prevents type mismatch warnings when function signature has requests.Session
            # but schema incorrectly declares "session" as a string type
            if module.startswith('requests') and 'Session' in type_name:
                schema["type"] = "object"
                return schema
            # Check for other common non-serializable HTTP client types
            # These are runtime objects that cannot be serialized to JSON
            non_serializable_patterns = [
                ('requests.', 'Session'),
                ('urllib3.', ''),
                ('http.client.', ''),
            ]
            for pattern_module, pattern_name in non_serializable_patterns:
                if pattern_module in module or (pattern_name and pattern_name in type_name):
                    schema["type"] = "object"
                    return schema
            # Check for UUID type (from uuid.UUID)
            if type_name == 'UUID' or module.startswith('uuid'):
                schema["type"] = "uuid"
                return schema
            # Check for Enum types
            if hasattr(param_type, '__bases__'):
                # Check if it's an Enum or Enum subclass
                bases = param_type.__bases__
                if any(base.__name__ == 'Enum' for base in bases if hasattr(base, '__name__')):
                    # Use lowercase enum name as schema type (matching XWSchema convention)
                    schema["type"] = type_name.lower()
                    return schema
            # Check for Decimal type (from decimal.Decimal)
            if type_name == 'Decimal' or module.startswith('decimal'):
                schema["type"] = "decimal"
                return schema
            # Check for date/datetime types (from datetime module)
            if type_name in ('date', 'datetime', 'time') or module.startswith('datetime'):
                schema["type"] = type_name  # "date", "datetime", "time"
                return schema
            # Standard type mapping
            type_mapping = {
                'str': 'string',
                'int': 'integer',
                'float': 'number',
                'bool': 'boolean',
                'dict': 'object',
                'list': 'array',
                'tuple': 'array',
                'set': 'array',
                'Any': 'object',
            }
            schema["type"] = type_mapping.get(type_name, 'object')
        else:
            # Fallback to object for unknown types
            schema["type"] = "object"
        # Return schema dictionary that represents the same type as the Python type annotation
        # This ensures XWSchema will validate values that match the function signature type
        return schema

    def _execute_wrapper(self, func: Callable, *args, **kwargs):
        """Execute the wrapped function."""
        # #region agent log
        from exonware.xwsystem.io.serialization import JsonSerializer
        import time
        import inspect
        try:
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            with open(r'd:\OneDrive\DEV\exonware\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(JsonSerializer().encode({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"facade.py:1032","message":"_execute_wrapper called","data":{"func_name":func.__name__,"args_count":len(args),"kwargs_keys":list(kwargs.keys()),"param_names":param_names,"first_param":param_names[0] if param_names else None,"first_arg_type":str(type(args[0])) if args else None},"timestamp":int(time.time()*1000)})+'\n')
        except: pass
        # #endregion
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
            # #region agent log
            try:
                with open(r'd:\OneDrive\DEV\exonware\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(JsonSerializer().encode({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"facade.py:1048","message":"About to call original func","data":{"func_name":func.__name__,"args_count":len(args),"first_arg_type":str(type(args[0])) if args else None},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            result = func(*args, **kwargs)
            # #region agent log
            try:
                with open(r'd:\OneDrive\DEV\exonware\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(JsonSerializer().encode({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"facade.py:1050","message":"Original func call succeeded","data":{"func_name":func.__name__},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            return result
        except Exception as e:
            raise XWActionError(f"Action execution failed: {str(e)}")

    def execute(self, context: ActionContext | None = None, instance: Any | None = None, **kwargs) -> ActionResult:
        """
        Execute the action with full validation pipeline.
        When called without context/instance, provides sensible defaults:
        - Creates default ActionContext with actor="direct_call" and source="direct"
        - Uses None for instance (actions that need instance should receive it from XWObject)
        Full pipeline includes:
        - Schema validation of parameters (in_types validation)
        - BEFORE handlers
        - Permission checks
        - Action execution
        - AFTER handlers
        - Error handling
        Args:
            context: Optional execution context (defaults to ActionContext if not provided)
            instance: Optional entity instance (defaults to None if not provided)
            **kwargs: Action parameters to validate and pass to handler
        Returns:
            ActionResult with success/failure and execution data
        Example:
            >>> action.execute(param1="value1", param2="value2")
            >>> # Full pipeline: schema validation -> handlers -> execution -> result
        """
        # Provide defaults if context/instance not provided
        if context is None:
            context = ActionContext(
                actor="direct_call",
                source="direct",
                metadata={
                    "action_name": self.api_name,
                    "profile": self.profile.value if hasattr(self, 'profile') else "action"
                }
            )
        # Instance can be None - actions that need it should receive it from XWObject
        if instance is None:
            instance = None
        # Execute through full pipeline (validation, handlers, execution)
        return action_executor.execute(self, context, instance, **kwargs)

    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        result = action_validator.validate_inputs(self, kwargs)
        return result.valid
    @staticmethod

    def query(query_string: str, data: Any, format: str | None = None, **kwargs) -> Any:
        """
        Execute a query on data using XWQuery.
        This method allows actions to use XWQuery internally for data querying
        and transformation. Supports all XWQuery formats (SQL, JSONPath, Cypher, etc.).
        Args:
            query_string: Query string in any supported format (SQL, JSONPath, Cypher, etc.)
            data: Data to query (can be XWData, dict, list, or any queryable structure)
            format: Optional format hint (auto-detected if not provided)
            **kwargs: Additional query options
        Returns:
            Query execution result (ExecutionResult or data directly)
        Example:
            >>> # Inside an action function
            >>> def my_action(self, **kwargs):
            >>>     # Query object data using SQL
            >>>     users = XWAction.query("SELECT * FROM users WHERE age > 25", self.data)
            >>>     return users
            >>>     
            >>>     # Query using JSONPath
            >>>     names = XWAction.query("$.users[*].name", self.data, format="jsonpath")
        """
        from exonware.xwquery import XWQuery
        # Convert XWData to native format if needed
        if hasattr(data, 'to_native'):
            query_data = data.to_native()
        elif hasattr(data, 'to_dict'):
            query_data = data.to_dict()
        else:
            query_data = data
        # Execute query using XWQuery - fully reuses xwquery capabilities
        result = XWQuery.execute(query_string, query_data, format=format, **kwargs)
        # Return plain query payload so callers can directly assert list/dict results.
        # Entity-specific wrappers can still normalize to {"results": ...} where needed.
        return result.data if hasattr(result, 'data') else (result.result if hasattr(result, 'result') else result)

    def set_authorizer(self, authorizer: IActionAuthorizer) -> None:
        """
        Set the authorization provider for this action.
        Args:
            authorizer: IActionAuthorizer implementation (e.g., from xwauth)
        """
        self._authorizer = authorizer

    def check_permissions(self, context: ActionContext) -> bool:
        """Check permissions for the action."""
        # If authorizer is set, use it
        if self._authorizer:
            try:
                decision = self._authorizer.authorize(action=self, context=context)
                if not decision.allowed:
                    raise XWActionPermissionError(
                        self.api_name,
                        required=self._roles,
                        actual=decision.roles or [],
                        reason=decision.reason
                    )
                return True
            except XWActionPermissionError:
                raise
            except Exception as e:
                # System errors (token invalid, backend down, etc.)
                logger.error(f"Authorization system error for {self.api_name}: {e}")
                raise XWActionExecutionError(
                    self.api_name,
                    XWActionPermissionError(
                        self.api_name,
                        required=self._roles,
                        actual=[],
                        reason=f"Authorization system error: {str(e)}"
                    )
                )
        # Fallback to basic role-based check if no authorizer
        if not self._roles or "*" in self._roles:
            return True
        user_roles = context.metadata.get("roles", [])
        if not user_roles:
            return False
        return any(role in user_roles for role in self._roles)

    def get_metrics(self) -> dict[str, Any]:
        """Get action metrics."""
        return {
            "action_name": self.api_name,
            "profile": self.profile.value,
            "engines": self.engines,
            "handlers": self.handlers,
            "executor_metrics": action_executor.get_metrics()
        }

    def to_openapi(self) -> dict[str, Any]:
        """Generate OpenAPI specification."""
        return openapi_generator.generate_spec(self)
    @classmethod

    def from_native(cls, data: dict[str, Any]) -> IAction:
        """Create XWAction from native data."""
        # Try to resolve function if provided
        func = None
        module_name = data.get("function_module")
        qualname = data.get("function_qualname")
        func_name = data.get("function_name")
        if module_name and (qualname or func_name):
            import importlib
            mod = importlib.import_module(module_name)
            if qualname:
                # Handle qualified name (e.g., "module.Class.method" or "module.function")
                parts = qualname.split(".")
                obj = mod
                start_idx = 1 if parts and parts[0] == module_name else 0
                for part in parts[start_idx:]:
                    if not hasattr(obj, part):
                        raise AttributeError(f"'{type(obj).__name__}' object has no attribute '{part}' in qualname '{qualname}'")
                    obj = getattr(obj, part)
                func = obj
            elif func_name:
                if not hasattr(mod, func_name):
                    raise AttributeError(f"Module '{module_name}' has no attribute '{func_name}'")
                func = getattr(mod, func_name)
        # Convert in_types and out_types from native to XWSchema
        in_types = None
        if "in_types" in data and data["in_types"]:
            in_types = {}
            for key, schema_dict in data["in_types"].items():
                if isinstance(schema_dict, dict):
                    in_types[key] = XWSchema(schema_dict)
                else:
                    in_types[key] = schema_dict
        out_types = None
        if "out_types" in data and data["out_types"]:
            out_types = {}
            for key, schema_dict in data["out_types"].items():
                if isinstance(schema_dict, dict):
                    out_types[key] = XWSchema(schema_dict)
                else:
                    out_types[key] = schema_dict
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
            in_types=in_types,
            out_types=out_types,
            dependencies=data.get("dependencies"),
            responses=data.get("responses"),
            examples=data.get("examples"),
            deprecated=data.get("deprecated", False),
            func=func
        )
    @classmethod

    def from_file(cls, path: str, format: str = "json") -> IAction:
        """Create XWAction from file."""
        # Implementation would depend on file format
        logger.warning("from_file not implemented yet")
        return cls()
    @staticmethod

    def extract_actions(obj: Any) -> list[XWAction]:
        """
        Extract all XWAction instances from an object (class or instance).
        This is a convenience static method that delegates to the utility function.
        See action_utils.extract_actions for full documentation.
        Args:
            obj: Object (class or instance) to scan for actions
        Returns:
            List of XWAction instances found on the object
        """
        from .action_utils import extract_actions as _extract_actions
        return _extract_actions(obj)
    @staticmethod

    def load_actions(obj: Any, actions: list[XWAction]) -> bool:
        """
        Load/attach XWAction instances to an object instance as callable methods.
        This is a convenience static method that delegates to the utility function.
        See action_utils.load_actions for full documentation.
        Args:
            obj: Object instance to attach actions to (must be an instance, not a class)
            actions: List of XWAction instances to attach
        Returns:
            True if all actions were successfully attached, False otherwise
        """
        from .action_utils import load_actions as _load_actions
        return _load_actions(obj, actions)

    def to_native(self) -> dict[str, Any]:
        """Export to native format using cached signature information."""
        # Convert XWSchema objects to their native format for serialization
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
        # Use cached signature and type hints if available (from _inspect_function_signature)
        if hasattr(self, '_signature') and self._signature is not None:
            sig = self._signature
        else:
            sig = inspect.signature(self._func) if self._func else None
        if hasattr(self, '_type_hints') and self._type_hints:
            func_hints = self._type_hints
        else:
            try:
                if self._func:
                    func_hints = get_type_hints(self._func)
                else:
                    func_hints = {}
            except Exception:
                func_hints = {}
        # Extract parameters from cached signature or in_types
        parameters = {}
        type_map = {
            "string": "str",
            "integer": "int",
            "number": "int",
            "boolean": "bool",
            "object": "dict",
            "array": "list"
        }
        if sig is not None:
            # Use signature-based parameter extraction
            for param in sig.parameters.values():
                if param.name == 'self':
                    continue
                # Check type hint first
                if param.name in func_hints:
                    param_type = func_hints[param.name]
                    type_name = getattr(param_type, '__name__', str(param_type))
                elif self._in_types and param.name in self._in_types:
                    # Fallback to in_types schema if no type hint
                    schema = self._in_types[param.name]
                    schema_dict = convert_xschema(schema)
                    if isinstance(schema_dict, dict):
                        raw_type = schema_dict.get("type")
                        raw = raw_type or "string"
                        type_name = type_map.get(raw, str(raw))
                    else:
                        type_name = "Any"
                else:
                    type_name = "Any"
                parameters[param.name] = {
                    "type": type_name,
                    "required": param.default == inspect.Parameter.empty,
                }
                if param.default != inspect.Parameter.empty:
                    parameters[param.name]["default"] = param.default
        elif self._in_types:
            # Fallback to in_types-based extraction
            type_map = {
                "string": "str",
                "integer": "int",
                "number": "int",
                "boolean": "bool",
                "object": "dict",
                "array": "list"
            }
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
        # Get return type from cached value
        if hasattr(self, '_return_type') and self._return_type is not None:
            returns_type = getattr(self._return_type, "__name__", str(self._return_type))
        elif func_hints and 'return' in func_hints:
            ret = func_hints.get('return')
            if ret is not None:
                returns_type = getattr(ret, "__name__", str(ret))
            else:
                returns_type = "Any"
        else:
            returns_type = "Any"
        result = {
            "operationId": self._operationId,
            "api_name": self._api_name,
            "summary": self._summary,
            "description": self._description,
            "tags": self._tags,
            "profile": self._profile.value if hasattr(self, '_profile') else None,
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
            "dependencies": self._dependencies,
            "responses": self._responses,
            "examples": self._examples,
            "deprecated": self._deprecated,
            "engines": self.engines,
            "parameters": parameters,
            "returns": returns_type
        }
        # Only add in_types/out_types if they exist
        if self._in_types:
            result["in_types"] = convert_xschema(self._in_types)
        if self._out_types:
            result["out_types"] = convert_xschema(self._out_types)
        # Add function location info if available (for reconstruction)
        if self._func:
            if hasattr(self, '_function_module') and self._function_module:
                result["function_module"] = self._function_module
            else:
                result["function_module"] = self._func.__module__
            if hasattr(self, '_function_qualname') and self._function_qualname:
                result["function_qualname"] = self._function_qualname
            else:
                result["function_qualname"] = f"{self._func.__module__}.{getattr(self._func, '__qualname__', self._func.__name__)}"
        # Remove None values for cleaner output (avoids writing None values to JSON)
        return {k: v for k, v in result.items() if v is not None}
    # ============================================================================
    # XWObject Implementation
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
            "profile": self.profile.value if hasattr(self.profile, 'value') else str(self.profile),
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
        # For now, this is a placeholder for future implementation
        logger.debug(f"Saving action metadata: {self.api_name}")

    def load(self, *args, **kwargs) -> None:
        """
        Load action metadata from storage.
        This loads the action definition metadata.
        """
        # Action metadata loading would be implemented here
        # For now, this is a placeholder for future implementation
        logger.debug(f"Loading action metadata: {self.api_name}")
# Utility functions


def register_action_profile(name: str, config: ProfileConfig):
    """Register a new action profile."""
    from .config import register_profile
    register_profile(name, config)


def get_action_profiles() -> dict[str, ProfileConfig]:
    """Get all action profiles."""
    from .config import get_all_profiles
    return get_all_profiles()


def create_smart_action(func: Callable, **overrides) -> XWAction:
    """Create a smart action with overrides."""
    return XWAction(smart_mode="smart", func=func, **overrides)
