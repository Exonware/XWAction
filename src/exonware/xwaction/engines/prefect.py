#exonware/xwaction/engines/prefect.py
"""
Prefect Action Engine Implementation
Workflow orchestration engine for XWAction.
"""

import time
import inspect
from typing import Any, Optional
from .base import AActionEngineBase
from .defs import ActionEngineType
from ..context import ActionContext, ActionResult
from ..defs import ActionProfile
# Fully reuse xwdata for serialization
# XWData internally uses xwsystem serialization registry
from exonware.xwdata import XWData
# Fully reuse xwsystem for logging
from exonware.xwsystem import get_logger
from prefect import flow, get_client
logger = get_logger(__name__)


class PrefectActionEngine(AActionEngineBase):
    """
    Prefect Action Engine
    Executes actions as Prefect flows with workflow orchestration.
    This engine is ideal for complex workflows with dependencies and monitoring.
    Uses XWData for workflow state management.
    """

    def __init__(self):
        super().__init__(
            name="prefect",
            engine_type=ActionEngineType.EXECUTION,
            priority=40  # Lower priority for complex workflows
        )
        self._client = None
        self._flows = {}
        self._deployments = {}
        self._work_queue = "default"
        self._flow_retries = 3

    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """Prefect engine can execute workflow and task profiles."""
        return action_profile in [ActionProfile.WORKFLOW, ActionProfile.TASK, ActionProfile.COMMAND]

    def execute(self, action: Any, context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """
        Execute action as Prefect flow.
        Args:
            action: The action to execute
            context: Execution context
            instance: The entity instance (self in decorated method)
            **kwargs: Action parameters
        Returns:
            ActionResult with flow execution results
        """
        start_time = time.time()
        try:
            # For Prefect, we create and run a flow
            if not self._client:
                logger.warning("Prefect client not initialized, falling back to native execution")
                return self._fallback_execution(action, context, instance, **kwargs)
            # Create and run the flow
            flow_run = self._create_and_run_flow(action, context, instance, **kwargs)
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            return ActionResult(
                success=True,
                data=flow_run,
                duration=duration,
                metadata={
                    "engine": "prefect",
                    "flow_run_id": getattr(flow_run, 'id', None) if flow_run else None,
                    "flow_name": action.api_name,
                    "work_queue": self._work_queue
                }
            )
        except Exception as e:
            duration = time.time() - start_time
            self._update_metrics(duration, False)
            logger.error(f"Prefect engine execution failed: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={
                    "engine": "prefect",
                    "error_type": type(e).__name__
                }
            )
    # Note: _fallback_execution is now provided by AActionEngineBase

    def _create_and_run_flow(self, action: Any, context: ActionContext, 
                            instance: Any, **kwargs) -> Any:
        """Create and run Prefect flow."""
        try:
            # Get or create flow
            if action.api_name not in self._flows:
                self._register_flow(action)
            # Get flow function
            flow_func = self._flows[action.api_name]
            # Fully reuse XWData for serialization
            # XWData provides format-agnostic serialization with automatic format detection
            # Serialize context and kwargs using XWData
            task_data = {
                "context": context.to_dict(),
                "kwargs": kwargs
            }
            if XWData:
                serialized_data = XWData.from_native(task_data)
                task_data = serialized_data.to_native()
            # Run flow
            flow_run = flow_func(**task_data)
            return flow_run
        except Exception as e:
            logger.error(f"Failed to create and run Prefect flow: {e}")
            return None

    def _register_flow(self, action: Any):
        """Register action as Prefect flow."""
        try:
            # Create flow function
            @flow(name=action.api_name, retries=self._flow_retries)
            def flow_function(task_data: dict[str, Any]):
                # Fully reuse XWData for deserialization
                # XWData.from_native() provides format-agnostic data loading
                # Deserialize using XWData
                if XWData:
                    data = XWData.from_native(task_data)
                    context_dict = data["context"]
                    kwargs = data["kwargs"]
                else:
                    context_dict = task_data["context"]
                    kwargs = task_data["kwargs"]
                # Recreate context
                context = ActionContext(
                    actor=context_dict.get("actor"),
                    source=context_dict.get("source"),
                    trace_id=context_dict.get("trace_id"),
                    metadata=context_dict.get("metadata", {})
                )
                # Execute action
                if action.func:
                    result = action.func(**kwargs)
                    return result
                return None
            self._flows[action.api_name] = flow_function
            logger.info(f"Registered action {action.api_name} as Prefect flow")
            return True
        except Exception as e:
            logger.error(f"Failed to register Prefect flow: {e}")
            return False

    def setup(self, config: dict[str, Any]) -> bool:
        """Setup Prefect engine."""
        try:
            # Initialize Prefect client if provided
            if "client" in config:
                self._client = config["client"]
            elif "api_url" in config:
                self._client = get_client(api_url=config["api_url"])
            else:
                self._client = get_client()
            # Configure work queue
            self._work_queue = config.get("work_queue", "default")
            self._flow_retries = config.get("flow_retries", 3)
            logger.debug("Prefect action engine setup completed")
            return True
        except Exception as e:
            logger.error(f"Failed to setup Prefect engine: {e}")
            return False
