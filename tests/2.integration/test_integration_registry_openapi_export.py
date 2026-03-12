"""
#exonware/xwaction/tests/2.integration/test_integration_registry_openapi_export.py
Integration tests around ActionRegistry export_openapi_spec with multiple actions.
"""

from __future__ import annotations
import pytest
from exonware.xwaction import ActionRegistry, ActionProfile, XWAction
pytestmark = pytest.mark.xwaction_integration


def test_export_openapi_spec_contains_all_registered_paths():
    _ = XWAction(api_name="a1", profile=ActionProfile.ACTION, func=lambda: None)
    _ = XWAction(api_name="a2", profile=ActionProfile.QUERY, func=lambda: None)
    _ = XWAction(api_name="a3", profile=ActionProfile.COMMAND, func=lambda: None)
    spec = ActionRegistry.export_openapi_spec(title="T", version="1")
    assert spec["openapi"] == "3.1.0"
    assert "/default/a1" in spec["paths"]
    assert "/default/a2" in spec["paths"]
    assert "/default/a3" in spec["paths"]


def test_export_all_returns_descriptors_list_per_entity():
    _ = XWAction(api_name="a1", profile=ActionProfile.ACTION, func=lambda: None)
    exported = ActionRegistry.export_all()
    assert "default" in exported
    assert isinstance(exported["default"], list)
