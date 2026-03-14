#exonware/xwaction/handlers/__init__.py
"""Handler implementations for XWAction."""

import asyncio
import time
from typing import Any
from .contracts import IActionHandler
from .defs import ActionHandlerConfig
from .base import aActionHandlerBase
from ..context import ActionContext
from ..defs import ActionHandlerPhase
from exonware.xwsystem import get_logger
logger = get_logger(__name__)


class ActionHandlerRegistry:
    """
    Action Handler Registry
    Manages registration, execution, and configuration of action handlers.
    """

    def __init__(self):
        self._handlers: dict[str, IActionHandler] = {}
        self._configs: dict[str, ActionHandlerConfig] = {}
        self._phase_handlers: dict[ActionHandlerPhase, list[IActionHandler]] = {
            phase: [] for phase in ActionHandlerPhase
        }
        self._cache: dict[str, Any] = {}
        self._cache_ttl: dict[str, float] = {}

    def register(self, handler: IActionHandler | type[IActionHandler],
                 config: ActionHandlerConfig | None = None):
        """Register an action handler (supports instance or class, MIGRAT parity)."""
        if isinstance(handler, type):
            handler = handler()
        if config is None:
            config = ActionHandlerConfig(
                name=handler.name,
                enabled=True,
                async_enabled=handler.async_enabled,
                priority=handler.priority
            )
        self._handlers[handler.name] = handler
        self._configs[handler.name] = config
        # Add to phase-specific lists
        for phase in handler.supported_phases:
            self._phase_handlers[phase].append(handler)
        # Sort by priority (highest first)
        for phase in ActionHandlerPhase:
            self._phase_handlers[phase].sort(key=lambda h: h.priority, reverse=True)

    def enable(self, name: str):
        """Enable an action handler."""
        if name in self._configs:
            self._configs[name].enabled = True

    def disable(self, name: str):
        """Disable an action handler."""
        if name in self._configs:
            self._configs[name].enabled = False

    def get_handler(self, name: str) -> IActionHandler | None:
        """Get an action handler by name."""
        return self._handlers.get(name)

    def get_handlers_for_phase(self, phase: ActionHandlerPhase) -> list[IActionHandler]:
        """Get all action handlers for a specific phase."""
        handlers = self._phase_handlers.get(phase, [])
        return [h for h in handlers if self._configs[h.name].enabled]

    def execute_phase(self, phase: ActionHandlerPhase, action: Any, 
                     context: ActionContext, **kwargs) -> bool:
        """
        Execute all action handlers for a specific phase.
        Args:
            phase: The phase to execute
            action: The action being processed
            context: Execution context
            **kwargs: Additional parameters
        Returns:
            True if all handlers succeeded, False otherwise
        """
        handlers = self.get_handlers_for_phase(phase)
        for handler in handlers:
            try:
                start_time = time.time()
                if phase == ActionHandlerPhase.BEFORE:
                    result = handler.before_execution(action, context, **kwargs)
                elif phase == ActionHandlerPhase.AFTER:
                    filtered = dict(kwargs)
                    filtered.pop('result', None)
                    result = handler.after_execution(action, context, kwargs.get('result'))
                elif phase == ActionHandlerPhase.ERROR:
                    filtered = dict(kwargs)
                    filtered.pop('error', None)
                    result = handler.on_error(action, context, kwargs.get('error'))
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
        return True

    async def execute_phase_async(self, phase: ActionHandlerPhase, action: Any,
                                 context: ActionContext, **kwargs) -> bool:
        """
        Execute all action handlers for a specific phase asynchronously (MIGRAT parity).
        """
        handlers = self.get_handlers_for_phase(phase)
        async_tasks = []
        sync_handlers = []
        for handler in handlers:
            if getattr(handler, "async_enabled", False):
                async_tasks.append(self._execute_async_handler(handler, phase, action, context, **kwargs))
            else:
                sync_handlers.append(handler)
        # Execute sync handlers first
        for handler in sync_handlers:
            try:
                start_time = time.time()
                if phase == ActionHandlerPhase.BEFORE:
                    result = await asyncio.to_thread(handler.before_execution, action, context, **kwargs)
                elif phase == ActionHandlerPhase.AFTER:
                    result = await asyncio.to_thread(handler.after_execution, action, context, kwargs.get("result"))
                elif phase == ActionHandlerPhase.ERROR:
                    result = await asyncio.to_thread(handler.on_error, action, context, kwargs.get("error"))
                else:
                    result = True
                duration = time.time() - start_time
                handler._update_metrics(duration, result)
                if not result:
                    logger.warning(f"Action handler {handler.name} failed for phase {phase.value}")
                    return False
            except Exception as e:
                logger.error(f"Error in action handler {handler.name} for phase {phase.value}: {e}")
                return False
        if async_tasks:
            results = await asyncio.gather(*async_tasks, return_exceptions=True)
            for idx, res in enumerate(results):
                if isinstance(res, Exception):
                    logger.error(f"Error in async action handler {handlers[idx].name}: {res}")
                    return False
                if not res:
                    logger.warning(f"Async action handler {handlers[idx].name} failed")
                    return False
        return True

    async def _execute_async_handler(self, handler: IActionHandler, phase: ActionHandlerPhase,
                                    action: Any, context: ActionContext, **kwargs) -> bool:
        """Execute a single async handler (MIGRAT parity)."""
        try:
            start_time = time.time()
            if phase == ActionHandlerPhase.BEFORE:
                result = await handler.before_execution(action, context, **kwargs)  # type: ignore[misc]
            elif phase == ActionHandlerPhase.AFTER:
                result = await handler.after_execution(action, context, kwargs.get("result"))  # type: ignore[misc]
            elif phase == ActionHandlerPhase.ERROR:
                result = await handler.on_error(action, context, kwargs.get("error"))  # type: ignore[misc]
            else:
                result = True
            duration = time.time() - start_time
            handler._update_metrics(duration, result)
            return bool(result)
        except Exception as e:
            logger.error(f"Error in async action handler {handler.name}: {e}")
            return False

    def get_all_handlers(self) -> dict[str, IActionHandler]:
        """Get all registered action handlers."""
        return self._handlers.copy()

    def get_handler_configs(self) -> dict[str, ActionHandlerConfig]:
        """Get all action handler configurations."""
        return self._configs.copy()

    def clear_cache(self):
        """Clear handler cache (MIGRAT parity)."""
        self._cache.clear()
        self._cache_ttl.clear()

    def clear(self):
        """Clear all registered action handlers."""
        self._handlers.clear()
        self._configs.clear()
        for phase in self._phase_handlers:
            self._phase_handlers[phase].clear()
        self.clear_cache()
# Global action handler registry instance
action_handler_registry = ActionHandlerRegistry()
__all__ = [
    "IActionHandler",
    "aActionHandlerBase",
    "ActionHandlerConfig",
    "ActionHandlerRegistry",
    "action_handler_registry",
    # concrete handlers
    "ValidationActionHandler",
    "SecurityActionHandler",
    "MonitoringActionHandler",
    "WorkflowActionHandler",
]
# Concrete handler implementations (for MIGRAT parity exports)
from .validation import ValidationActionHandler  # noqa: E402
from .security import SecurityActionHandler  # noqa: E402
from .monitoring import MonitoringActionHandler  # noqa: E402
from .workflow import WorkflowActionHandler  # noqa: E402
