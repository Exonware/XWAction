"""
#exonware/xwaction/tests/1.unit/test_unit_handler_registry.py
Unit tests for ActionHandlerRegistry ordering + execution.
"""

from __future__ import annotations
import pytest
from exonware.xwaction import ActionHandlerPhase
from exonware.xwaction.context import ActionContext
from exonware.xwaction.handlers import aActionHandlerBase, action_handler_registry
pytestmark = pytest.mark.xwaction_unit


class _Handler(aActionHandlerBase):

    def __init__(self, name: str, priority: int, calls: list[str]):
        super().__init__(name=name, priority=priority, async_enabled=False)
        self._calls = calls
    @property

    def supported_phases(self):
        return {ActionHandlerPhase.BEFORE}

    def before_execution(self, action, context: ActionContext, **kwargs) -> bool:
        self._calls.append(self.name)
        return True

    def after_execution(self, action, context: ActionContext, result):
        return True

    def on_error(self, action, context: ActionContext, error: Exception):
        return True


def test_handler_registry_executes_in_priority_order():
    calls: list[str] = []
    h1 = _Handler("h1", priority=10, calls=calls)
    h2 = _Handler("h2", priority=99, calls=calls)
    action_handler_registry.register(h1)
    action_handler_registry.register(h2)
    ok = action_handler_registry.execute_phase(
        ActionHandlerPhase.BEFORE, action=object(), context=ActionContext(actor="t", source="u")
    )
    assert ok is True
    assert calls == ["h2", "h1"]
