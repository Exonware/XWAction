"""
#exonware/xwaction/tests/0.core/test_core_facade.py
Core facade behavior tests (focused on MIGRAT feature parity).
"""

from __future__ import annotations
from typing import Any
import pytest
from exonware.xwaction import XWAction, ActionRegistry, ActionProfile
pytestmark = pytest.mark.xwaction_core


def test_decorator_basic_execution():
    class Svc:
        @XWAction()
        def add(self, a: int, b: int) -> int:
            return a + b
    s = Svc()
    assert s.add(1, 2) == 3
    assert hasattr(s.add, "_is_action") and s.add._is_action is True


def test_decorator_attaches_xwaction_attribute():
    class Svc:
        @XWAction()
        def ping(self) -> str:
            return "pong"
    s = Svc()
    assert hasattr(s.ping, "xwaction")
    assert s.ping.xwaction.api_name == "ping"


def test_smart_mode_shortcut_decorator():
    class Svc:
        @XWAction("smart")
        def ping(self) -> str:
            return "pong"
    s = Svc()
    assert s.ping() == "pong"


def test_profile_resolution_smoke():
    a = XWAction(profile="query", func=lambda: None)
    assert a.profile == ActionProfile.QUERY


def test_registry_registers_action():
    before = ActionRegistry.get_metrics()["total_actions"]
    _ = XWAction(func=lambda: None)
    after = ActionRegistry.get_metrics()["total_actions"]
    assert after >= before + 1


def test_to_openapi_returns_dict():
    a = XWAction(func=lambda: None)
    spec = a.to_openapi()
    assert isinstance(spec, dict)
    assert "operationId" in spec or "operation_id" in spec


def test_handler_registry_has_async_api():
    from exonware.xwaction import action_handler_registry
    assert hasattr(action_handler_registry, "execute_phase_async")


def test_engine_registry_has_selection_api():
    from exonware.xwaction import action_engine_registry
    assert hasattr(action_engine_registry, "select_engine")
