#!/usr/bin/env python3
"""
🎯 xAction Handler Interface
Defines the contract for all action handler implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Set
from enum import Enum
from dataclasses import dataclass
import time
import asyncio

from ..abc import ActionContext
from src.xlib.xsystem import get_logger

logger = get_logger(__name__)


class ActionHandlerPhase(Enum):
    """Execution phases for action handlers."""
    BEFORE = "before"      # Before action execution
    AFTER = "after"        # After successful execution
    ERROR = "error"        # After failed execution
    FINALLY = "finally"    # Always executed (cleanup)


@dataclass
class ActionHandlerConfig:
    """Configuration for an action handler."""
    name: str
    enabled: bool = True
    async_enabled: bool = False  # Whether handler supports async execution
    priority: int = 0  # Higher priority handlers run first
    cache_ttl: int = 0  # Cache TTL in seconds (0 = no caching)
    config: Dict[str, Any] = None


class iActionHandler(ABC):
    """
    🌟 Action Handler Interface
    
    Defines the contract that all action handlers must implement.
    Action handlers provide cross-cutting concerns like validation, security, monitoring, etc.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this action handler."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Get the priority of this action handler (higher = runs first)."""
        pass
    
    @property
    @abstractmethod
    def supported_phases(self) -> Set[ActionHandlerPhase]:
        """Get the phases this action handler supports."""
        pass
    
    @property
    @abstractmethod
    def async_enabled(self) -> bool:
        """Whether this action handler supports async execution."""
        pass
    
    @abstractmethod
    def before_execution(self, action: 'xAction', context: ActionContext, **kwargs) -> bool:
        """
        Execute before action execution.
        
        Args:
            action: The action being executed
            context: Execution context
            **kwargs: Action parameters
            
        Returns:
            True if execution should continue, False to abort
        """
        pass
    
    @abstractmethod
    def after_execution(self, action: 'xAction', context: ActionContext, result: Any) -> bool:
        """
        Execute after successful action execution.
        
        Args:
            action: The action that was executed
            context: Execution context
            result: The execution result
            
        Returns:
            True if successful, False if there was an issue
        """
        pass
    
    @abstractmethod
    def on_error(self, action: 'xAction', context: ActionContext, error: Exception) -> bool:
        """
        Execute when an error occurs during action execution.
        
        Args:
            action: The action that failed
            context: Execution context
            error: The exception that occurred
            
        Returns:
            True if error was handled, False otherwise
        """
        pass
    
    @abstractmethod
    def setup(self, config: Dict[str, Any]) -> bool:
        """
        Setup the action handler with configuration.
        
        Args:
            config: Action handler-specific configuration
            
        Returns:
            True if setup was successful
        """
        pass
    
    @abstractmethod
    def teardown(self) -> bool:
        """
        Teardown the action handler.
        
        Returns:
            True if teardown was successful
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from this action handler.
        
        Returns:
            Dictionary of metrics
        """
        pass


class aActionHandlerBase(iActionHandler):
    """
    🌟 Abstract Action Handler Base
    
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
    
    def setup(self, config: Dict[str, Any]) -> bool:
        """Default setup implementation."""
        return True
    
    def teardown(self) -> bool:
        """Default teardown implementation."""
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get base metrics."""
        return self._metrics.copy()
    
    def _update_metrics(self, duration: float, success: bool = True):
        """Update execution metrics."""
        self._metrics["executions"] += 1
        self._metrics["total_duration"] += duration
        if not success:
            self._metrics["errors"] += 1
    
    def _get_cache_key(self, action: 'xAction', context: ActionContext, **kwargs) -> str:
        """Generate cache key for handler execution."""
        return f"{self.name}:{action.api_name}:{context.trace_id}"


class ActionHandlerRegistry:
    """
    🌟 Action Handler Registry
    
    Manages registration, execution, and configuration of action handlers.
    """
    
    def __init__(self):
        self._handlers: Dict[str, iActionHandler] = {}
        self._configs: Dict[str, ActionHandlerConfig] = {}
        self._phase_handlers: Dict[ActionHandlerPhase, List[iActionHandler]] = {
            phase: [] for phase in ActionHandlerPhase
        }
        self._cache = {}
        self._cache_ttl = {}
    
    def register(self, handler_class: Type[iActionHandler], config: Optional[ActionHandlerConfig] = None):
        """
        Register an action handler class.
        
        Args:
            handler_class: The action handler class to register
            config: Optional configuration for the handler
        """
        # Create handler instance
        handler = handler_class()
        
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
    
    def get_handler(self, name: str) -> Optional[iActionHandler]:
        """Get an action handler by name."""
        return self._handlers.get(name)
    
    def get_handlers_for_phase(self, phase: ActionHandlerPhase) -> List[iActionHandler]:
        """Get all action handlers for a specific phase."""
        handlers = self._phase_handlers.get(phase, [])
        return [h for h in handlers if self._configs[h.name].enabled]
    
    def execute_phase(self, phase: ActionHandlerPhase, action: 'xAction', 
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
    
    async def execute_phase_async(self, phase: ActionHandlerPhase, action: 'xAction',
                               context: ActionContext, **kwargs) -> bool:
        """
        Execute all action handlers for a specific phase asynchronously.
        
        Args:
            phase: The phase to execute
            action: The action being processed
            context: Execution context
            **kwargs: Additional parameters
            
        Returns:
            True if all handlers succeeded, False otherwise
        """
        handlers = self.get_handlers_for_phase(phase)
        
        # Execute async handlers concurrently
        async_tasks = []
        sync_handlers = []
        
        for handler in handlers:
            if handler.async_enabled:
                task = self._execute_async_handler(handler, phase, action, context, **kwargs)
                async_tasks.append(task)
            else:
                sync_handlers.append(handler)
        
        # Execute sync handlers first
        for handler in sync_handlers:
            try:
                start_time = time.time()
                
                if phase == ActionHandlerPhase.BEFORE:
                    result = await asyncio.to_thread(handler.before_execution, action, context, **kwargs)
                elif phase == ActionHandlerPhase.AFTER:
                    result = await asyncio.to_thread(handler.after_execution, action, context, kwargs.get('result'), **kwargs)
                elif phase == ActionHandlerPhase.ERROR:
                    result = await asyncio.to_thread(handler.on_error, action, context, kwargs.get('error'), **kwargs)
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
        
        # Execute async handlers
        if async_tasks:
            results = await asyncio.gather(*async_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in async action handler {handlers[i].name}: {result}")
                    return False
                elif not result:
                    logger.warning(f"Async action handler {handlers[i].name} failed")
                    return False
        
        return True
    
    async def _execute_async_handler(self, handler: iActionHandler, phase: ActionHandlerPhase,
                                  action: 'xAction', context: ActionContext, **kwargs):
        """Execute a single async handler."""
        try:
            start_time = time.time()
            
            if phase == ActionHandlerPhase.BEFORE:
                result = await handler.before_execution(action, context, **kwargs)
            elif phase == ActionHandlerPhase.AFTER:
                result = await handler.after_execution(action, context, kwargs.get('result'), **kwargs)
            elif phase == ActionHandlerPhase.ERROR:
                result = await handler.on_error(action, context, kwargs.get('error'), **kwargs)
            else:  # FINALLY
                result = True
            
            duration = time.time() - start_time
            handler._update_metrics(duration, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in async action handler {handler.name}: {e}")
            return False
    
    def get_all_handlers(self) -> Dict[str, iActionHandler]:
        """Get all registered action handlers."""
        return self._handlers.copy()
    
    def get_handler_configs(self) -> Dict[str, ActionHandlerConfig]:
        """Get all action handler configurations."""
        return self._configs.copy()
    
    def clear_cache(self):
        """Clear handler cache."""
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
