"""
#exonware/xwaction/tests/0.core/test_core_wrapper_vs_execute.py
Core tests: wrapper direct call vs wrapper.execute(ActionContext,...).
"""

from __future__ import annotations
import pytest
from exonware.xwaction import XWAction
from exonware.xwaction.context import ActionContext
from exonware.xwschema import XWSchema, XWSchemaValidationError
pytestmark = pytest.mark.xwaction_core


def test_wrapper_direct_call_returns_raw_value():
    class Svc:
        @XWAction(roles=["*"])
        def add(self, a: int, b: int) -> int:
            return a + b
    s = Svc()
    assert s.add(1, 2) == 3


def test_wrapper_execute_returns_action_result():
    class Svc:
        @XWAction(roles=["*"])
        def add(self, a: int, b: int) -> int:
            return a + b
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    res = s.add.execute(ctx, s, a=1, b=2)
    assert res.success is True
    assert res.data == 3
@pytest.mark.parametrize("roles", [["*"], [], ["admin"]])


def test_wrapper_direct_call_permission_check_uses_default_context_roles_empty(roles):
    class Svc:
        @XWAction(roles=roles)
        def ping(self) -> str:
            return "pong"
    s = Svc()
    if roles == ["admin"]:
        with pytest.raises(Exception):
            _ = s.ping()
    else:
        assert s.ping() == "pong"


def test_wrapper_direct_call_validation_raises_xwactionexecutionerror():
    class Svc:
        @XWAction(roles=["*"], in_types={"a": XWSchema({"type": "integer"})})
        def add(self, a: int, b: int) -> int:
            return a + b
    s = Svc()
    with pytest.raises(Exception):
        _ = s.add(a="nope", b=2)


def test_wrapper_execute_validation_raises_xwschema_validation_error():
    class Svc:
        @XWAction(roles=["*"], in_types={"a": XWSchema({"type": "integer"})})
        def add(self, a: int, b: int) -> int:
            return a + b
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    with pytest.raises(XWSchemaValidationError):
        _ = s.add.execute(ctx, s, a="nope", b=2)
