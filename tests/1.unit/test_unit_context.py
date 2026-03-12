"""
#exonware/xwaction/tests/1.unit/test_unit_context.py
Unit tests for ActionContext + ActionResult.
"""

from __future__ import annotations
import pytest
from exonware.xwaction.context import ActionContext, ActionResult
pytestmark = pytest.mark.xwaction_unit


def test_action_context_generates_trace_id():
    c1 = ActionContext(actor="a")
    c2 = ActionContext(actor="a")
    assert isinstance(c1.trace_id, str) and c1.trace_id
    assert isinstance(c2.trace_id, str) and c2.trace_id
    assert c1.trace_id != c2.trace_id
@pytest.mark.parametrize(
    "initial_meta, key, value",
    [
        ({}, "k", 1),
        ({"k": 1}, "k", 2),
        ({"a": "b"}, "x", {"y": 3}),
    ],
)


def test_action_context_metadata_helpers(initial_meta, key, value):
    ctx = ActionContext(actor="u", metadata=dict(initial_meta))
    assert ctx.has_metadata("missing") is False
    ctx.add_metadata(key, value)
    assert ctx.has_metadata(key) is True
    assert ctx.get_metadata(key) == value


def test_action_context_to_dict_has_expected_keys():
    ctx = ActionContext(actor="u", source="s", metadata={"a": 1})
    d = ctx.to_dict()
    assert set(d.keys()) >= {"actor", "timestamp", "source", "trace_id", "metadata", "start_time", "workflow_state"}
    assert d["actor"] == "u"
    assert d["source"] == "s"
    assert d["metadata"]["a"] == 1
@pytest.mark.parametrize(
    "success,data,error",
    [
        (True, {"x": 1}, None),
        (True, 123, None),
        (False, None, "boom"),
    ],
)


def test_action_result_to_dict(success, data, error):
    r = ActionResult(success=success, data=data, error=error, duration=1.25, metadata={"m": 1})
    d = r.to_dict()
    assert d["success"] == success
    assert d["data"] == data
    assert d["error"] == error
    assert d["duration"] == 1.25
    assert d["metadata"]["m"] == 1
    assert isinstance(d["timestamp"], str)


def test_action_result_factories():
    ok = ActionResult.success(data=5, duration=0.1, a=1)
    assert ok.success is True
    assert ok.data == 5
    assert ok.duration == 0.1
    assert ok.metadata["a"] == 1
    bad = ActionResult.failure(error="x", duration=0.2, b=2)
    assert bad.success is False
    assert bad.error == "x"
    assert bad.duration == 0.2
    assert bad.metadata["b"] == 2
