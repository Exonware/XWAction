"""
#exonware/xwaction/tests/1.unit/test_unit_errors.py
Unit tests for xwaction error types.
"""

from __future__ import annotations
import pytest
from exonware.xwaction.errors import (
    XWActionError,
    XWActionValidationError,
    XWActionSecurityError,
    XWActionWorkflowError,
    XWActionEngineError,
    XWActionPermissionError,
    XWActionExecutionError,
)
pytestmark = pytest.mark.xwaction_unit


def test_xwaction_error_has_details():
    e = XWActionError("m", details={"a": 1})
    assert str(e) == "m"
    assert e.details["a"] == 1
@pytest.mark.parametrize(
    "param_name,constraint,value",
    [
        ("a", "min", 1),
        (None, None, None),
        ("x", "pattern", "abc"),
    ],
)


def test_validation_error_includes_issues_and_fields(param_name, constraint, value):
    issues = [{"message": "bad"}]
    e = XWActionValidationError("m", param_name=param_name, constraint=constraint, value=value, issues=issues)
    assert e.details["issues"] == issues
    assert e.issues == issues
    assert e.details["param"] == param_name
    assert e.details["constraint"] == constraint
    assert e.details["value"] == value


def test_security_error_merges_details():
    e = XWActionSecurityError("m", security_type="auth", details={"x": 1})
    assert e.details["security_type"] == "auth"
    assert e.details["x"] == 1
@pytest.mark.parametrize(
    "step, idx",
    [("s1", 0), ("s2", 2), (None, None)],
)


def test_workflow_error_fields(step, idx):
    e = XWActionWorkflowError("m", workflow_step=step, step_number=idx, details={"k": 1})
    assert e.details["workflow_step"] == step
    assert e.details["step_number"] == idx
    assert e.details["k"] == 1
@pytest.mark.parametrize(
    "engine_name, engine_type",
    [("native", "execution"), ("celery", "execution"), (None, None)],
)


def test_engine_error_fields(engine_name, engine_type):
    e = XWActionEngineError("m", engine_name=engine_name, engine_type=engine_type, details={"k": 1})
    assert e.details["engine_name"] == engine_name
    assert e.details["engine_type"] == engine_type
    assert e.details["k"] == 1


def test_permission_error_message_contains_action_and_roles():
    e = XWActionPermissionError("act", required=["admin"], actual=["user"])
    assert "Permission denied" in str(e)
    assert e.details["action"] == "act"
    assert e.required_roles == ["admin"]
    assert e.user_roles == ["user"]


def test_execution_error_wraps_original_exception():
    orig = ValueError("bad")
    e = XWActionExecutionError("act", orig)
    assert "act" in str(e)
    assert e.details["error_type"] == "ValueError"
    assert "bad" in e.details["error_message"]
    assert e.original_error is orig
