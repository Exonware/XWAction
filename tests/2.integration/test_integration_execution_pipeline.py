"""
#exonware/xwaction/tests/2.integration/test_integration_execution_pipeline.py
Integration tests that exercise the executor pipeline via wrapper.execute().
"""

from __future__ import annotations
import pytest
from exonware.xwaction import ActionHandlerPhase, XWAction
from exonware.xwaction.context import ActionContext
from exonware.xwaction.handlers import aActionHandlerBase, action_handler_registry
from exonware.xwschema import XWSchema, XWSchemaValidationError
pytestmark = pytest.mark.xwaction_integration


class _RecordHandler(aActionHandlerBase):

    def __init__(self, calls: list[str]):
        super().__init__(name="record", priority=100, async_enabled=False)
        self._calls = calls
    @property

    def supported_phases(self):
        return {ActionHandlerPhase.BEFORE, ActionHandlerPhase.AFTER, ActionHandlerPhase.ERROR}

    def before_execution(self, action, context: ActionContext, **kwargs) -> bool:
        self._calls.append("before")
        return True

    def after_execution(self, action, context: ActionContext, result):
        self._calls.append("after")
        return True

    def on_error(self, action, context: ActionContext, error: Exception):
        self._calls.append("error")
        return True


def test_execute_pipeline_success_runs_handlers_and_returns_actionresult():
    calls: list[str] = []
    action_handler_registry.register(_RecordHandler(calls))
    class Svc:
        @XWAction(
            handlers=["record"],
            in_types={"a": XWSchema({"type": "integer"})},
        )
        def add(self, a: int, b: int) -> int:
            return a + b
    s = Svc()
    ctx = ActionContext(actor="tester", source="pytest", metadata={"roles": ["*"]})
    res = s.add.execute(ctx, s, a=1, b=2)
    assert res.success is True
    assert res.data == 3
    assert calls == ["before", "after"]


def test_execute_pipeline_validation_failure_raises_xwschema_validation_error():
    class Svc:
        @XWAction(
            handlers=["record"],
            in_types={"a": XWSchema({"type": "integer"})},
        )
        def add(self, a: int, b: int) -> int:
            return a + b
    s = Svc()
    ctx = ActionContext(actor="tester", source="pytest", metadata={"roles": ["*"]})
    with pytest.raises(XWSchemaValidationError):
        _ = s.add.execute(ctx, s, a="nope", b=2)
