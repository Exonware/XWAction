"""
#exonware/xwaction/tests/1.unit/test_unit_handlers_security_monitoring_workflow.py
Unit tests for built-in handler implementations.
"""

from __future__ import annotations
from types import SimpleNamespace
import pytest
from exonware.xwaction.context import ActionContext
from exonware.xwaction.handlers.monitoring import MonitoringActionHandler
from exonware.xwaction.handlers.security import SecurityActionHandler
from exonware.xwaction.handlers.workflow import WorkflowActionHandler
pytestmark = pytest.mark.xwaction_unit
@pytest.mark.parametrize(
    "token, ok",
    [
        ("", False),
        ("short", False),
        ("0123456789", True),
        ("a" * 100, True),
    ],
)


def test_security_basic_token_validation(token: str, ok: bool):
    h = SecurityActionHandler()
    assert h._basic_token_validation(token) is ok
@pytest.mark.parametrize(
    "required_roles,user_roles,ok",
    [
        ([], [], True),
        (["*"], [], True),
        (["admin"], ["admin"], True),
        (["admin"], ["user"], False),
        (["admin", "ops"], ["admin", "ops"], True),
        (["admin", "ops"], ["admin"], False),
    ],
)


def test_security_authorization(required_roles, user_roles, ok):
    h = SecurityActionHandler()
    action = SimpleNamespace(api_name="a", roles=required_roles, security_config="api_key", rate_limit=None, audit_enabled=False)
    ctx = ActionContext(actor="u", source="t", metadata={"auth_token": "0123456789", "roles": user_roles})
    assert h._check_authorization(action, ctx) is ok
@pytest.mark.parametrize(
    "required_roles,user_roles,ok",
    [
        (["admin"], ["admin"], True),
        (["admin"], ["user"], False),
        (["admin", "ops"], ["admin", "ops"], True),
        (["admin", "ops"], ["ops"], False),
    ],
)


def test_security_authorization_accepts_user_roles_key(required_roles, user_roles, ok):
    h = SecurityActionHandler()
    action = SimpleNamespace(api_name="a", roles=required_roles, security_config="api_key", rate_limit=None, audit_enabled=False)
    ctx = ActionContext(actor="u", source="t", metadata={"auth_token": "0123456789", "user_roles": user_roles})
    assert h._check_authorization(action, ctx) is ok


def test_security_rate_limit_blocks_second_request_within_one_second(monkeypatch: pytest.MonkeyPatch):
    h = SecurityActionHandler()
    action = SimpleNamespace(api_name="a", roles=["*"], security_config="api_key", rate_limit="100/hour", audit_enabled=False)
    t = 1000.0
    def fake_time():
        return t
    monkeypatch.setattr("time.time", fake_time)
    ctx = ActionContext(actor="u", source="t", metadata={"auth_token": "0123456789", "roles": ["*"]})
    assert h.before_execution(action, ctx) is True
    # same timestamp -> should be blocked
    assert h.before_execution(action, ctx) is False
    # advance time by >= 1s -> allowed again
    t = 1001.0
    assert h.before_execution(action, ctx) is True


def test_monitoring_before_and_after_records_execution():
    h = MonitoringActionHandler()
    action = SimpleNamespace(api_name="a")
    ctx = ActionContext(actor="u", source="t")
    assert h.before_execution(action, ctx, x=1) is True
    assert h.after_execution(action, ctx, result={"ok": True}) is True
    rec = h._find_execution_record(ctx.trace_id)
    assert rec is not None
    assert rec["action_name"] == "a"
    assert rec["success"] is True
    assert "duration" in rec


def test_monitoring_on_error_marks_record_failed():
    h = MonitoringActionHandler()
    action = SimpleNamespace(api_name="a")
    ctx = ActionContext(actor="u", source="t")
    assert h.before_execution(action, ctx) is True
    assert h.on_error(action, ctx, error=ValueError("x")) is True
    rec = h._find_execution_record(ctx.trace_id)
    assert rec is not None
    assert rec["success"] is False
    assert rec["error_type"] == "ValueError"


def test_workflow_handler_tracks_state_in_xwdata():
    h = WorkflowActionHandler()
    action = SimpleNamespace(api_name="a", workflow_steps=None, rollback=False)
    ctx = ActionContext(actor="u", source="t")
    assert h.before_execution(action, ctx, x=1) is True
    # after_execution should mark completed
    assert h.after_execution(action, ctx, result={"ok": True}) is True
    wf = h._workflow_state[ctx.trace_id]
    assert isinstance(wf, dict)
    assert wf["status"] == "completed"
    assert wf["action_name"] == "a"


def test_workflow_handler_on_error_marks_failed():
    h = WorkflowActionHandler()
    action = SimpleNamespace(api_name="a", workflow_steps=None, rollback=False)
    ctx = ActionContext(actor="u", source="t")
    assert h.before_execution(action, ctx) is True
    assert h.on_error(action, ctx, error=RuntimeError("boom")) is True
    wf = h._workflow_state[ctx.trace_id]
    assert wf["status"] == "failed"
    assert "error" in wf
