#!/usr/bin/env python3
"""
🎯 xAction Execution Engine
Core execution logic for actions with engine and handler integration.
"""

import time
import asyncio
from typing import Any, Dict, Optional, List, Callable
from functools import wraps

from .context import ActionContext, ActionResult
from .config import ActionProfile, ProfileConfig
from ..engines import action_engine_registry, ActionEngineType, NativeActionEngine
from ..handlers import action_handler_registry, ActionHandlerPhase
from ..errors import xActionPermissionError
from src.xlib.xdata.core.exceptions import SchemaValidationError
from src.xlib.xsystem import get_logger

logger = get_logger(__name__)


class ActionExecutor:
    """
    🌟 Action Executor
    
    Handles the execution of actions with engine and handler integration.
    """
    
    def __init__(self):
        self._cache = {}
        self._metrics = {
            "executions": 0,
            "errors": 0,
            "total_duration": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def execute(self, action: 'xAction', context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """
        Execute an action with full engine and handler pipeline.
        
        Args:
            action: The action to execute
            context: Execution context
            instance: The entity instance (self in decorated method)
            **kwargs: Action parameters
            
        Returns:
            ActionResult with execution results
        """
        start_time = time.time()
        
        try:
            # Built-in input validation (always on)
            try:
                from ..core.validation import action_validator as _validator
                validation_result = _validator.validate_inputs(action, kwargs)
                if not validation_result.valid:
                    raise SchemaValidationError("Action validation failed", errors=validation_result.errors)
            except Exception as ve:
                if isinstance(ve, SchemaValidationError):
                    raise
                # If validator import failed, continue (no-op)
            
            # Execute BEFORE handlers
            if not self._execute_handlers(ActionHandlerPhase.BEFORE, action, context, **kwargs):
                raise SchemaValidationError("Action validation failed", errors=["handler_before_validation_failed"])

            # Permission check (after validation)
            if hasattr(action, 'check_permissions'):
                # Build a unified roles list from context supporting both keys
                ctx_roles = context.metadata.get('roles') or context.metadata.get('user_roles') or []
                ctx = ActionContext(actor=context.actor, source=context.source, trace_id=context.trace_id, metadata={"roles": ctx_roles})
                if not action.check_permissions(ctx):
                    raise xActionPermissionError(action.api_name, getattr(action, 'roles', []), ctx_roles)
            
            # Select and execute engine
            engine = self._select_engine(action)
            if not engine:
                # Ensure native engine exists
                native = action_engine_registry.get_engine("native")
                if native is None:
                    native = NativeActionEngine()
                    action_engine_registry.register(native)
                engine = native
            
            # Execute the action
            result = engine.execute(action, context, instance, **kwargs)
            
            # AFTER handlers with output validation
            if not self._execute_handlers(ActionHandlerPhase.AFTER, action, context, result=result.data, **kwargs):
                raise SchemaValidationError("Output validation failed", errors=["handler_after_validation_failed"])
            
            # FINALLY handlers
            self._execute_handlers(ActionHandlerPhase.FINALLY, action, context, **kwargs)
            
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._update_metrics(duration, False)
            
            # ERROR handlers
            try:
                self._execute_handlers(ActionHandlerPhase.ERROR, action, context, error=e, **kwargs)
                self._execute_handlers(ActionHandlerPhase.FINALLY, action, context, **kwargs)
            finally:
                pass
            
            logger.error(f"Action execution failed: {e}")
            
            # Propagate validation and permission errors for tests expecting exceptions
            if isinstance(e, (SchemaValidationError, xActionPermissionError)):
                raise
            
            return ActionResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={
                    "phase": "execution",
                    "error_type": type(e).__name__
                }
            )
    
    def _select_engine(self, action: 'xAction'):
        """Select the appropriate engine for the action."""
        try:
            # Get configured engines
            engines = getattr(action, 'engines', ["native"])
            
            # Try each engine in order
            for engine_name in engines:
                engine = action_engine_registry.get_engine(engine_name)
                if engine and engine.can_execute(action.profile):
                    return engine
            
            # Fallback to native engine
            return action_engine_registry.get_engine("native")
            
        except Exception as e:
            logger.error(f"Engine selection failed: {e}")
            return action_engine_registry.get_engine("native")
    
    def _execute_handlers(self, phase: ActionHandlerPhase, action: 'xAction', 
                         context: ActionContext, **kwargs) -> bool:
        """Execute handlers for a specific phase."""
        try:
            # Get configured handlers
            handlers = getattr(action, 'handlers', [])
            if not handlers:
                return True
            
            # Execute handlers
            if phase in [ActionHandlerPhase.BEFORE, ActionHandlerPhase.AFTER, ActionHandlerPhase.ERROR]:
                return action_handler_registry.execute_phase(phase, action, context, **kwargs)
            else:  # FINALLY
                action_handler_registry.execute_phase(phase, action, context, **kwargs)
                return True
                
        except Exception as e:
            logger.error(f"Handler execution failed for phase {phase}: {e}")
            return phase != ActionHandlerPhase.BEFORE  # Only abort on BEFORE phase
    
    def _update_metrics(self, duration: float, success: bool):
        """Update execution metrics."""
        self._metrics["executions"] += 1
        self._metrics["total_duration"] += duration
        if not success:
            self._metrics["errors"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        total_executions = self._metrics["executions"]
        
        return {
            "executor": "action_executor",
            "executions": total_executions,
            "errors": self._metrics["errors"],
            "total_duration": self._metrics["total_duration"],
            "average_duration": (
                self._metrics["total_duration"] / total_executions 
                if total_executions > 0 else 0.0
            ),
            "error_rate": (
                self._metrics["errors"] / total_executions 
                if total_executions > 0 else 0.0
            ),
            "cache_hits": self._metrics["cache_hits"],
            "cache_misses": self._metrics["cache_misses"],
            "cache_hit_rate": (
                self._metrics["cache_hits"] / (self._metrics["cache_hits"] + self._metrics["cache_misses"])
                if (self._metrics["cache_hits"] + self._metrics["cache_misses"]) > 0 else 0.0
            )
        }

    async def execute_phase_async(self, phase: ActionHandlerPhase, action: 'xAction',
                               context: ActionContext, **kwargs) -> bool:
        """
        Execute all action handlers for a specific phase asynchronously.
        
        Args:
            phase: The phase to execute
            action: The action being processed
            context: Execution context
            **kwargs: Additional parameters
            
        Returns:
            True if all handlers succeeded, False otherwise
        """
        handlers = action_handler_registry.get_handlers_for_phase(phase)
        
        # Execute async handlers concurrently
        async_tasks = []
        sync_handlers = []
        
        for handler in handlers:
            if handler.async_enabled:
                async_tasks.append((handler, dict(kwargs)))
            else:
                sync_handlers.append(handler)
        
        # Execute sync handlers first
        for handler in sync_handlers:
            try:
                start_time = time.time()
                
                if phase == ActionHandlerPhase.BEFORE:
                    result = await asyncio.to_thread(handler.before_execution, action, context, **kwargs)
                elif phase == ActionHandlerPhase.AFTER:
                    filtered = dict(kwargs)
                    filtered.pop('result', None)
                    result = await asyncio.to_thread(handler.after_execution, action, context, kwargs.get('result'))
                elif phase == ActionHandlerPhase.ERROR:
                    filtered = dict(kwargs)
                    filtered.pop('error', None)
                    result = await asyncio.to_thread(handler.on_error, action, context, kwargs.get('error'))
                else:  # FINALLY
                    result = True
                
                duration = time.time() - start_time
                handler._update_metrics(duration, result)
                
                if not result:
                    logger.warning(f"Action handler {handler.name} failed for phase {phase.value}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error in action handler {handler.name} for phase {phase.value}: {e}")
                return False
        
        # Execute async handlers
        if async_tasks:
            results = []
            for handler, handler_kwargs in async_tasks:
                try:
                    start_time = time.time()
                    if phase == ActionHandlerPhase.BEFORE:
                        res = await handler.before_execution(action, context, **handler_kwargs)
                    elif phase == ActionHandlerPhase.AFTER:
                        filtered = dict(handler_kwargs)
                        filtered.pop('result', None)
                        res = await handler.after_execution(action, context, handler_kwargs.get('result'))
                    elif phase == ActionHandlerPhase.ERROR:
                        filtered = dict(handler_kwargs)
                        filtered.pop('error', None)
                        res = await handler.on_error(action, context, handler_kwargs.get('error'))
                    else:
                        res = True
                    duration = time.time() - start_time
                    handler._update_metrics(duration, res)
                    results.append(res)
                except Exception as e:
                    logger.error(f"Error in async action handler {handler.name}: {e}")
                    return False
            for res in results:
                if not res:
                    return False
        
        return True


# Global executor instance
action_executor = ActionExecutor()
