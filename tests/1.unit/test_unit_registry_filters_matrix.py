"""
#exonware/xwaction/tests/1.unit/test_unit_registry_filters_matrix.py
Unit tests for ActionRegistry.find_actions() filter combinations.
"""

from __future__ import annotations
import pytest
from exonware.xwaction import ActionRegistry, ActionProfile, XWAction
pytestmark = pytest.mark.xwaction_unit


def test_find_actions_filters_by_entity_type():
    ActionRegistry.register("SvcA", XWAction(api_name="a1", profile=ActionProfile.ACTION, func=lambda: None))
    ActionRegistry.register("SvcB", XWAction(api_name="b1", profile=ActionProfile.ACTION, func=lambda: None))
    only_a = ActionRegistry.find_actions(entity_type="SvcA")
    assert {a.api_name for a in only_a} == {"a1"}
@pytest.mark.parametrize(
    "readonly",
    [True, False],
)


def test_find_actions_filters_by_readonly(readonly: bool):
    ActionRegistry.register("E", XWAction(api_name="r", profile=ActionProfile.ACTION, readonly=True, func=lambda: None))
    ActionRegistry.register("E", XWAction(api_name="w", profile=ActionProfile.ACTION, readonly=False, func=lambda: None))
    res = ActionRegistry.find_actions(readonly=readonly)
    names = {a.api_name for a in res}
    assert names == ({"r"} if readonly else {"w"})
@pytest.mark.parametrize(
    "security_config, query",
    [
        ("api_key", "api_key"),
        (["api_key", "roles"], "roles"),
        ({"oauth2": ["read"]}, "oauth2"),
    ],
)


def test_find_actions_filters_by_security_scheme(security_config, query):
    ActionRegistry.register("E", XWAction(api_name="s", profile=ActionProfile.ACTION, security=security_config, func=lambda: None))
    res = ActionRegistry.find_actions(security_scheme=query)
    assert {a.api_name for a in res} == {"s"}
