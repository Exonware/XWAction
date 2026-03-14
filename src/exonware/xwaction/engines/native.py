#exonware/xwaction/engines/native.py
"""
Native Action Engine
In-process execution engine for actions.
"""

import time
from typing import Any
from ..context import ActionContext, ActionResult
from ..defs import ActionProfile
from .base import AActionEngineBase
from .defs import ActionEngineType
from exonware.xwsystem import get_logger
logger = get_logger(__name__)


class NativeActionEngine(AActionEngineBase):
    """
    Native Action Engine
    Executes actions in-process without external dependencies.
    """

    def __init__(self):
        super().__init__(
            name="native",
            engine_type=ActionEngineType.EXECUTION,
            priority=100  # High priority for native execution
        )

    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """Native engine can execute any action profile."""
        return True

    def execute(self, action: Any, context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """
        Execute an action natively.
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
            # Use base class method for consistent execution
            result_data = self._execute_function(action, instance, **kwargs)
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            return ActionResult.success(data=result_data, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self._update_metrics(duration, False)
            logger.error(f"Native execution failed: {e}")
            return ActionResult.failure(error=str(e), duration=duration)
