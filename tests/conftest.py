"""
#exonware/xwaction/tests/conftest.py
Shared pytest fixtures for xwaction tests.
"""

from __future__ import annotations
import pytest
@pytest.fixture(autouse=True)


@pytest.fixture(autouse=True)
def _reset_xwaction_globals():
    """
    Ensure test isolation.
    xwaction uses module-level singletons (registry, handler registry, engine registry,
    executor, validator). We reset their in-memory state between tests.
    """
    from exonware.xwaction import ActionRegistry, action_engine_registry, action_handler_registry
    from exonware.xwaction.core import action_executor, action_validator
    ActionRegistry.clear()
    action_engine_registry.clear()
    action_handler_registry.clear()
    # Validator caches
    action_validator._validation_cache.clear()
    action_validator._contract_cache.clear()
    # Executor caches/metrics
    action_executor._cache.clear()
    action_executor._metrics = {
        "executions": 0,
        "errors": 0,
        "total_duration": 0.0,
        "cache_hits": 0,
        "cache_misses": 0,
    }
    yield
