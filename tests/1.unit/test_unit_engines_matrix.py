"""
#exonware/xwaction/tests/1.unit/test_unit_engines_matrix.py
Unit tests for engine can_execute behavior across profiles.
"""

from __future__ import annotations
import pytest
from exonware.xwaction import ActionProfile
from exonware.xwaction.engines.celery import CeleryActionEngine
from exonware.xwaction.engines.fastapi import FastAPIActionEngine
from exonware.xwaction.engines.native import NativeActionEngine
from exonware.xwaction.engines.prefect import PrefectActionEngine
pytestmark = pytest.mark.xwaction_unit
@pytest.mark.parametrize("profile", list(ActionProfile))


def test_native_engine_can_execute_any_profile(profile: ActionProfile):
    assert NativeActionEngine().can_execute(profile) is True
@pytest.mark.parametrize(
    "profile, ok",
    [(p, p in {ActionProfile.QUERY, ActionProfile.COMMAND, ActionProfile.ENDPOINT}) for p in ActionProfile],
)


def test_fastapi_engine_can_execute_expected_profiles(profile: ActionProfile, ok: bool):
    assert FastAPIActionEngine().can_execute(profile) is ok
@pytest.mark.parametrize(
    "profile, ok",
    [(p, p in {ActionProfile.TASK, ActionProfile.WORKFLOW, ActionProfile.COMMAND}) for p in ActionProfile],
)


def test_celery_engine_can_execute_expected_profiles(profile: ActionProfile, ok: bool):
    assert CeleryActionEngine().can_execute(profile) is ok
@pytest.mark.parametrize(
    "profile, ok",
    [(p, p in {ActionProfile.WORKFLOW, ActionProfile.TASK, ActionProfile.COMMAND}) for p in ActionProfile],
)


def test_prefect_engine_can_execute_expected_profiles(profile: ActionProfile, ok: bool):
    assert PrefectActionEngine().can_execute(profile) is ok
