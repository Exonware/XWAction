#!/usr/bin/env python3
"""
🎯 xAction Handlers Package
Cross-cutting concerns handlers for action execution.
"""

# Core interfaces and base classes
from .abc import (
    iActionHandler,
    aActionHandlerBase,
    ActionHandlerPhase,
    ActionHandlerConfig,
    ActionHandlerRegistry,
    action_handler_registry
)

# Concrete handler implementations
from .validation import ValidationActionHandler
from .security import SecurityActionHandler
from .monitoring import MonitoringActionHandler
from .workflow import WorkflowActionHandler

# Convenience exports
__all__ = [
    # Interfaces and base classes
    "iActionHandler",
    "aActionHandlerBase",
    "ActionHandlerPhase",
    "ActionHandlerConfig",
    "ActionHandlerRegistry",
    "action_handler_registry",
    
    # Concrete handlers
    "ValidationActionHandler",
    "SecurityActionHandler",
    "MonitoringActionHandler",
    "WorkflowActionHandler"
]
