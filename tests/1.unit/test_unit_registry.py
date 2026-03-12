"""
#exonware/xwaction/tests/1.unit/test_unit_registry.py
Unit tests for ActionRegistry behavior.
"""

from __future__ import annotations
import pytest
from exonware.xwaction import ActionRegistry, ActionProfile, XWAction
pytestmark = pytest.mark.xwaction_unit


def test_registry_metrics_increment_on_register():
    _ = XWAction(api_name="a1", profile=ActionProfile.QUERY, tags=["t1"], func=lambda: None)
    _ = XWAction(api_name="a2", profile=ActionProfile.COMMAND, tags=["t2"], func=lambda: None)
    metrics = ActionRegistry.get_metrics()
    assert metrics["total_actions"] == 2
    assert metrics["total_entities"] == 1
    assert metrics["profiles"][ActionProfile.QUERY.value] == 1
    assert metrics["profiles"][ActionProfile.COMMAND.value] == 1


def test_registry_find_actions_filters_by_profile_and_tag():
    _ = XWAction(api_name="q1", profile=ActionProfile.QUERY, tags=["alpha"], func=lambda: None)
    _ = XWAction(api_name="q2", profile=ActionProfile.QUERY, tags=["beta"], func=lambda: None)
    _ = XWAction(api_name="c1", profile=ActionProfile.COMMAND, tags=["alpha"], func=lambda: None)
    qs = ActionRegistry.find_actions(profile=ActionProfile.QUERY.value)
    assert {a.api_name for a in qs} == {"q1", "q2"}
    alpha = ActionRegistry.find_actions(tag="alpha")
    assert {a.api_name for a in alpha} == {"q1", "c1"}


def test_registry_export_openapi_spec_has_paths():
    _ = XWAction(api_name="ping", profile=ActionProfile.ACTION, func=lambda: None)
    spec = ActionRegistry.export_openapi_spec(title="T", version="0.0.0")
    assert spec["openapi"] == "3.1.0"
    assert "/default/ping" in spec["paths"]
