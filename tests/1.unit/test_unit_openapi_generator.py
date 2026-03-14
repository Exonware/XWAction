"""
#exonware/xwaction/tests/1.unit/test_unit_openapi_generator.py
Unit tests for OpenAPIGenerator.
We intentionally use parametrization to multiply coverage without slow runtime.
"""

from __future__ import annotations
import pytest
from exonware.xwaction.core.openapi import OpenAPIGenerator
from exonware.xwaction.facade import XWAction
pytestmark = pytest.mark.xwaction_unit
@pytest.mark.parametrize(
    "py_type, expected",
    [
        (str, {"type": "string"}),
        (int, {"type": "integer"}),
        (float, {"type": "number"}),
        (bool, {"type": "boolean"}),
        (dict, {"type": "object"}),
        (list, {"type": "array"}),
        (set, {"type": "array"}),
        (tuple, {"type": "array"}),
    ],
)


def test_python_type_to_openapi_basic_types(py_type, expected):
    g = OpenAPIGenerator()
    assert g._python_type_to_openapi(py_type) == expected
@pytest.mark.parametrize(
    "py_type, expected",
    [
        (int | None, {"type": "integer"}),
        (str | None, {"type": "string"}),
        (int | None, {"type": "integer"}),
        (str | None, {"type": "string"}),
    ],
)


def test_python_type_to_openapi_optional(py_type, expected):
    g = OpenAPIGenerator()
    assert g._python_type_to_openapi(py_type) == expected
@pytest.mark.parametrize(
    "py_type, expected",
    [
        (list[int], {"type": "array", "items": {"type": "integer"}}),
        (list[str], {"type": "array", "items": {"type": "string"}}),
        (list[bool], {"type": "array", "items": {"type": "boolean"}}),
    ],
)


def test_python_type_to_openapi_list_items(py_type, expected):
    g = OpenAPIGenerator()
    assert g._python_type_to_openapi(py_type) == expected
@pytest.mark.parametrize(
    "annotation",
    [None, "X", object()],
)


def test_python_type_to_openapi_unknown_defaults_to_string(annotation):
    g = OpenAPIGenerator()
    assert g._python_type_to_openapi(annotation) == {"type": "string"}
@pytest.mark.parametrize(
    "py_type",
    [
        list[int | None],
        list[str | None],
        list[int | None],
        list[str | None],
        dict[str, int],
        dict[str, str],
        list[int] | None,
        list[str] | None,
        dict[str, int] | None,
    ],
)


def test_python_type_to_openapi_more_generics_does_not_crash(py_type):
    g = OpenAPIGenerator()
    out = g._python_type_to_openapi(py_type)
    assert isinstance(out, dict)
    assert "type" in out


def test_generate_spec_includes_defaults_when_action_fields_missing():
    a = XWAction(api_name="ping", func=lambda: None)
    spec = OpenAPIGenerator().generate_spec(a)
    assert spec["operationId"]
    assert isinstance(spec["tags"], list)
    assert "responses" in spec


def test_generate_spec_extracts_parameters_from_function_signature():
    def fn(self, a: int, b: str, c: int | None = None):  # noqa: ANN001
        return a
    a = XWAction(api_name="f", func=fn)
    spec = OpenAPIGenerator().generate_spec(a)
    names = [p["name"] for p in spec["parameters"]]
    assert "self" not in names
    assert names == ["a", "b", "c"]
    required = {p["name"]: p["required"] for p in spec["parameters"]}
    assert required["a"] is True
    assert required["b"] is True
    assert required["c"] is False
