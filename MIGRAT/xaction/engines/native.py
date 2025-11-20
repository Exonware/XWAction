#!/usr/bin/env python3
"""
🎯 Native Action Engine Implementation
In-process execution engine for xAction.
"""

import time
import inspect
from typing import Any, Dict, Optional, Union, Callable

from .abc import aActionEngineBase, ActionEngineType
from ..abc import ActionContext, ActionResult
from ..core.profiles import ActionProfile
from src.xlib.xsystem import get_logger

logger = get_logger(__name__)


class NativeActionEngine(aActionEngineBase):
    """
    🌟 Native Action Engine
    
    Executes actions in the current process with minimal overhead.
    This is the default engine for simple, synchronous operations.
    """
    
    def __init__(self):
        super().__init__(
            name="native",
            engine_type=ActionEngineType.EXECUTION,
            priority=100  # Highest priority for native execution
        )
    
    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """Native engine can execute all action profiles."""
        return True  # Native engine can handle everything
    
    def execute(self, action: Union['xAction', Callable], context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """
        Execute action in the current process.
        
        Args:
            action: The action to execute (xAction object or decorated function)
            context: Execution context
            instance: The entity instance (self in decorated method)
            **kwargs: Action parameters
            
        Returns:
            ActionResult with execution results
        """
        start_time = time.time()
        
        try:
            # Handle both xAction objects and decorated functions
            if hasattr(action, 'func'):
                # It's an xAction object
                func = action.func
            elif callable(action):
                # It's a decorated function
                func = action
            else:
                raise ValueError(f"Invalid action type: {type(action)}")
            
            # Execute the function with proper parameters
            if instance is not None:
                result = func(instance, **kwargs)
            else:
                result = func(**kwargs)
            
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            
            return ActionResult(
                success=True,
                data=result,
                duration=duration,
                metadata={
                    "engine": "native",
                    "execution_type": "synchronous",
                    "instance_type": type(instance).__name__ if instance else None
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self._update_metrics(duration, False)
            
            logger.error(f"Native engine execution failed: {e}")
            
            return ActionResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={
                    "engine": "native",
                    "execution_type": "synchronous",
                    "error_type": type(e).__name__
                }
            )
    
    def setup(self, config: Dict[str, Any]) -> bool:
        """Setup native engine (no special setup needed)."""
        logger.debug("Native action engine setup completed")
        return True
    
    def teardown(self) -> bool:
        """Teardown native engine (no cleanup needed)."""
        logger.debug("Native action engine teardown completed")
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get native engine metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "engine_type": "native",
            "execution_mode": "synchronous"
        })
        return metrics
