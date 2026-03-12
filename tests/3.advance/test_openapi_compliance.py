#!/usr/bin/env python3
"""
#exonware/xwaction/tests/3.advance/test_openapi_compliance.py
OpenAPI 3.1 compliance verification tests for xwaction.
Priority #3: Maintainability Excellence
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 07-Jan-2025
"""

from __future__ import annotations
import pytest
from typing import Any
from exonware.xwaction.facade import XWAction
from exonware.xwaction.registry import ActionRegistry
from exonware.xwaction.core.openapi import OpenAPIGenerator
@pytest.mark.xwaction_advance
@pytest.mark.xwaction_maintainability

class TestOpenAPI31Compliance:
    """Test OpenAPI 3.1 specification compliance."""

    def test_openapi_version_is_31(self):
        """Test that generated OpenAPI spec uses version 3.1.0."""
        registry = ActionRegistry()
        spec = registry.export_openapi_spec()
        assert spec["openapi"] == "3.1.0", "OpenAPI version must be 3.1.0"

    def test_openapi_info_structure(self):
        """Test that OpenAPI info structure is correct."""
        registry = ActionRegistry()
        spec = registry.export_openapi_spec(title="Test API", version="1.0.0")
        assert "info" in spec
        assert spec["info"]["title"] == "Test API"
        assert spec["info"]["version"] == "1.0.0"
        assert "description" in spec["info"]

    def test_openapi_paths_structure(self):
        """Test that OpenAPI paths structure is correct."""
        def test_action(x: int, y: str) -> dict:
            return {"result": f"{x}_{y}"}
        action = XWAction(api_name="test_action", func=test_action)
        registry = ActionRegistry()
        registry.register("test", action)
        spec = registry.export_openapi_spec()
        assert "paths" in spec
        assert isinstance(spec["paths"], dict)

    def test_openapi_components_structure(self):
        """Test that OpenAPI components structure is correct."""
        registry = ActionRegistry()
        spec = registry.export_openapi_spec()
        assert "components" in spec
        assert "securitySchemes" in spec["components"]
        assert isinstance(spec["components"]["securitySchemes"], dict)

    def test_openapi_tags_structure(self):
        """Test that OpenAPI tags structure is correct."""
        registry = ActionRegistry()
        spec = registry.export_openapi_spec()
        assert "tags" in spec
        assert isinstance(spec["tags"], list)

    def test_operation_spec_structure(self):
        """Test that individual operation spec has required fields."""
        def test_action(x: int) -> dict:
            return {"result": x}
        action = XWAction(api_name="test_action", func=test_action)
        generator = OpenAPIGenerator()
        spec = generator.generate_spec(action)
        # Required fields for OpenAPI 3.1 operation
        assert "operationId" in spec
        assert "summary" in spec
        assert "description" in spec
        assert "tags" in spec
        assert "responses" in spec
        assert isinstance(spec["responses"], dict)

    def test_operation_responses_structure(self):
        """Test that operation responses follow OpenAPI 3.1 format."""
        def test_action() -> dict:
            return {"result": "ok"}
        action = XWAction(api_name="test_action", func=test_action)
        generator = OpenAPIGenerator()
        spec = generator.generate_spec(action)
        responses = spec["responses"]
        # Should have at least 200, 400, 500
        assert "200" in responses
        assert "400" in responses
        assert "500" in responses
        # Each response should have description
        for status_code, response in responses.items():
            assert "description" in response

    def test_operation_parameters_structure(self):
        """Test that operation parameters follow OpenAPI 3.1 format."""
        def test_action(x: int, y: str = "default") -> dict:
            return {"result": f"{x}_{y}"}
        action = XWAction(api_name="test_action", func=test_action)
        generator = OpenAPIGenerator()
        spec = generator.generate_spec(action)
        assert "parameters" in spec
        assert isinstance(spec["parameters"], list)
        # Check parameter structure
        for param in spec["parameters"]:
            assert "name" in param
            assert "in" in param
            assert "required" in param
            assert "schema" in param
            assert "type" in param["schema"]

    def test_openapi_type_mapping(self):
        """Test that Python types are correctly mapped to OpenAPI types."""
        generator = OpenAPIGenerator()
        # Test basic type mappings
        assert generator._python_type_to_openapi(str) == {"type": "string"}
        assert generator._python_type_to_openapi(int) == {"type": "integer"}
        assert generator._python_type_to_openapi(float) == {"type": "number"}
        assert generator._python_type_to_openapi(bool) == {"type": "boolean"}
        assert generator._python_type_to_openapi(list) == {"type": "array"}
        assert generator._python_type_to_openapi(dict) == {"type": "object"}

    def test_openapi_list_types(self):
        """Test that list types are correctly converted to OpenAPI array."""
        generator = OpenAPIGenerator()
        # Test list[int]
        list_int_spec = generator._python_type_to_openapi(list[int])
        assert list_int_spec["type"] == "array"
        assert "items" in list_int_spec
        assert list_int_spec["items"]["type"] == "integer"
        # Test list[str]
        list_str_spec = generator._python_type_to_openapi(list[str])
        assert list_str_spec["type"] == "array"
        assert list_str_spec["items"]["type"] == "string"

    def test_openapi_optional_types(self):
        """Test that Optional types are correctly handled."""
        from typing import Optional
        generator = OpenAPIGenerator()
        # Optional[int] should become integer (not nullable in 3.1, but type preserved)
        optional_int_spec = generator._python_type_to_openapi(Optional[int])
        assert optional_int_spec["type"] == "integer"

    def test_openapi_security_schemes(self):
        """Test that security schemes are correctly generated."""
        registry = ActionRegistry()
        spec = registry.export_openapi_spec()
        security_schemes = spec["components"]["securitySchemes"]
        assert isinstance(security_schemes, dict)

    def test_openapi_spec_valid_json(self):
        """Test that OpenAPI spec can be serialized to valid JSON."""
        import json
        registry = ActionRegistry()
        spec = registry.export_openapi_spec()
        # Should be able to serialize to JSON
        json_str = json.dumps(spec)
        assert isinstance(json_str, str)
        # Should be able to deserialize back
        deserialized = json.loads(json_str)
        assert deserialized["openapi"] == "3.1.0"

    def test_openapi_spec_completeness(self):
        """Test that OpenAPI spec has all required top-level fields."""
        registry = ActionRegistry()
        spec = registry.export_openapi_spec()
        # Required top-level fields for OpenAPI 3.1
        required_fields = ["openapi", "info", "paths", "components"]
        for field in required_fields:
            assert field in spec, f"Missing required field: {field}"
        # Info should have required fields
        assert "title" in spec["info"]
        assert "version" in spec["info"]

    def test_multiple_actions_openapi_export(self):
        """Test that multiple actions are correctly exported to OpenAPI."""
        def action1(x: int) -> dict:
            return {"result": x}
        def action2(y: str) -> dict:
            return {"result": y}
        action1_obj = XWAction(api_name="action1", func=action1)
        action2_obj = XWAction(api_name="action2", func=action2)
        registry = ActionRegistry()
        registry.register("test", action1_obj)
        registry.register("test", action2_obj)
        spec = registry.export_openapi_spec()
        # Should have paths for both actions
        assert len(spec["paths"]) >= 2
