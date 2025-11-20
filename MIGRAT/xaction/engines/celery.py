#!/usr/bin/env python3
"""
🎯 Celery Action Engine Implementation
Background task execution engine for xAction.
"""

import time
import inspect
from typing import Any, Dict, Optional, List
from functools import wraps

from .abc import aActionEngineBase, ActionEngineType
from ..abc import ActionContext, ActionResult
from ..core.profiles import ActionProfile
from src.xlib.xsystem import get_logger

logger = get_logger(__name__)


class CeleryActionEngine(aActionEngineBase):
    """
    🌟 Celery Action Engine
    
    Executes actions as background tasks using Celery.
    This engine is ideal for long-running, asynchronous operations.
    """
    
    def __init__(self):
        super().__init__(
            name="celery",
            engine_type=ActionEngineType.EXECUTION,
            priority=60  # Medium priority for background tasks
        )
        self._app = None
        self._registered_tasks = {}
        self._task_queue = "default"
        self._task_routing = {}
    
    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """Celery engine can execute task and workflow profiles."""
        return action_profile in [ActionProfile.TASK, ActionProfile.WORKFLOW, ActionProfile.COMMAND]
    
    def execute(self, action: 'xAction', context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """
        Execute action as Celery background task.
        
        Args:
            action: The action to execute
            context: Execution context
            instance: The entity instance (self in decorated method)
            **kwargs: Action parameters
            
        Returns:
            ActionResult with task submission results
        """
        start_time = time.time()
        
        try:
            # For Celery, we submit the task and return immediately
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
                    "task_id": task_result.id if task_result else None,
                    "task_status": task_result.status if task_result else None,
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
    
    def _fallback_execution(self, action: 'xAction', context: ActionContext, 
                           instance: Any, **kwargs) -> ActionResult:
        """Fallback to native execution when Celery is not available."""
        from .native import NativeActionEngine
        native_engine = NativeActionEngine()
        return native_engine.execute(action, context, instance, **kwargs)
    
    def _submit_task(self, action: 'xAction', context: ActionContext, 
                     instance: Any, **kwargs) -> Any:
        """Submit the action as a Celery task."""
        # Create task function if not already registered
        task_name = f"xaction_{action.api_name}"
        
        if task_name not in self._registered_tasks:
            self._register_task(action, task_name)
        
        # Prepare task arguments
        task_args = {
            "action_name": action.api_name,
            "context": context.to_dict(),
            "instance_data": self._serialize_instance(instance),
            "kwargs": kwargs
        }
        
        # Submit task with routing
        routing_key = self._task_routing.get(action.api_name, self._task_queue)
        
        task = self._app.send_task(
            task_name,
            args=[task_args],
            queue=routing_key,
            task_id=context.trace_id
        )
        
        return task
    
    def _register_task(self, action: 'xAction', task_name: str):
        """Register an action as a Celery task."""
        if not self._app:
            return
        
        # Create the task function
        def task_function(task_data: Dict[str, Any]):
            try:
                # Extract data
                action_name = task_data["action_name"]
                context_data = task_data["context"]
                instance_data = task_data["instance_data"]
                kwargs = task_data["kwargs"]
                
                # Reconstruct context
                context = ActionContext.from_dict(context_data)
                
                # Reconstruct instance if needed
                instance = self._deserialize_instance(instance_data)
                
                # Execute the action
                result = self._execute_action(action, instance, **kwargs)
                
                return result
                
            except Exception as e:
                logger.error(f"Celery task execution failed: {e}")
                raise
        
        # Register with Celery
        task_function.__name__ = task_name
        task_function.__doc__ = action.description
        
        # Create Celery task
        celery_task = self._app.task(
            task_function,
            name=task_name,
            queue=self._task_queue,
            bind=True,
            max_retries=3,
            default_retry_delay=60
        )
        
        self._registered_tasks[task_name] = celery_task
        logger.info(f"Registered Celery task: {task_name}")
    
    def _execute_action(self, action: 'xAction', instance: Any, **kwargs) -> Any:
        """Execute the action function."""
        func = action.func
        
        # Prepare arguments
        args = []
        if instance is not None:
            args.append(instance)
        
        # Add action parameters
        args.extend(kwargs.values())
        
        # Execute the function
        return func(*args)
    
    def _serialize_instance(self, instance: Any) -> Dict[str, Any]:
        """Serialize instance for Celery task."""
        if instance is None:
            return None
        
        # Basic serialization - in practice, you'd want more sophisticated serialization
        return {
            "type": type(instance).__name__,
            "module": type(instance).__module__,
            "data": str(instance)  # Simplified - should use proper serialization
        }
    
    def _deserialize_instance(self, instance_data: Dict[str, Any]) -> Any:
        """Deserialize instance from Celery task."""
        if instance_data is None:
            return None
        
        # Basic deserialization - in practice, you'd want more sophisticated deserialization
        # For now, return None as we can't easily reconstruct complex objects
        return None
    
    def setup(self, config: Dict[str, Any]) -> bool:
        """Setup Celery engine."""
        try:
            # Try to import Celery
            from celery import Celery
            
            # Create Celery app
            broker_url = config.get("broker_url", "redis://localhost:6379/0")
            result_backend = config.get("result_backend", "redis://localhost:6379/0")
            
            self._app = Celery(
                "xaction",
                broker=broker_url,
                backend=result_backend
            )
            
            # Configure Celery
            self._app.conf.update(
                task_serializer="json",
                accept_content=["json"],
                result_serializer="json",
                timezone="UTC",
                enable_utc=True,
                task_track_started=True,
                task_time_limit=30 * 60,  # 30 minutes
                task_soft_time_limit=25 * 60,  # 25 minutes
            )
            
            # Set queue and routing
            self._task_queue = config.get("queue", "default")
            self._task_routing = config.get("routing", {})
            
            logger.debug("Celery action engine setup completed")
            return True
            
        except ImportError:
            logger.warning("Celery not available, engine will use fallback execution")
            return False
        except Exception as e:
            logger.error(f"Failed to setup Celery engine: {e}")
            return False
    
    def teardown(self) -> bool:
        """Teardown Celery engine."""
        self._app = None
        self._registered_tasks.clear()
        logger.debug("Celery action engine teardown completed")
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get Celery engine metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "engine_type": "celery",
            "registered_tasks": len(self._registered_tasks),
            "task_queue": self._task_queue,
            "task_routing": len(self._task_routing)
        })
        return metrics
