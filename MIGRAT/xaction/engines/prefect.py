#!/usr/bin/env python3
"""
🎯 Prefect Action Engine Implementation
Workflow orchestration engine for xAction.
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


class PrefectActionEngine(aActionEngineBase):
    """
    🌟 Prefect Action Engine
    
    Executes actions as Prefect flows with workflow orchestration.
    This engine is ideal for complex workflows with dependencies and monitoring.
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
    
    def execute(self, action: 'xAction', context: ActionContext, 
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
                    "flow_run_id": flow_run.id if flow_run else None,
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
    
    def _fallback_execution(self, action: 'xAction', context: ActionContext, 
                           instance: Any, **kwargs) -> ActionResult:
        """Fallback to native execution when Prefect is not available."""
        from .native import NativeActionEngine
        native_engine = NativeActionEngine()
        return native_engine.execute(action, context, instance, **kwargs)
    
    def _create_and_run_flow(self, action: 'xAction', context: ActionContext, 
                            instance: Any, **kwargs) -> Any:
        """Create and run a Prefect flow for the action."""
        from prefect import flow, task
        
        # Create task function if not already registered
        task_name = f"xaction_{action.api_name}"
        
        if task_name not in self._flows:
            self._register_flow(action, task_name)
        
        # Create flow function
        @flow(name=f"xaction_flow_{action.api_name}")
        def action_flow():
            # Execute the registered task
            return self._flows[task_name](action, context, instance, **kwargs)
        
        # Run the flow
        flow_run = action_flow()
        
        return flow_run
    
    def _register_flow(self, action: 'xAction', task_name: str):
        """Register an action as a Prefect task."""
        from prefect import task
        
        @task(name=task_name, retries=self._flow_retries)
        def action_task(action: 'xAction', context: ActionContext, 
                       instance: Any, **kwargs) -> Any:
            try:
                # Execute the action
                result = self._execute_action(action, instance, **kwargs)
                
                # Log execution
                logger.info(f"Prefect task {task_name} completed successfully")
                
                return result
                
            except Exception as e:
                logger.error(f"Prefect task {task_name} failed: {e}")
                raise
        
        self._flows[task_name] = action_task
        logger.info(f"Registered Prefect task: {task_name}")
    
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
    
    def create_deployment(self, action: 'xAction', deployment_name: str = None):
        """
        Create a Prefect deployment for an action.
        
        Args:
            action: The action to deploy
            deployment_name: Optional deployment name
        """
        if not self._client:
            logger.warning("Prefect client not available, cannot create deployment")
            return
        
        try:
            from prefect.deployments import Deployment
            from prefect.server.schemas.schedules import CronSchedule
            
            # Create deployment
            deployment = Deployment.build_from_flow(
                flow=self._flows[f"xaction_{action.api_name}"],
                name=deployment_name or f"xaction_deployment_{action.api_name}",
                work_queue_name=self._work_queue,
                schedule=CronSchedule(cron="0 0 * * *")  # Daily at midnight
            )
            
            # Apply deployment
            deployment_id = deployment.apply()
            
            self._deployments[action.api_name] = deployment_id
            logger.info(f"Created Prefect deployment: {deployment_name}")
            
        except Exception as e:
            logger.error(f"Failed to create Prefect deployment: {e}")
    
    def setup(self, config: Dict[str, Any]) -> bool:
        """Setup Prefect engine."""
        try:
            # Try to import Prefect
            from prefect.client import get_client
            
            # Configure Prefect
            api_url = config.get("api_url", "http://localhost:4200/api")
            work_queue = config.get("work_queue", "default")
            flow_retries = config.get("flow_retries", 3)
            
            # Set configuration
            self._work_queue = work_queue
            self._flow_retries = flow_retries
            
            # Initialize client
            self._client = get_client()
            
            logger.debug("Prefect action engine setup completed")
            return True
            
        except ImportError:
            logger.warning("Prefect not available, engine will use fallback execution")
            return False
        except Exception as e:
            logger.error(f"Failed to setup Prefect engine: {e}")
            return False
    
    def teardown(self) -> bool:
        """Teardown Prefect engine."""
        self._client = None
        self._flows.clear()
        self._deployments.clear()
        logger.debug("Prefect action engine teardown completed")
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get Prefect engine metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "engine_type": "prefect",
            "registered_flows": len(self._flows),
            "deployments": len(self._deployments),
            "work_queue": self._work_queue,
            "flow_retries": self._flow_retries
        })
        return metrics
