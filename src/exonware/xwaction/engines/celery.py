#exonware/xwaction/engines/celery.py
"""
Celery Action Engine Implementation
Background task execution engine for XWAction.
"""

import time
import inspect
import asyncio  # <--- Required for worker execution
from typing import Any, Optional
from .base import AActionEngineBase
from .defs import ActionEngineType
from ..context import ActionContext, ActionResult
from ..defs import ActionProfile
# Fully reuse xwdata for serialization
from exonware.xwdata import XWData
from exonware.xwsystem import get_logger
from celery import Celery
logger = get_logger(__name__)


class CeleryActionEngine(AActionEngineBase):
    """
    Celery Action Engine
    Executes actions as background tasks using Celery.
    This engine is ideal for long-running, asynchronous operations.
    Uses XWData for task serialization.
    """

    def __init__(self):
        super().__init__(
            name="celery",
            engine_type=ActionEngineType.EXECUTION,
            priority=60
        )
        self._app = None
        self._registered_tasks = {}
        self._task_queue = "default"
        self._task_routing = {}

    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """Celery engine can execute task and workflow profiles."""
        return action_profile in [
            ActionProfile.TASK, 
            ActionProfile.WORKFLOW, 
            ActionProfile.COMMAND
        ]

    def execute(self, action: Any, context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """
        Execute action as Celery background task.
        """
        start_time = time.time()
        try:
            if not self._app:
                logger.warning("Celery app not initialized, falling back to native execution")
                return self._fallback_execution(action, context, instance, **kwargs)
            # Submit the task
            task_result = self._submit_task(action, context, instance, **kwargs)
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            return ActionResult(
                success=True,
                data=task_result,
                duration=duration,
                metadata={
                    "engine": "celery",
                    "task_id": getattr(task_result, 'id', None) if task_result else None,
                    "task_status": getattr(task_result, 'status', None) if task_result else None,
                    "queue": self._task_queue
                }
            )
        except Exception as e:
            duration = time.time() - start_time
            self._update_metrics(duration, False)
            logger.error(f"Celery engine execution failed: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={
                    "engine": "celery",
                    "error_type": type(e).__name__
                }
            )

    def _submit_task(self, action: Any, context: ActionContext, 
                    instance: Any, **kwargs) -> Any:
        """Submit action as Celery task."""
        try:
            # 1. 🛡️ Filter non-serializable arguments using Base Class Helper
            # This prevents crashing the serializer with DB sessions/Requests
            serializable_kwargs = {
                k: v for k, v in kwargs.items()
                if self._is_pydantic_compatible(type(v))
            }
            # Serialize context and SAFE kwargs
            task_data = {
                "action_name": action.api_name,
                "context": context.to_dict(),
                "kwargs": serializable_kwargs
            }
            if XWData:
                serialized_data = XWData.from_native(task_data)
                task_data = serialized_data.to_native()
            if action.api_name not in self._registered_tasks:
                self._register_task(action)
            task_func = self._registered_tasks[action.api_name]
            task_result = task_func.delay(task_data)
            return task_result
        except Exception as e:
            logger.error(f"Failed to submit Celery task: {e}")
            return None

    def _register_task(self, action: Any):
        """Register action as Celery task."""
        try:
            # Create task function
            @self._app.task(name=action.api_name, queue=self._task_queue)
            def task_function(task_data: dict[str, Any]):
                # Deserialize using XWData
                if XWData:
                    data = XWData.from_native(task_data)
                    context_dict = data["context"]
                    kwargs = data["kwargs"]
                else:
                    context_dict = task_data["context"]
                    kwargs = task_data["kwargs"]
                # Recreate context (unused in execution but useful for logging/tracing if needed)
                # context = ActionContext(...)
                # 2. ⚡ Unified Execution Strategy
                # We use asyncio.run() to create an event loop for this worker thread.
                # We pass the execution to the Base class async helper.
                # This handles:
                #   - Async Actions (awaited)
                #   - Sync Actions (run in threadpool via asyncio.to_thread)
                #   - Bound Methods (self injection handled correctly)
                return asyncio.run(
                    self._execute_function_async(action, None, **kwargs)
                )
            self._registered_tasks[action.api_name] = task_function
            logger.info(f"Registered action {action.api_name} as Celery task")
            return True
        except Exception as e:
            logger.error(f"Failed to register Celery task: {e}")
            return False

    def setup(self, config: dict[str, Any]) -> bool:
        """Setup Celery engine."""
        try:
            if "app" in config:
                self._app = config["app"]
            elif "broker_url" in config:
                self._app = Celery(
                    "xwaction",
                    broker=config["broker_url"],
                    backend=config.get("backend_url")
                )
            self._task_queue = config.get("task_queue", "default")
            logger.debug("Celery action engine setup completed")
            return True
        except Exception as e:
            logger.error(f"Failed to setup Celery engine: {e}")
            return False
