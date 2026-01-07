#exonware/xwaction/engines/__init__.py
"""Engine implementations for XWAction."""

from typing import Any, Optional

from .contracts import IActionEngine
from .defs import ActionEngineType, ActionEngineConfig
from .base import AActionEngineBase
from .native import NativeActionEngine
from .fastapi import FastAPIActionEngine
from .flask import FlaskActionEngine
from ..defs import ActionProfile

# Optional engine imports - these may have dependencies not installed
try:
    from .celery import CeleryActionEngine
    CELERY_ENGINE_AVAILABLE = True
except ImportError:
    CeleryActionEngine = None  # type: ignore
    CELERY_ENGINE_AVAILABLE = False

try:
    from .prefect import PrefectActionEngine
    PREFECT_ENGINE_AVAILABLE = True
except ImportError:
    PrefectActionEngine = None  # type: ignore
    PREFECT_ENGINE_AVAILABLE = False

from exonware.xwsystem import get_logger

logger = get_logger(__name__)


class ActionEngineRegistry:
    """
    Action Engine Registry
    
    Manages registration, selection, and configuration of action engines.
    """
    
    def __init__(self):
        self._engines: dict[str, IActionEngine] = {}
        self._configs: dict[str, ActionEngineConfig] = {}
        self._engine_types: dict[ActionEngineType, list[IActionEngine]] = {
            engine_type: [] for engine_type in ActionEngineType
        }
    
    def register(self, engine: IActionEngine, config: Optional[ActionEngineConfig] = None):
        """Register an action engine."""
        if config is None:
            config = ActionEngineConfig(
                name=engine.name,
                engine_type=engine.engine_type,
                priority=engine.priority
            )
        
        self._engines[engine.name] = engine
        self._configs[engine.name] = config

        # Add to type-specific list (MIGRAT parity)
        engine_type = engine.engine_type
        self._engine_types[engine_type].append(engine)
        self._engine_types[engine_type].sort(key=lambda e: e.priority, reverse=True)
    
    def get_engine(self, name: str) -> Optional[IActionEngine]:
        """Get an action engine by name."""
        return self._engines.get(name)
    
    def get_engines_by_type(self, engine_type: ActionEngineType) -> list[IActionEngine]:
        """Get all action engines of a specific type."""
        return self._engine_types.get(engine_type, []).copy()

    def select_engine(self, action_profile: ActionProfile,
                      engine_type: ActionEngineType = ActionEngineType.EXECUTION,
                      **kwargs) -> Optional[IActionEngine]:
        """
        Select the best action engine for an action profile (MIGRAT parity).
        """
        engines = self.get_engines_by_type(engine_type)
        for engine in engines:
            if engine.can_execute(action_profile, **kwargs):
                return engine
        return None

    def get_all_engines(self) -> dict[str, IActionEngine]:
        """Get all registered action engines."""
        return self._engines.copy()

    def get_engine_configs(self) -> dict[str, ActionEngineConfig]:
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

__all__ = [
    "IActionEngine",
    "AActionEngineBase",
    "ActionEngineType",
    "ActionEngineConfig",
    "ActionEngineRegistry",
    "action_engine_registry",
    "NativeActionEngine",
    "FastAPIActionEngine",
    "FlaskActionEngine",
    "CELERY_ENGINE_AVAILABLE",
    "PREFECT_ENGINE_AVAILABLE",
]

# Conditionally add optional engines to __all__
if CELERY_ENGINE_AVAILABLE:
    __all__.append("CeleryActionEngine")
if PREFECT_ENGINE_AVAILABLE:
    __all__.append("PrefectActionEngine")

