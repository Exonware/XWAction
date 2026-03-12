#exonware/xwaction/handlers/base.py
"""
XWAction Handler Base Classes
Abstract base classes for action handler implementations.
"""

from abc import abstractmethod
from typing import Any
from .contracts import IActionHandler
from ..context import ActionContext
from ..defs import ActionHandlerPhase


class aActionHandlerBase(IActionHandler):
    """
    Abstract Action Handler Base
    Provides common functionality for action handler implementations.
    """

    def __init__(self, name: str, priority: int = 0, async_enabled: bool = False):
        self._name = name
        self._priority = priority
        self._async_enabled = async_enabled
        self._metrics = {
            "executions": 0,
            "errors": 0,
            "total_duration": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        self._enabled = True
        self._cache = {}
    @property

    def name(self) -> str:
        return self._name
    @property

    def priority(self) -> int:
        return self._priority
    @property

    def async_enabled(self) -> bool:
        return self._async_enabled
    @property
    @abstractmethod

    def supported_phases(self) -> set[ActionHandlerPhase]:
        """Get the phases this action handler supports."""
        pass
    @abstractmethod

    def before_execution(self, action: Any, context: ActionContext, **kwargs) -> bool:
        """Execute before action execution."""
        pass
    @abstractmethod

    def after_execution(self, action: Any, context: ActionContext, result: Any) -> bool:
        """Execute after successful action execution."""
        pass
    @abstractmethod

    def on_error(self, action: Any, context: ActionContext, error: Exception) -> bool:
        """Execute when an error occurs during action execution."""
        pass

    def setup(self, config: dict[str, Any]) -> bool:
        """Default setup implementation."""
        return True

    def teardown(self) -> bool:
        """Default teardown implementation."""
        return True

    def get_metrics(self) -> dict[str, Any]:
        """Get base metrics."""
        return self._metrics.copy()

    def _update_metrics(self, duration: float, success: bool = True):
        """Update execution metrics."""
        self._metrics["executions"] += 1
        self._metrics["total_duration"] += duration
        if not success:
            self._metrics["errors"] += 1

    def _get_cache_key(self, action: Any, context: ActionContext, **kwargs) -> str:
        """Generate cache key for handler execution (MIGRAT parity)."""
        return f"{self.name}:{getattr(action, 'api_name', 'unknown')}:{context.trace_id}"
