"""
#exonware/xwaction/tests/0.core/test_core_imports.py
Core import and export-surface tests (MIGRAT parity).
"""

from __future__ import annotations
import pytest
pytestmark = pytest.mark.xwaction_core


def test_import_exonware_xaction():
    import exonware.xwaction as xwaction_pkg  # noqa: F401


def test_import_convenience_xaction():
    import xwaction  # noqa: F401


def test_export_surface_minimum():
    import exonware.xwaction as xwaction_pkg
    assert hasattr(xwaction_pkg, "XWAction")
    assert hasattr(xwaction_pkg, "ActionRegistry")
    assert hasattr(xwaction_pkg, "ActionProfile")
    assert hasattr(xwaction_pkg, "ActionHandlerPhase")


def test_engines_and_handlers_exports_present():
    import exonware.xwaction as xwaction_pkg
    assert hasattr(xwaction_pkg, "action_engine_registry")
    assert hasattr(xwaction_pkg, "action_handler_registry")
    assert hasattr(xwaction_pkg, "NativeActionEngine")
    assert hasattr(xwaction_pkg, "ValidationActionHandler")
