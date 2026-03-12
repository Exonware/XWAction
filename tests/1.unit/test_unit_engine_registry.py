"""
#exonware/xwaction/tests/1.unit/test_unit_engine_registry.py
Unit tests for ActionEngineRegistry selection logic.
"""

from __future__ import annotations
import pytest
from exonware.xwaction import ActionProfile
from exonware.xwaction.engines import AActionEngineBase, ActionEngineType, action_engine_registry
pytestmark = pytest.mark.xwaction_unit


class _Engine(AActionEngineBase):

    def __init__(self, name: str, priority: int, allow: set[ActionProfile]):
        super().__init__(name=name, engine_type=ActionEngineType.EXECUTION, priority=priority)
        self._allow = allow

    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        return action_profile in self._allow

    def execute(self, action, context, instance, **kwargs):
        raise RuntimeError("not used in unit test")


def test_engine_registry_selects_highest_priority_that_can_execute():
    low = _Engine("low", priority=1, allow={ActionProfile.QUERY, ActionProfile.ACTION})
    high = _Engine("high", priority=100, allow={ActionProfile.ACTION})
    action_engine_registry.register(low)
    action_engine_registry.register(high)
    selected = action_engine_registry.select_engine(ActionProfile.ACTION)
    assert selected is not None
    assert selected.name == "high"
    selected_q = action_engine_registry.select_engine(ActionProfile.QUERY)
    assert selected_q is not None
    assert selected_q.name == "low"
