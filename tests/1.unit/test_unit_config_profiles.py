"""
#exonware/xwaction/tests/1.unit/test_unit_config_profiles.py
Unit tests for xwaction config + profile defaults.
"""

from __future__ import annotations
import pytest
from exonware.xwaction.config import (
    XWActionConfig,
    ProfileConfig,
    PROFILE_CONFIGS,
    get_profile_config,
    get_all_profiles,
    register_profile,
)
from exonware.xwaction.defs import ActionProfile
pytestmark = pytest.mark.xwaction_unit


def test_xwaction_config_copy_is_deep_copy_for_lists():
    cfg = XWActionConfig()
    cfg.default_handlers.append("security")
    clone = cfg.copy()
    assert clone is not cfg
    assert clone.default_handlers == cfg.default_handlers
    clone.default_handlers.append("monitoring")
    assert "monitoring" not in cfg.default_handlers
@pytest.mark.parametrize("profile", list(ActionProfile))


def test_profile_configs_has_all_profiles(profile: ActionProfile):
    assert profile in PROFILE_CONFIGS
    assert isinstance(PROFILE_CONFIGS[profile], ProfileConfig)
@pytest.mark.parametrize(
    "profile, expected_engine",
    [
        (ActionProfile.ACTION, "native"),
        (ActionProfile.QUERY, "fastapi"),
        (ActionProfile.COMMAND, "fastapi"),
        (ActionProfile.TASK, "celery"),
        (ActionProfile.WORKFLOW, "prefect"),
        (ActionProfile.ENDPOINT, "fastapi"),
    ],
)


def test_get_profile_config_by_enum(profile: ActionProfile, expected_engine: str):
    cfg = get_profile_config(profile)
    assert isinstance(cfg, ProfileConfig)
    assert cfg.engine == expected_engine
@pytest.mark.parametrize(
    "profile_str, expected_profile",
    [(p.value, p) for p in ActionProfile],
)


def test_get_profile_config_by_str(profile_str: str, expected_profile: ActionProfile):
    cfg = get_profile_config(profile_str)
    assert cfg == PROFILE_CONFIGS[expected_profile]


def test_get_all_profiles_returns_string_keys():
    allp = get_all_profiles()
    assert isinstance(allp, dict)
    assert set(allp.keys()) == {p.value for p in ActionProfile}


def test_register_profile_overrides_existing_profile_config():
    original = get_profile_config(ActionProfile.QUERY)
    new_cfg = ProfileConfig(readonly=True, cache_ttl=999, engine="native")
    register_profile(ActionProfile.QUERY.value, new_cfg)
    updated = get_profile_config(ActionProfile.QUERY)
    assert updated.cache_ttl == 999
    assert updated.engine == "native"
    # restore
    register_profile(ActionProfile.QUERY.value, original)
@pytest.mark.parametrize(
    "name",
    ["not-a-profile", "CUSTOM", "custom", "actionX", ""],
)


def test_register_profile_rejects_unknown_enum_value(name: str):
    with pytest.raises(ValueError):
        register_profile(name, ProfileConfig())
