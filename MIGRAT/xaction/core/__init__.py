#!/usr/bin/env python3
"""
🎯 xAction Core Package
Core components for action management, execution, and configuration.
"""

# Configuration
from .config import (
    ActionProfile,
    ProfileConfig,
    PROFILE_CONFIGS,
    WorkflowStep,
    MonitoringConfig,
    SecurityConfig,
    ContractConfig,
    get_profile_config,
    register_profile,
    get_all_profiles
)

# Context and results
from .context import ActionContext, ActionResult

# Execution engine
from .execution import ActionExecutor, action_executor

# Validation engine
from .validation import ActionValidator, ValidationResult, action_validator

# OpenAPI generator
from .openapi import OpenAPIGenerator, OpenAPISpec, openapi_generator

# Convenience exports
__all__ = [
    # Configuration
    "ActionProfile",
    "ProfileConfig", 
    "PROFILE_CONFIGS",
    "WorkflowStep",
    "MonitoringConfig",
    "SecurityConfig",
    "ContractConfig",
    "get_profile_config",
    "register_profile",
    "get_all_profiles",
    
    # Context and results
    "ActionContext",
    "ActionResult",
    
    # Execution engine
    "ActionExecutor",
    "action_executor",
    
    # Validation engine
    "ActionValidator",
    "ValidationResult",
    "action_validator",
    
    # OpenAPI generator
    "OpenAPIGenerator",
    "OpenAPISpec",
    "openapi_generator"
]
