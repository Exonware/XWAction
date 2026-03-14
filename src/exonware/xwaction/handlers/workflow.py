#exonware/xwaction/handlers/workflow.py
"""
Workflow Action Handler Implementation
Workflow orchestration and state management handler for XWAction.
This module fully reuses ecosystem libraries:
- xwdata: For workflow state management (XWData.from_native(), to_native())
  - XWData internally uses xwsystem serialization registry
- xwsystem: For logging (get_logger)
- No manual data manipulation - all data operations delegated to xwdata
"""

import time
from typing import Any
from .base import aActionHandlerBase
from ..defs import ActionHandlerPhase
from ..context import ActionContext
# Fully reuse xwdata for workflow state management
# XWData internally uses xwsystem serialization registry
from exonware.xwdata import XWData
# Fully reuse xwsystem for logging
from exonware.xwsystem import get_logger
logger = get_logger(__name__)


class WorkflowActionHandler(aActionHandlerBase):
    """
    Workflow Action Handler
    Handles workflow orchestration, state management, and rollback capabilities.
    Provides comprehensive workflow support for complex action sequences.
    Uses XWData for workflow state management.
    """

    def __init__(self):
        super().__init__(
            name="workflow",
            priority=30,  # Lower priority - workflow should run after core handlers
            async_enabled=True
        )
        # Use XWData for workflow state
        self._workflow_state = XWData.from_native({})
        self._rollback_stack = []
        self._workflow_registry = {}
    @property

    def supported_phases(self) -> set[ActionHandlerPhase]:
        """Workflow handler supports all phases."""
        return {ActionHandlerPhase.BEFORE, ActionHandlerPhase.AFTER, ActionHandlerPhase.ERROR, ActionHandlerPhase.FINALLY}

    def before_execution(self, action: Any, context: ActionContext, **kwargs) -> bool:
        """
        Initialize workflow state before execution.
        Args:
            action: The action being executed
            context: Execution context
            **kwargs: Action parameters
        Returns:
            True if workflow initialization successful, False otherwise
        """
        try:
            start_time = time.time()
            # Initialize workflow state using XWData
            workflow_id = context.trace_id
            workflow_state = {
                "action_name": action.api_name,
                "start_time": time.time(),
                "status": "running",
                "steps": [],
                "checkpoints": [],
                "rollback_points": []
            }
            # Store workflow state in XWData
            if isinstance(self._workflow_state, XWData):
                self._workflow_state[workflow_id] = workflow_state
            else:
                self._workflow_state[workflow_id] = workflow_state
            # Add initial checkpoint
            self._add_checkpoint(workflow_id, "start", kwargs)
            # Check if action is part of a workflow
            if hasattr(action, 'workflow_steps') and action.workflow_steps:
                self._setup_workflow(action, context, kwargs)
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            logger.debug(f"Workflow initialized for action {action.api_name}")
            return True
        except Exception as e:
            logger.error(f"Workflow handler error in before_execution: {e}")
            return False

    def after_execution(self, action: Any, context: ActionContext, result: Any, **kwargs) -> bool:
        """
        Update workflow state after successful execution.
        Args:
            action: The action that was executed
            context: Execution context
            result: The execution result
            **kwargs: Additional parameters
        Returns:
            True if workflow update successful, False otherwise
        """
        try:
            start_time = time.time()
            # Update workflow state using XWData
            workflow_id = context.trace_id
            if isinstance(self._workflow_state, XWData):
                if workflow_id in self._workflow_state:
                    workflow = self._workflow_state[workflow_id]
                    if isinstance(workflow, dict):
                        workflow["status"] = "completed"
                        workflow["end_time"] = time.time()
                        workflow["result"] = result
                        # Add completion checkpoint
                        if "checkpoints" in workflow:
                            workflow["checkpoints"].append({
                                "timestamp": time.time(),
                                "type": "completion",
                                "data": {"result": result}
                            })
            else:
                if workflow_id in self._workflow_state:
                    workflow = self._workflow_state[workflow_id]
                    workflow["status"] = "completed"
                    workflow["end_time"] = time.time()
                    workflow["result"] = result
                    # Add completion checkpoint
                    self._add_checkpoint(workflow_id, "completion", {"result": result})
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            logger.debug(f"Workflow completed for action {action.api_name}")
            return True
        except Exception as e:
            logger.error(f"Workflow handler error in after_execution: {e}")
            return False

    def on_error(self, action: Any, context: ActionContext, error: Exception, **kwargs) -> bool:
        """
        Handle workflow errors and rollback if needed.
        Args:
            action: The action that failed
            context: Execution context
            error: The exception that occurred
            **kwargs: Additional parameters
        Returns:
            True if error handling successful, False otherwise
        """
        try:
            start_time = time.time()
            # Update workflow state
            workflow_id = context.trace_id
            if isinstance(self._workflow_state, XWData):
                if workflow_id in self._workflow_state:
                    workflow = self._workflow_state[workflow_id]
                    if isinstance(workflow, dict):
                        workflow["status"] = "failed"
                        workflow["end_time"] = time.time()
                        workflow["error"] = str(error)
                        # Add error checkpoint
                        if "checkpoints" in workflow:
                            workflow["checkpoints"].append({
                                "timestamp": time.time(),
                                "type": "error",
                                "data": {"error": str(error)}
                            })
            else:
                if workflow_id in self._workflow_state:
                    workflow = self._workflow_state[workflow_id]
                    workflow["status"] = "failed"
                    workflow["end_time"] = time.time()
                    workflow["error"] = str(error)
                    # Add error checkpoint
                    self._add_checkpoint(workflow_id, "error", {"error": str(error)})
            # Check if rollback is needed
            if hasattr(action, 'rollback') and action.rollback:
                self._perform_rollback(action, context, error)
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            logger.debug(f"Workflow error handled for action {action.api_name}")
            return True
        except Exception as e:
            logger.error(f"Workflow handler error in on_error: {e}")
            return False

    def _add_checkpoint(self, workflow_id: str, checkpoint_type: str, data: dict[str, Any]):
        """
        Add checkpoint using XWData.
        Fully reuses XWData for checkpoint storage which provides:
        - Format-agnostic data storage
        - Path-based access for nested checkpoints
        - Query capabilities for checkpoint retrieval
        """
        try:
            checkpoint = {
                "timestamp": time.time(),
                "type": checkpoint_type,
                "data": data
            }
            # Use XWData for checkpoint storage
            if isinstance(self._workflow_state, XWData):
                checkpoints_path = f"{workflow_id}/checkpoints"
                if checkpoints_path in self._workflow_state:
                    checkpoints = self._workflow_state[checkpoints_path]
                    if isinstance(checkpoints, list):
                        checkpoints.append(checkpoint)
                    else:
                        self._workflow_state[checkpoints_path] = [checkpoint]
                else:
                    self._workflow_state[checkpoints_path] = [checkpoint]
            else:
                if workflow_id in self._workflow_state:
                    workflow = self._workflow_state[workflow_id]
                    if "checkpoints" in workflow:
                        workflow["checkpoints"].append(checkpoint)
                    else:
                        workflow["checkpoints"] = [checkpoint]
        except Exception as e:
            logger.error(f"Checkpoint addition failed: {e}")

    def _setup_workflow(self, action: Any, context: ActionContext, kwargs: dict[str, Any]):
        """Setup workflow configuration."""
        try:
            workflow_id = context.trace_id
            # Register workflow
            self._workflow_registry[workflow_id] = {
                "action": action,
                "context": context
            }
            # Setup rollback points if rollback is enabled
            if hasattr(action, 'rollback') and action.rollback:
                self._setup_rollback_points(workflow_id, action)
            logger.debug(f"Workflow setup completed for {action.api_name}")
        except Exception as e:
            logger.error(f"Workflow setup failed: {e}")

    def _perform_rollback(self, action: Any, context: ActionContext, error: Exception):
        """Perform workflow rollback."""
        try:
            workflow_id = context.trace_id
            # Get rollback points from XWData
            if isinstance(self._workflow_state, XWData):
                rollback_points_path = f"{workflow_id}/rollback_points"
                if rollback_points_path in self._workflow_state:
                    rollback_points = self._workflow_state[rollback_points_path]
                    if isinstance(rollback_points, list):
                        # Execute rollback in reverse order
                        for point in reversed(rollback_points):
                            self._execute_rollback_point(point, context)
            else:
                if workflow_id in self._workflow_state:
                    workflow = self._workflow_state[workflow_id]
                    rollback_points = workflow.get("rollback_points", [])
                    # Execute rollback in reverse order
                    for point in reversed(rollback_points):
                        self._execute_rollback_point(point, context)
            logger.info(f"Workflow rollback completed for {action.api_name}")
        except Exception as e:
            logger.error(f"Workflow rollback failed: {e}")

    def _setup_rollback_points(self, workflow_id: str, action: Any):
        """Setup rollback points for workflow."""
        try:
            # Store rollback points in XWData
            rollback_points = []
            if isinstance(self._workflow_state, XWData):
                self._workflow_state[f"{workflow_id}/rollback_points"] = rollback_points
            else:
                if workflow_id in self._workflow_state:
                    self._workflow_state[workflow_id]["rollback_points"] = rollback_points
            logger.debug(f"Rollback points setup for workflow {workflow_id}")
        except Exception as e:
            logger.error(f"Rollback points setup failed: {e}")

    def _execute_rollback_point(self, rollback_point: dict[str, Any], context: ActionContext):
        """Execute a rollback point."""
        try:
            rollback_type = rollback_point.get("type")
            rollback_data = rollback_point.get("data", {})
            if rollback_type == "data_restore":
                self._restore_data(rollback_data, context)
            elif rollback_type == "state_restore":
                self._restore_state(rollback_data, context)
            elif rollback_type == "compensation":
                self._execute_compensation(rollback_data, context)
            logger.debug(f"Rollback point executed: {rollback_type}")
        except Exception as e:
            logger.error(f"Rollback point execution failed: {e}")

    def _restore_data(self, data: dict[str, Any], context: ActionContext):
        """Restore data from checkpoint."""
        logger.debug(f"Data restore requested for {context.trace_id}")

    def _restore_state(self, state: dict[str, Any], context: ActionContext):
        """Restore state from checkpoint."""
        logger.debug(f"State restore requested for {context.trace_id}")

    def _execute_compensation(self, compensation: dict[str, Any], context: ActionContext):
        """Execute compensation action."""
        logger.debug(f"Compensation executed for {context.trace_id}")

    def setup(self, config: dict[str, Any]) -> bool:
        """Setup workflow handler."""
        try:
            # Clear state
            if isinstance(self._workflow_state, XWData):
                self._workflow_state = XWData.from_native({})
            else:
                self._workflow_state.clear()
            self._rollback_stack.clear()
            self._workflow_registry.clear()
            logger.debug("Workflow action handler setup completed")
            return True
        except Exception as e:
            logger.error(f"Failed to setup workflow handler: {e}")
            return False

    def teardown(self) -> bool:
        """Teardown workflow handler."""
        if XWData is not None and isinstance(self._workflow_state, XWData):
            self._workflow_state = XWData.from_native({})
        if isinstance(self._workflow_state, XWData):
            self._workflow_state = XWData.from_native({})
        else:
            self._workflow_state.clear()
        self._rollback_stack.clear()
        self._workflow_registry.clear()
        logger.debug("Workflow action handler teardown completed")
        return True

    def get_metrics(self) -> dict[str, Any]:
        """Get workflow handler metrics."""
        metrics = super().get_metrics()
        # Calculate workflow statistics
        if isinstance(self._workflow_state, XWData):
            # Fully reuse XWData.to_native() for serialization
            # XWData provides format-agnostic conversion to native Python types
            workflow_dict = self._workflow_state.to_native()
            active_workflows = len(workflow_dict) if isinstance(workflow_dict, dict) else 0
            completed_workflows = 0
            failed_workflows = 0
            if isinstance(workflow_dict, dict):
                for workflow in workflow_dict.values():
                    if isinstance(workflow, dict):
                        status = workflow.get("status")
                        if status == "completed":
                            completed_workflows += 1
                        elif status == "failed":
                            failed_workflows += 1
        else:
            active_workflows = len(self._workflow_state)
            completed_workflows = sum(1 for w in self._workflow_state.values() if isinstance(w, dict) and w.get("status") == "completed")
            failed_workflows = sum(1 for w in self._workflow_state.values() if isinstance(w, dict) and w.get("status") == "failed")
        metrics.update({
            "handler_type": "workflow",
            "active_workflows": active_workflows,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "total_workflows": len(self._workflow_registry),
            "success_rate": completed_workflows / (completed_workflows + failed_workflows) if (completed_workflows + failed_workflows) > 0 else 0.0
        })
        return metrics
