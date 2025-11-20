#!/usr/bin/env python3
"""
🎯 Security Action Handler Implementation
Security and authentication handler for xAction.
"""

import time
from typing import Any, Dict, Optional, Set

from .abc import aActionHandlerBase, ActionHandlerPhase
from ..abc import ActionContext
from src.xlib.xsystem import get_logger

logger = get_logger(__name__)


class SecurityActionHandler(aActionHandlerBase):
    """
    🌟 Security Action Handler
    
    Handles security, authentication, and authorization for actions.
    Integrates with xAuth for comprehensive security features.
    """
    
    def __init__(self):
        super().__init__(
            name="security",
            priority=90,  # High priority - security should run early
            async_enabled=True
        )
        self._auth_client = None
        self._rate_limit_cache = {}
        self._audit_log = []
    
    @property
    def supported_phases(self) -> Set[ActionHandlerPhase]:
        """Security handler supports before and after phases."""
        return {ActionHandlerPhase.BEFORE, ActionHandlerPhase.AFTER}
    
    def before_execution(self, action: 'xAction', context: ActionContext, **kwargs) -> bool:
        """Execute security checks before action execution."""
        try:
            # Skip security checks if no security is configured
            if not hasattr(action, 'security_config') or not action.security_config:
                return True
            
            # Check authentication if required
            if action.security_config:
                if not self._check_authentication(action, context):
                    logger.warning(f"Authentication failed for action {action.api_name}")
                    return False
            
            # Check authorization
            if not self._check_authorization(action, context):
                logger.warning(f"Authorization failed for action {action.api_name}")
                return False
            
            # Check rate limiting
            if not self._check_rate_limit(action, context):
                logger.warning(f"Rate limit exceeded for action {action.api_name}")
                return False
            
            # Log audit event if enabled
            if getattr(action, 'audit_enabled', False):
                self._log_audit_event(action, context, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Security check failed: {e}")
            return False
    
    def after_execution(self, action: 'xAction', context: ActionContext, result: Any, **kwargs) -> bool:
        """
        Perform security audit after execution.
        
        Args:
            action: The action that was executed
            context: Execution context
            result: The execution result
            **kwargs: Additional parameters
            
        Returns:
            True if audit passes, False otherwise
        """
        try:
            start_time = time.time()
            
            # Log audit event
            audit_result = self._log_audit_event(action, context, result)
            
            duration = time.time() - start_time
            self._update_metrics(duration, audit_result)
            
            if not audit_result:
                logger.warning(f"Audit logging failed for action {action.api_name}")
                return False
            
            logger.debug(f"Security audit completed for action {action.api_name}")
            return True
            
        except Exception as e:
            logger.error(f"Security handler error in after_execution: {e}")
            return False
    
    def on_error(self, action: 'xAction', context: ActionContext, error: Exception, **kwargs) -> bool:
        """
        Handle security errors.
        
        Args:
            action: The action that failed
            context: Execution context
            error: The exception that occurred
            **kwargs: Additional parameters
            
        Returns:
            True if error was handled, False otherwise
        """
        logger.error(f"Security error for action {action.api_name}: {error}")
        
        # Log security incident
        self._log_security_incident(action, context, error)
        
        return True  # Always handle security errors gracefully
    
    def _check_authentication(self, action: 'xAction', context: ActionContext) -> bool:
        """Check if the user is authenticated."""
        try:
            # Get authentication token from context
            token = context.metadata.get("auth_token")
            if not token:
                logger.warning("No authentication token provided")
                return False
            
            # Validate token using xAuth
            if self._auth_client:
                return self._auth_client.validate_token(token)
            else:
                # Fallback to basic token validation
                return self._basic_token_validation(token)
                
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            return False
    
    def _check_authorization(self, action: 'xAction', context: ActionContext) -> bool:
        """Check if the user is authorized to perform the action."""
        try:
            # Get required roles from action
            required_roles = getattr(action, 'roles', [])
            if not required_roles:
                return True  # No roles required
            
            # Get user roles from context
            user_roles = context.metadata.get("user_roles", [])
            if not user_roles:
                logger.warning("No user roles provided")
                return False
            
            # Check if user has required roles
            for required_role in required_roles:
                if required_role not in user_roles:
                    logger.warning(f"User missing required role: {required_role}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Authorization check failed: {e}")
            return False
    
    def _check_rate_limit(self, action: 'xAction', context: ActionContext) -> bool:
        """Check if the action is within rate limits."""
        try:
            # Get rate limit configuration
            rate_limit = getattr(action, 'rate_limit', None)
            if not rate_limit:
                return True  # No rate limiting configured
            
            # Get user identifier
            user_id = context.actor or "anonymous"
            
            # Check rate limit
            current_time = time.time()
            key = f"{user_id}:{action.api_name}"
            
            if key in self._rate_limit_cache:
                last_request_time = self._rate_limit_cache[key]
                if current_time - last_request_time < rate_limit:
                    return False
            
            # Update rate limit cache
            self._rate_limit_cache[key] = current_time
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False
    
    def _log_audit_event(self, action: 'xAction', context: ActionContext, result: Any) -> bool:
        """Log audit event for the action."""
        try:
            audit_event = {
                "timestamp": time.time(),
                "action_name": action.api_name,
                "actor": context.actor,
                "source": context.source,
                "trace_id": context.trace_id,
                "success": True,
                "result_type": type(result).__name__
            }
            
            self._audit_log.append(audit_event)
            
            # Send to external audit system if configured
            if self._auth_client:
                self._auth_client.log_audit_event(audit_event)
            
            return True
            
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
            return False
    
    def _log_security_incident(self, action: 'xAction', context: ActionContext, error: Exception):
        """Log security incident."""
        try:
            incident = {
                "timestamp": time.time(),
                "action_name": action.api_name,
                "actor": context.actor,
                "source": context.source,
                "trace_id": context.trace_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "severity": "high"
            }
            
            self._audit_log.append(incident)
            
            # Send to security monitoring system
            if self._auth_client:
                self._auth_client.log_security_incident(incident)
                
        except Exception as e:
            logger.error(f"Security incident logging failed: {e}")
    
    def _basic_token_validation(self, token: str) -> bool:
        """Basic token validation fallback."""
        # Simple token format validation
        if not token or len(token) < 10:
            return False
        
        # Check if token is not expired (basic check)
        try:
            # This is a simplified check - in practice, you'd decode and validate JWT
            return "exp" not in token or time.time() < float(token.split(".")[-1])
        except:
            return False
    
    def setup(self, config: Dict[str, Any]) -> bool:
        """Setup security handler."""
        try:
            # Initialize xAuth client if available
            try:
                from src.xlib.xauth import xAuthClient
                self._auth_client = xAuthClient()
                logger.debug("xAuth client initialized for security handler")
            except ImportError:
                logger.debug("xAuth not available, using basic security")
            
            # Clear caches
            self._rate_limit_cache.clear()
            self._audit_log.clear()
            
            logger.debug("Security action handler setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup security handler: {e}")
            return False
    
    def teardown(self) -> bool:
        """Teardown security handler."""
        self._auth_client = None
        self._rate_limit_cache.clear()
        self._audit_log.clear()
        logger.debug("Security action handler teardown completed")
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get security handler metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "handler_type": "security",
            "audit_events": len(self._audit_log),
            "rate_limit_entries": len(self._rate_limit_cache),
            "auth_client_available": self._auth_client is not None
        })
        return metrics
