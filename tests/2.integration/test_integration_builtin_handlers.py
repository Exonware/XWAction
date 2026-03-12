"""
#exonware/xwaction/tests/2.integration/test_integration_builtin_handlers.py
Integration tests using real built-in handlers with the ActionExecutor pipeline.
"""

from __future__ import annotations
import pytest
from exonware.xwaction import XWAction
from exonware.xwaction.context import ActionContext
from exonware.xwaction.handlers import action_handler_registry
from exonware.xwaction.handlers.monitoring import MonitoringActionHandler
from exonware.xwaction.handlers.security import SecurityActionHandler
from exonware.xwaction.handlers.validation import ValidationActionHandler
from exonware.xwschema import XWSchema, XWSchemaValidationError
pytestmark = pytest.mark.xwaction_integration


def test_pipeline_with_validation_handler_blocks_invalid_inputs():
    action_handler_registry.register(ValidationActionHandler())
    class Svc:
        @XWAction(
            handlers=["validation"],
            in_types={"a": XWSchema({"type": "integer"})},
            roles=["*"],
        )
        def add(self, a: int, b: int) -> int:
            return a + b
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    with pytest.raises(XWSchemaValidationError):
        _ = s.add.execute(ctx, s, a="nope", b=2)


def test_pipeline_with_security_handler_blocks_missing_token():
    action_handler_registry.register(SecurityActionHandler())
    class Svc:
        @XWAction(handlers=["security"], roles=["*"], security="api_key")
        def ping(self) -> str:
            return "pong"
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    # security handler returns False -> executor raises schema validation error wrapper
    with pytest.raises(Exception):
        _ = s.ping.execute(ctx, s)


def test_pipeline_with_monitoring_handler_records_success():
    action_handler_registry.register(MonitoringActionHandler())
    class Svc:
        @XWAction(handlers=["monitoring"], roles=["*"])
        def ping(self) -> str:
            return "pong"
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    res = s.ping.execute(ctx, s)
    assert res.success is True
    assert res.data == "pong"
