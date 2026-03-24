#exonware/xwaction/__init__.py
"""
XWAction - Modern Action Decorator Library
Production-grade action decorator with comprehensive features:
- Smart inference with profiles and convention-based defaults
- OpenAPI 3.1 compliance for full API documentation
- Security integration (OAuth2, API keys, MFA, rate limiting)
- Workflow orchestration with monitoring and rollback
- Contract validation with XWSchema integration
- Pluggable engine system (Native, FastAPI, Celery, Prefect)
- Cross-cutting concerns handlers (Validation, Security, Monitoring, Workflow)
"""
# =============================================================================
# XWLAZY INTEGRATION - Optional: install exonware-xwaction[lazy] for auto-enable
# =============================================================================
from .version import __version__
from .facade import XWAction
from .errors import (
    XWActionError,
    XWActionValidationError,
    XWActionSecurityError,
    XWActionWorkflowError,
    XWActionEngineError,
    XWActionPermissionError,
    XWActionExecutionError
)
from .defs import ActionProfile, ActionHandlerPhase, ActionParameter
from .config import (
    XWActionConfig,
    ProfileConfig,
    PROFILE_CONFIGS,
    get_profile_config,
    register_profile,
    get_all_profiles,
)
from .context import ActionContext, ActionResult
from .registry import ActionRegistry
from .core import action_executor, action_validator, openapi_generator, DEFAULT_CONTEXT_PARAMS
from .engines import (
    IActionEngine,
    ActionEngineType,
    ActionEngineConfig,
    ActionEngineRegistry,
    action_engine_registry,
    NativeActionEngine,
    FastAPIActionEngine,
)
from .handlers import (
    IActionHandler,
    ActionHandlerConfig,
    ActionHandlerRegistry,
    action_handler_registry,
    ValidationActionHandler,
    SecurityActionHandler,
    MonitoringActionHandler,
    WorkflowActionHandler,
)
from .action_utils import extract_actions, load_actions
from .base import AActionsProvider
from .contracts import IActionsProvider, IAction, IActionAuthorizer, AuthzDecision
__all__ = [
    "__version__",
    "XWAction",
    "XWActionError",
    "XWActionValidationError",
    "XWActionSecurityError",
    "XWActionWorkflowError",
    "XWActionEngineError",
    "XWActionPermissionError",
    "XWActionExecutionError",
    "ActionProfile",
    "ActionHandlerPhase",
    "ActionParameter",
    "XWActionConfig",
    "ProfileConfig",
    "PROFILE_CONFIGS",
    "get_profile_config",
    "register_profile",
    "get_all_profiles",
    "ActionContext",
    "ActionResult",
    "ActionRegistry",
    "action_executor",
    "action_validator",
    "openapi_generator",
    "DEFAULT_CONTEXT_PARAMS",
    # engines
    "IActionEngine",
    "ActionEngineType",
    "ActionEngineConfig",
    "ActionEngineRegistry",
    "action_engine_registry",
    "NativeActionEngine",
    "FastAPIActionEngine",
    # handlers
    "IActionHandler",
    "ActionHandlerConfig",
    "ActionHandlerRegistry",
    "action_handler_registry",
    "ValidationActionHandler",
    "SecurityActionHandler",
    "MonitoringActionHandler",
    "WorkflowActionHandler",
    # utilities
    "extract_actions",
    "load_actions",
    "AActionsProvider",
    "IActionsProvider",
    "IAction",
    "IActionAuthorizer",
    "AuthzDecision",
]
