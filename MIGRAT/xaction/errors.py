#!/usr/bin/env python3
"""
🚨 xAction Error Classes
Simple, focused exceptions for action execution.
"""

from typing import Optional, Any, Dict


class xActionError(Exception):
    """Base exception for all xAction errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class xActionValidationError(xActionError):
    """Raised when action input/output validation fails."""
    
    def __init__(self, message: str, param_name: Optional[str] = None, 
                 constraint: Optional[str] = None, value: Any = None):
        details = {
            "param": param_name,
            "constraint": constraint,
            "value": value
        }
        super().__init__(message, details)


class xActionSecurityError(xActionError):
    """Raised when security checks fail (authentication, authorization, rate limiting)."""
    
    def __init__(self, message: str, security_type: str = "general", 
                 details: Optional[Dict[str, Any]] = None):
        error_details = {
            "security_type": security_type,
            **(details or {})
        }
        super().__init__(message, error_details)


class xActionWorkflowError(xActionError):
    """Raised when workflow execution fails."""
    
    def __init__(self, message: str, workflow_step: Optional[str] = None,
                 step_number: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        error_details = {
            "workflow_step": workflow_step,
            "step_number": step_number,
            **(details or {})
        }
        super().__init__(message, error_details)


class xActionEngineError(xActionError):
    """Raised when engine execution fails."""
    
    def __init__(self, message: str, engine_name: Optional[str] = None,
                 engine_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = {
            "engine_name": engine_name,
            "engine_type": engine_type,
            **(details or {})
        }
        super().__init__(message, error_details)


class xActionPermissionError(xActionError):
    """Raised when user lacks permission to execute action."""
    
    def __init__(self, action_name: str, required_roles: list, 
                 user_roles: Optional[list] = None):
        message = f"Permission denied for action '{action_name}'. Required roles: {required_roles}"
        details = {
            "action": action_name,
            "required_roles": required_roles,
            "user_roles": user_roles or []
        }
        super().__init__(message, details)
        self.api_name = action_name
        self.required_roles = required_roles
        self.user_roles = user_roles or []


class xActionExecutionError(xActionError):
    """Raised when action execution fails."""
    
    def __init__(self, action_name: str, original_error: Exception):
        message = f"Action '{action_name}' failed: {str(original_error)}"
        details = {
            "action": action_name,
            "error_type": type(original_error).__name__,
            "error_message": str(original_error)
        }
        super().__init__(message, details)
        self.api_name = action_name
        self.original_error = original_error 