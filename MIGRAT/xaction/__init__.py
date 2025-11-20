#!/usr/bin/env python3
"""
🌟 xAction Library - Modular Implementation
Production-grade action decorators with comprehensive features.

This library provides:
- xAction: Enhanced action decorator with modular features
- Smart inference with profiles and convention-based defaults
- OpenAPI 3.1 compliance for full API documentation  
- Security integration with xAuth (OAuth2, API keys, MFA, rate limiting)
- Workflow orchestration with monitoring and rollback
- Contract validation with xSchema integration
- FastAPI-style dependency injection
- Background task execution with retry logic
- Pluggable engine system (Native, FastAPI, Celery, Prefect)
- Cross-cutting concerns handlers (Validation, Security, Monitoring, Workflow)

Key Features:
✅ Smart Inference: @xAction("smart") - Auto-detects action characteristics
✅ Profile System: Pre-configured profiles (query, command, task, workflow, endpoint)
✅ OpenAPI 3.1: Full compliance with operation specs, examples, responses
✅ Security: xAuth integration, OAuth2, API keys, MFA, rate limiting, audit
✅ Workflows: Multi-step orchestration with rollback capabilities
✅ Contracts: Input/output validation with xSchema integration
✅ Dependencies: FastAPI-style dependency injection
✅ Monitoring: Metrics, alerts, performance tracking
✅ Caching: Smart caching with TTL support
✅ Async: Full async/await support with background tasks
✅ Engines: Pluggable execution engines (Native, FastAPI, Celery, Prefect)
✅ Handlers: Cross-cutting concerns (Validation, Security, Monitoring, Workflow)

Usage Examples:
    # Smart inference
    @xAction("smart")
    def get_user_profile(self): pass
    
    # Profile-based with security
    @xAction(profile="command", roles=["admin"], audit=True)
    def delete_user(self, user_id: str): pass
    
    # Full OpenAPI with contracts
    @xAction(
        operationId="updateUserEmail",
        tags=["users"],
        security={"oauth2": ["write:users"]},
        contracts={"input": {"email": "string:email"}},
        examples={"request": {"email": "user@example.com"}}
    )
    def update_email(self, email: str): pass
    
    # Workflow with monitoring
    @xAction(
        profile="workflow",
        steps=[
            {"name": "validate", "timeout": 5},
            {"name": "process", "retry": 3},
            {"name": "notify", "async": True}
        ],
        monitor={"metrics": ["duration", "success_rate"]},
        rollback=True
    )
    def process_order(self, order: dict): pass
    
    # Multi-engine configuration
    @xAction(
        profile="task",
        engine=["celery", "prefect"],
        handlers=["validation", "security", "monitoring"]
    )
    def process_data(self, data: dict): pass
"""

# Core xAction decorator (using new modular facade)
from .facade import xAction

# Core interfaces and base classes
from .abc import iAction, aAction

# Core components
from .core import (
    ActionProfile, ProfileConfig, PROFILE_CONFIGS,
    ActionContext, ActionResult,
    action_executor, action_validator, openapi_generator
)
from .model import ActionRegistry

# Engine system
from .engines import (
    iActionEngine,
    aActionEngineBase,
    ActionEngineType,
    ActionEngineConfig,
    ActionEngineRegistry,
    action_engine_registry,
    NativeActionEngine,
    FastAPIActionEngine,
    CeleryActionEngine,
    PrefectActionEngine
)

# Handler system
from .handlers import (
    iActionHandler,
    aActionHandlerBase,
    ActionHandlerPhase,
    ActionHandlerConfig,
    ActionHandlerRegistry,
    action_handler_registry,
    ValidationActionHandler,
    SecurityActionHandler,
    MonitoringActionHandler,
    WorkflowActionHandler
)

# Error classes
from .errors import (
    xActionError,
    xActionValidationError,
    xActionSecurityError,
    xActionWorkflowError,
    xActionEngineError,
    xActionPermissionError,
    xActionExecutionError
)

# Utility functions
from .facade import register_action_profile, get_action_profiles, create_smart_action

# Convenience exports
__all__ = [
    # Main decorator
    "xAction",
    
    # Core interfaces
    "iAction",
    "aAction",
    
    # Core components
    "ActionProfile",
    "ProfileConfig", 
    "PROFILE_CONFIGS",
    "ActionContext",
    "ActionResult",
    "ActionRegistry",
    "action_executor",
    "action_validator",
    "openapi_generator",
    
    # Engine system
    "iActionEngine",
    "aActionEngineBase",
    "ActionEngineType",
    "ActionEngineConfig",
    "ActionEngineRegistry",
    "action_engine_registry",
    "NativeActionEngine",
    "FastAPIActionEngine",
    "CeleryActionEngine",
    "PrefectActionEngine",
    
    # Handler system
    "iActionHandler",
    "aActionHandlerBase",
    "ActionHandlerPhase",
    "ActionHandlerConfig",
    "ActionHandlerRegistry",
    "action_handler_registry",
    "ValidationActionHandler",
    "SecurityActionHandler",
    "MonitoringActionHandler",
    "WorkflowActionHandler",
    
    # Error classes
    "xActionError",
    "xActionValidationError",
    "xActionSecurityError",
    "xActionWorkflowError",
    "xActionEngineError",
    "xActionPermissionError",
    "xActionExecutionError",
    
    # Utility functions
    "register_action_profile",
    "get_action_profiles",
    "create_smart_action"
]

# Version information
__version__ = "2.0.0"
__author__ = "xComBot Team"
__description__ = "Production-grade action decorators with comprehensive features" 