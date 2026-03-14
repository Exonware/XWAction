#exonware/xwaction/core/execution.py
"""
XWAction Execution Engine
Core execution logic for actions with engine and handler integration.
"""

import time
import asyncio
from typing import Any
from ..context import ActionContext, ActionResult
from ..defs import ActionProfile
from ..errors import XWActionPermissionError
from exonware.xwschema import XWSchemaValidationError
from exonware.xwsystem import get_logger
from collections.abc import Callable
logger = get_logger(__name__)


class ActionExecutor:
    """
    Action Executor
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

    def execute(self, action: Any, context: ActionContext, 
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
                from .validation import action_validator as _validator
                validation_result = _validator.validate_inputs(action, kwargs)
                if not validation_result.valid:
                    raise XWSchemaValidationError(
                        "Action validation failed",
                        context={"issues": [{"message": err} for err in validation_result.errors]},
                    )
            except Exception as ve:
                if isinstance(ve, XWSchemaValidationError):
                    raise
                # If validator import failed, continue (no-op)
            # Execute BEFORE handlers
            try:
                from ..defs import ActionHandlerPhase
                if not self._execute_handlers(ActionHandlerPhase.BEFORE, action, context, **kwargs):
                    raise XWSchemaValidationError(
                        "Action validation failed",
                        context={"issues": [{"message": "handler_before_validation_failed"}]},
                    )
            except Exception as e:
                if isinstance(e, XWSchemaValidationError):
                    raise
                logger.warning(f"Handler execution failed: {e}")
            # Permission check (after validation)
            if hasattr(action, 'check_permissions'):
                # Build a unified roles list from context supporting both keys
                ctx_roles = context.metadata.get('roles') or context.metadata.get('user_roles') or []
                ctx = ActionContext(actor=context.actor, source=context.source, trace_id=context.trace_id, metadata={"roles": ctx_roles})
                if not action.check_permissions(ctx):
                    raise XWActionPermissionError(
                        action.api_name, 
                        required=getattr(action, 'roles', []), 
                        actual=ctx_roles
                    )
            # Select and execute engine
            engine = self._select_engine(action)
            if not engine:
                # Fallback to direct execution
                result = self._execute_direct(action, context, instance, **kwargs)
            else:
                result = engine.execute(action, context, instance, **kwargs)
            # If the engine returns an ActionResult failure, treat it as an error-phase execution
            # (MIGRAT parity: failed results should still run ERROR handlers).
            if isinstance(result, ActionResult) and not result.success:
                duration = time.time() - start_time
                self._update_metrics(duration, False)
                from ..defs import ActionHandlerPhase
                self._execute_handlers(ActionHandlerPhase.ERROR, action, context, error=Exception(result.error or "execution_failed"), **kwargs)
                self._execute_handlers(ActionHandlerPhase.FINALLY, action, context, **kwargs)
                return result
            # AFTER handlers with output validation
            try:
                from ..defs import ActionHandlerPhase
                if not self._execute_handlers(ActionHandlerPhase.AFTER, action, context, result=result.data, **kwargs):
                    raise XWSchemaValidationError(
                        "Output validation failed",
                        context={"issues": [{"message": "handler_after_validation_failed"}]},
                    )
            except Exception as e:
                if isinstance(e, XWSchemaValidationError):
                    raise
                logger.warning(f"Handler execution failed: {e}")
            # FINALLY handlers
            from ..defs import ActionHandlerPhase
            self._execute_handlers(ActionHandlerPhase.FINALLY, action, context, **kwargs)
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self._update_metrics(duration, False)
            # ERROR handlers
            try:
                from ..defs import ActionHandlerPhase
                self._execute_handlers(ActionHandlerPhase.ERROR, action, context, error=e, **kwargs)
                self._execute_handlers(ActionHandlerPhase.FINALLY, action, context, **kwargs)
            finally:
                pass
            logger.error(f"Action execution failed: {e}")
            # Propagate validation and permission errors
            if isinstance(e, (XWSchemaValidationError, XWActionPermissionError)):
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

    def _execute_direct(self, action: Any, context: ActionContext, instance: Any, **kwargs) -> ActionResult:
        """Execute action directly without engine."""
        try:
            if not action.func:
                raise ValueError("Action has no function to execute")
            # Execute the function
            if instance is not None:
                result_data = action.func(instance, **kwargs)
            else:
                result_data = action.func(**kwargs)
            return ActionResult.success(data=result_data)
        except Exception as e:
            return ActionResult.failure(error=str(e))

    def _select_engine(self, action: Any):
        """Select the appropriate engine for the action."""
        try:
            # Try to import engine registry
            from ..engines import action_engine_registry
            from ..engines.native import NativeActionEngine
            # Get configured engines
            engines = getattr(action, 'engines', ["native"])
            # Try each engine in order
            for engine_name in engines:
                engine = action_engine_registry.get_engine(engine_name)
                if engine and engine.can_execute(action.profile):
                    return engine
            # Fallback to native engine
            native = action_engine_registry.get_engine("native")
            if native is None:
                native = NativeActionEngine()
                action_engine_registry.register(native)
            return native
        except Exception as e:
            logger.error(f"Engine selection failed: {e}")
            return None

    def _execute_handlers(self, phase: Any, action: Any, 
                         context: ActionContext, **kwargs) -> bool:
        """Execute handlers for a specific phase."""
        try:
            from ..handlers import action_handler_registry
            # Get configured handlers
            handler_names = getattr(action, 'handlers', []) or []
            if not handler_names:
                return True
            selected = set(handler_names)
            handlers = [
                h for h in action_handler_registry.get_handlers_for_phase(phase)
                if h.name in selected
            ]
            # Execute handlers (preserving registry ordering by priority)
            for handler in handlers:
                if phase.value == "before":
                    ok = handler.before_execution(action, context, **kwargs)
                    if not ok:
                        return False
                elif phase.value == "after":
                    ok = handler.after_execution(action, context, kwargs.get("result"))
                    if not ok:
                        return False
                elif phase.value == "error":
                    ok = handler.on_error(action, context, kwargs.get("error"))
                    if not ok:
                        return False
                else:
                    # FINALLY: best-effort
                    continue
            return True
        except Exception as e:
            logger.error(f"Handler execution failed for phase {phase}: {e}")
            return phase.value != 'before'  # Only abort on BEFORE phase

    def _update_metrics(self, duration: float, success: bool):
        """Update execution metrics."""
        self._metrics["executions"] += 1
        self._metrics["total_duration"] += duration
        if not success:
            self._metrics["errors"] += 1

    def get_metrics(self) -> dict[str, Any]:
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

    async def execute_phase_async(self, phase: Any, action: Any,
                                 context: ActionContext, **kwargs) -> bool:
        """
        Execute all action handlers for a specific phase asynchronously (MIGRAT parity).
        """
        try:
            from ..handlers import action_handler_registry
            return await action_handler_registry.execute_phase_async(phase, action, context, **kwargs)
        except Exception as e:
            logger.error(f"Async handler execution failed for phase {phase}: {e}")
            return getattr(phase, "value", str(phase)) != "before"
# Global executor instance
action_executor = ActionExecutor()
