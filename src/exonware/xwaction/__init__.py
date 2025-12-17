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
from .defs import ActionProfile, ActionHandlerPhase
from .config import XWActionConfig
from .context import ActionContext, ActionResult
from .registry import ActionRegistry

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
    "XWActionConfig",
    "ActionContext",
    "ActionResult",
    "ActionRegistry",
]

