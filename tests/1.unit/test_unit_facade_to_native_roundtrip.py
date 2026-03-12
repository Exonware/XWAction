"""
#exonware/xwaction/tests/1.unit/test_unit_facade_to_native_roundtrip.py
Unit tests for XWAction.to_native() and XWAction.from_native().
"""

from __future__ import annotations
import pytest
from exonware.xwaction import ActionProfile, XWAction
from exonware.xwschema import XWSchema
pytestmark = pytest.mark.xwaction_unit


def _fn(self, a: int, b: str) -> int:  # noqa: ANN001
    return a


def _fn_no_hints(self, a, b):  # noqa: ANN001
    return a


def test_to_native_includes_core_fields():
    a = XWAction(
        api_name="f",
        operationId="op",
        summary="s",
        description="d",
        tags=["t1"],
        profile=ActionProfile.QUERY,
        roles=["admin"],
        func=_fn,
    )
    d = a.to_native()
    assert d["api_name"] == "f"
    assert d["operationId"] == "op"
    assert d["summary"] == "s"
    assert d["description"] == "d"
    assert d["tags"] == ["t1"]
    assert d["profile"] == ActionProfile.QUERY.value
    assert d["roles"] == ["admin"]
@pytest.mark.parametrize(
    "schema_type, expected_param_type",
    [
        ("string", "str"),
        ("integer", "int"),
        ("boolean", "bool"),
        ("object", "dict"),
        ("array", "list"),
    ],
)


def test_to_native_parameters_mapping_uses_schema_types(schema_type: str, expected_param_type: str):
    a = XWAction(
        api_name="f",
        in_types={"a": XWSchema({"type": schema_type})},
        func=_fn_no_hints,
    )
    d = a.to_native()
    assert d["parameters"]["a"]["type"] == expected_param_type


def test_to_native_parameters_mapping_prefers_function_type_hints():
    a = XWAction(
        api_name="f",
        in_types={"a": XWSchema({"type": "string"})},
        func=_fn,
    )
    d = a.to_native()
    assert d["parameters"]["a"]["type"] == "int"


def test_from_native_roundtrip_preserves_profile_and_tags():
    a = XWAction(api_name="x", tags=["t"], profile=ActionProfile.COMMAND, func=_fn)
    d = a.to_native()
    b = XWAction.from_native(d)
    assert b.api_name == "x"
    assert b.profile == ActionProfile.COMMAND
    assert b.tags == ["t"]
