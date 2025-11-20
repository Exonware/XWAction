#!/usr/bin/env python3
"""
🎯 xAction Engine Interface
Defines the contract for all action engine implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Type
from enum import Enum
from dataclasses import dataclass

from ..abc import ActionContext, ActionResult
from ..core.profiles import ActionProfile


class ActionEngineType(Enum):
    """Types of action engines for different execution contexts."""
    EXECUTION = "execution"      # WHERE to run (fastapi, celery, prefect, native)
    STORAGE = "storage"          # WHERE to persist (redis, postgres, mongodb, s3)
    COMMUNICATION = "communication"  # HOW to communicate (http, grpc, websocket, kafka)
    PROCESSING = "processing"    # HOW to process (ray, dask, spark, gpu)


@dataclass
class ActionEngineConfig:
    """Configuration for an action engine."""
    name: str
    engine_type: ActionEngineType
    priority: int = 0  # Higher priority engines are used first
    enabled: bool = True
    config: Dict[str, Any] = None


class iActionEngine(ABC):
    """
    🌟 Action Engine Interface
    
    Defines the contract that all action engines must implement.
    Action engines handle the actual execution of actions in different contexts.
    """
    
    @property
    @abstractmethod
    def engine_type(self) -> ActionEngineType:
        """Get the type of this action engine."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this action engine."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Get the priority of this action engine (higher = used first)."""
        pass
    
    @abstractmethod
    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """
        Check if this action engine can execute the given action.
        
        Args:
            action_profile: The action profile to check
            **kwargs: Additional context
            
        Returns:
            True if this action engine can handle the action
        """
        pass
    
    @abstractmethod
    def execute(self, action: 'xAction', context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """
        Execute an action using this action engine.
        
        Args:
            action: The action to execute
            context: Execution context
            instance: The entity instance (self in decorated method)
            **kwargs: Action parameters
            
        Returns:
            ActionResult with execution results
        """
        pass
    
    @abstractmethod
    def setup(self, config: Dict[str, Any]) -> bool:
        """
        Setup the action engine with configuration.
        
        Args:
            config: Action engine-specific configuration
            
        Returns:
            True if setup was successful
        """
        pass
    
    @abstractmethod
    def teardown(self) -> bool:
        """
        Teardown the action engine.
        
        Returns:
            True if teardown was successful
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from this action engine.
        
        Returns:
            Dictionary of metrics
        """
        pass


class aActionEngineBase(iActionEngine):
    """
    🌟 Abstract Action Engine Base
    
    Provides common functionality for action engine implementations.
    """
    
    def __init__(self, name: str, engine_type: ActionEngineType, priority: int = 0):
        self._name = name
        self._engine_type = engine_type
        self._priority = priority
        self._metrics = {
            "executions": 0,
            "errors": 0,
            "total_duration": 0.0,
            "setup_time": 0.0
        }
        self._enabled = True
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def engine_type(self) -> ActionEngineType:
        return self._engine_type
    
    @property
    def priority(self) -> int:
        return self._priority
    
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


class ActionEngineRegistry:
    """
    🌟 Action Engine Registry
    
    Manages registration, selection, and configuration of action engines.
    """
    
    def __init__(self):
        self._engines: Dict[str, iActionEngine] = {}
        self._configs: Dict[str, ActionEngineConfig] = {}
        self._engine_types: Dict[ActionEngineType, List[iActionEngine]] = {
            engine_type: [] for engine_type in ActionEngineType
        }
    
    def register(self, engine: iActionEngine, config: Optional[ActionEngineConfig] = None):
        """
        Register an action engine.
        
        Args:
            engine: The action engine to register
            config: Optional configuration for the engine
        """
        if config is None:
            config = ActionEngineConfig(
                name=engine.name,
                engine_type=engine.engine_type,
                priority=engine.priority
            )
        
        self._engines[engine.name] = engine
        self._configs[engine.name] = config
        
        # Add to type-specific list
        engine_type = engine.engine_type
        self._engine_types[engine_type].append(engine)
        
        # Sort by priority (highest first)
        self._engine_types[engine_type].sort(key=lambda e: e.priority, reverse=True)
    
    def get_engine(self, name: str) -> Optional[iActionEngine]:
        """Get an action engine by name."""
        return self._engines.get(name)
    
    def get_engines_by_type(self, engine_type: ActionEngineType) -> List[iActionEngine]:
        """Get all action engines of a specific type."""
        return self._engine_types.get(engine_type, []).copy()
    
    def select_engine(self, action_profile: ActionProfile, 
                     engine_type: ActionEngineType = ActionEngineType.EXECUTION,
                     **kwargs) -> Optional[iActionEngine]:
        """
        Select the best action engine for an action profile.
        
        Args:
            action_profile: The action profile
            engine_type: The type of engine needed
            **kwargs: Additional selection criteria
            
        Returns:
            The best matching action engine, or None
        """
        engines = self.get_engines_by_type(engine_type)
        
        for engine in engines:
            if engine.can_execute(action_profile, **kwargs):
                return engine
        
        return None
    
    def get_all_engines(self) -> Dict[str, iActionEngine]:
        """Get all registered action engines."""
        return self._engines.copy()
    
    def get_engine_configs(self) -> Dict[str, ActionEngineConfig]:
        """Get all action engine configurations."""
        return self._configs.copy()
    
    def enable_engine(self, name: str):
        """Enable an action engine."""
        if name in self._configs:
            self._configs[name].enabled = True
    
    def disable_engine(self, name: str):
        """Disable an action engine."""
        if name in self._configs:
            self._configs[name].enabled = False
    
    def clear(self):
        """Clear all registered action engines."""
        self._engines.clear()
        self._configs.clear()
        for engine_type in self._engine_types:
            self._engine_types[engine_type].clear()


# Global action engine registry instance
action_engine_registry = ActionEngineRegistry()
