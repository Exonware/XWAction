"""
#exonware/xwaction/tests/2.integration/test_integration_workflow_handler_state.py
Integration tests for workflow handler state transitions through the executor pipeline.
"""

from __future__ import annotations
import pytest
from exonware.xwaction import XWAction
from exonware.xwaction.context import ActionContext
from exonware.xwaction.handlers import action_handler_registry
from exonware.xwaction.handlers.workflow import WorkflowActionHandler
pytestmark = pytest.mark.xwaction_integration


def test_workflow_handler_state_transitions_success():
    h = WorkflowActionHandler()
    action_handler_registry.register(h)
    class Svc:
        @XWAction(handlers=["workflow"], roles=["*"])
        def ping(self) -> str:
            return "pong"
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    res = s.ping.execute(ctx, s)
    assert res.success is True
    wf = h._workflow_state[ctx.trace_id]
    assert wf["status"] == "completed"
    assert wf["action_name"] == "ping"
    assert "checkpoints" in wf


def test_workflow_handler_state_transitions_error():
    h = WorkflowActionHandler()
    action_handler_registry.register(h)
    class Svc:
        @XWAction(handlers=["workflow"], roles=["*"])
        def bad(self) -> str:
            raise RuntimeError("boom")
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    res = s.bad.execute(ctx, s)
    assert res.success is False
    wf = h._workflow_state[ctx.trace_id]
    assert wf["status"] == "failed"
    assert "error" in wf
