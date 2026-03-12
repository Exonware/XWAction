"""
#exonware/xwaction/tests/1.unit/test_unit_validation_contracts.py
Unit tests for ActionValidator contract parsing + schema building.
"""

from __future__ import annotations
from types import SimpleNamespace
import pytest
from exonware.xwaction.core.validation import ActionValidator
pytestmark = pytest.mark.xwaction_unit
@pytest.mark.parametrize(
    "constraint, expected",
    [
        ("string", {"type": "string"}),
        ("string:email", {"type": "string", "format": "email"}),
        ("string:uri", {"type": "string", "format": "uri"}),
        ("string:date", {"type": "string", "format": "date"}),
        ("string:datetime", {"type": "string", "format": "datetime"}),
        ("string:pattern:^a+$", {"type": "string", "pattern": "^a+$"}),
        ("string:min:2", {"type": "string", "minLength": 2}),
        ("string:max:9", {"type": "string", "maxLength": 9}),
        ("integer", {"type": "integer"}),
        ("integer:min:1", {"type": "integer", "minimum": 1}),
        ("integer:max:10", {"type": "integer", "maximum": 10}),
        ("number", {"type": "number"}),
        ("number:min:1.5", {"type": "number", "minimum": 1.5}),
        ("number:max:9.5", {"type": "number", "maximum": 9.5}),
        ("array:string", {"type": "array", "items": {"type": "string"}}),
        ("array:integer:min:1", {"type": "array", "items": {"type": "integer"}, "minItems": 1}),
        ("array:integer:max:3", {"type": "array", "items": {"type": "integer"}, "maxItems": 3}),
    ],
)


def test_parse_contract_constraint(constraint: str, expected: dict):
    v = ActionValidator()
    assert v._parse_contract_constraint(constraint) == expected
@pytest.mark.parametrize(
    "n",
    list(range(1, 51)),
)


def test_parse_contract_constraint_integer_min_many(n: int):
    v = ActionValidator()
    assert v._parse_contract_constraint(f"integer:min:{n}") == {"type": "integer", "minimum": n}
@pytest.mark.parametrize(
    "n",
    list(range(1, 51)),
)


def test_parse_contract_constraint_integer_max_many(n: int):
    v = ActionValidator()
    assert v._parse_contract_constraint(f"integer:max:{n}") == {"type": "integer", "maximum": n}
@pytest.mark.parametrize("constraint", ["", ":", "string:min:notint", "number:max:notfloat", "array::min:1"])


def test_parse_contract_constraint_invalid_falls_back_to_string(constraint: str):
    v = ActionValidator()
    assert v._parse_contract_constraint(constraint) == {"type": "string"}


def test_build_validation_schema_marks_required_when_no_optional_suffix():
    v = ActionValidator()
    action = SimpleNamespace(contracts={"input": {"a": "integer", "b": "string?"}})
    schema = v.build_validation_schema(action)
    assert schema is not None
    sd = schema.to_native()
    assert sd["type"] == "object"
    assert set(sd["properties"].keys()) == {"a", "b"}
    assert sd["properties"]["a"]["type"] == "integer"
    assert sd["properties"]["b"]["type"] == "string"
    # required list should include only "a"
    assert "a" in sd.get("required", [])
    assert "b" not in sd.get("required", [])


def test_build_contract_schema_builds_object_properties():
    v = ActionValidator()
    action = SimpleNamespace(contracts={"output": {"result": "string:email"}})
    schema = v.build_contract_schema(action)
    assert schema is not None
    sd = schema.to_native()
    assert sd["type"] == "object"
    assert sd["properties"]["result"]["type"] == "string"
    assert sd["properties"]["result"]["format"] == "email"
