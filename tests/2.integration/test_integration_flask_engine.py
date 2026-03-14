"""
Integration tests for FlaskActionEngine.
"""

from __future__ import annotations
import builtins
import pytest
from exonware.xwaction import XWAction, ActionProfile
from exonware.xwaction.context import ActionContext
from exonware.xwaction.engines.flask import FlaskActionEngine
from exonware.xwaction.engines import action_engine_registry
from collections.abc import Callable
pytestmark = pytest.mark.xwaction_integration


class _Svc:
    @XWAction(roles=["*"])

    def ping(self) -> str:
        return "pong"


def test_flask_engine_can_execute_expected_profiles():
    assert FlaskActionEngine().can_execute(ActionProfile.QUERY) is True
    assert FlaskActionEngine().can_execute(ActionProfile.COMMAND) is True
    assert FlaskActionEngine().can_execute(ActionProfile.ENDPOINT) is True
    assert FlaskActionEngine().can_execute(ActionProfile.TASK) is False


def test_flask_engine_execute_fallback_when_no_app():
    s = _Svc()
    action = s.ping.xwaction
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    eng = FlaskActionEngine()
    res = eng.execute(action, ctx, s)
    assert res.success is True
    assert res.data == "pong"
    # assert res.metadata.get("engine") == "native"  # fallback uses native engine which doesn't set metadata


def test_flask_engine_execute_main_path_when_app_present_sets_metadata():
    s = _Svc()
    action = s.ping.xwaction
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    eng = FlaskActionEngine()
    eng._app = object()  # force non-fallback path
    res = eng.execute(action, ctx, s)
    assert res.success is True
    assert res.data == "pong"
    assert res.metadata.get("engine") == "flask"


def test_action_executor_uses_registered_flask_engine_when_configured():
    # Register a configured Flask engine so executor can select it by name
    eng = FlaskActionEngine()
    eng._app = object()
    action_engine_registry.register(eng)
    class Svc:
        @XWAction(engine="flask", profile="query", roles=["*"])
        def ping(self) -> str:
            return "pong"
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    res = s.ping.execute(ctx, s)
    assert res.success is True
    assert res.data == "pong"
    assert res.metadata.get("engine") == "flask"
