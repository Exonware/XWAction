"""
#exonware/xwaction/tests/2.integration/test_integration_engines_coverage.py
Integration tests that explicitly exercise ALL engines:
- NativeActionEngine
- FastAPIActionEngine
- CeleryActionEngine
- PrefectActionEngine
We keep these tests deterministic by forcing optional third-party imports
(fastapi/celery/prefect) to raise ImportError when needed.
"""

from __future__ import annotations
import builtins
from typing import Callable
import pytest
from exonware.xwaction import XWAction
from exonware.xwaction.context import ActionContext
from exonware.xwaction.engines.celery import CeleryActionEngine
from exonware.xwaction.engines.fastapi import FastAPIActionEngine
from exonware.xwaction.engines.native import NativeActionEngine
from exonware.xwaction.engines.prefect import PrefectActionEngine
from exonware.xwaction.engines import action_engine_registry
pytestmark = pytest.mark.xwaction_integration


def _block_imports(monkeypatch: pytest.MonkeyPatch, blocked: set[str]) -> None:
    """Force ImportError for specific top-level modules."""
    orig_import: Callable = builtins.__import__
    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: ANN001
        top = name.split(".", 1)[0]
        if top in blocked:
            raise ImportError(f"blocked import: {top}")
        return orig_import(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, "__import__", _fake_import)


class _Svc:
    @XWAction(roles=["*"])

    def ping(self) -> str:
        return "pong"


def test_native_engine_execute_success_and_failure():
    s = _Svc()
    action = s.ping.xwaction
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    ok = NativeActionEngine().execute(action, ctx, s)
    assert ok.success is True
    assert ok.data == "pong"
    def bad() -> None:
        raise RuntimeError("boom")
    bad_action = XWAction(api_name="bad", roles=["*"], func=bad)
    bad_res = NativeActionEngine().execute(bad_action, ctx, None)
    assert bad_res.success is False
    assert "boom" in (bad_res.error or "")


def test_fastapi_engine_execute_fallback_when_no_app():
    s = _Svc()
    action = s.ping.xwaction
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    eng = FastAPIActionEngine()
    res = eng.execute(action, ctx, s)
    assert res.success is True
    assert res.data == "pong"


def test_fastapi_engine_execute_main_path_when_app_present_sets_metadata():
    s = _Svc()
    action = s.ping.xwaction
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    eng = FastAPIActionEngine()
    eng._app = object()  # force non-fallback path
    res = eng.execute(action, ctx, s)
    assert res.success is True
    assert res.data == "pong"
    assert res.metadata.get("engine") == "fastapi"


def test_celery_engine_execute_fallback_when_no_app():
    s = _Svc()
    action = s.ping.xwaction
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    eng = CeleryActionEngine()
    res = eng.execute(action, ctx, s)
    assert res.success is True
    assert res.data == "pong"


def test_celery_engine_execute_main_path_when_app_present_even_if_celery_missing(monkeypatch: pytest.MonkeyPatch):
    _block_imports(monkeypatch, {"celery"})
    s = _Svc()
    action = s.ping.xwaction
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    eng = CeleryActionEngine()
    eng._app = object()  # force non-fallback path
    res = eng.execute(action, ctx, s)
    assert res.success is True
    assert res.metadata.get("engine") == "celery"
    # when celery is missing, internal submit returns None
    assert res.data is None


def test_prefect_engine_execute_fallback_when_no_client():
    s = _Svc()
    action = s.ping.xwaction
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    eng = PrefectActionEngine()
    res = eng.execute(action, ctx, s)
    assert res.success is True
    assert res.data == "pong"


def test_prefect_engine_execute_main_path_when_client_present_even_if_prefect_missing(monkeypatch: pytest.MonkeyPatch):
    _block_imports(monkeypatch, {"prefect"})
    s = _Svc()
    action = s.ping.xwaction
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    eng = PrefectActionEngine()
    eng._client = object()  # force non-fallback path
    res = eng.execute(action, ctx, s)
    assert res.success is True
    assert res.metadata.get("engine") == "prefect"
    # when prefect is missing, internal flow creation returns None
    assert res.data is None


def test_engine_registry_registers_all_engines():
    action_engine_registry.register(NativeActionEngine())
    action_engine_registry.register(FastAPIActionEngine())
    action_engine_registry.register(CeleryActionEngine())
    action_engine_registry.register(PrefectActionEngine())
    assert action_engine_registry.get_engine("native") is not None
    assert action_engine_registry.get_engine("fastapi") is not None
    assert action_engine_registry.get_engine("celery") is not None
    assert action_engine_registry.get_engine("prefect") is not None


def test_action_executor_uses_registered_fastapi_engine_when_configured():
    # Register a configured FastAPI engine so executor can select it by name
    eng = FastAPIActionEngine()
    eng._app = object()
    action_engine_registry.register(eng)
    class Svc:
        @XWAction(engine="fastapi", profile="query", roles=["*"])
        def ping(self) -> str:
            return "pong"
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    res = s.ping.execute(ctx, s)
    assert res.success is True
    assert res.data == "pong"
    assert res.metadata.get("engine") == "fastapi"


def test_action_executor_can_route_to_celery_engine_when_registered(monkeypatch: pytest.MonkeyPatch):
    _block_imports(monkeypatch, {"celery"})
    eng = CeleryActionEngine()
    eng._app = object()  # force non-fallback path
    action_engine_registry.register(eng)
    class Svc:
        @XWAction(engine="celery", profile="task", roles=["*"])
        def ping(self) -> str:
            return "pong"
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    res = s.ping.execute(ctx, s)
    assert res.success is True
    assert res.metadata.get("engine") == "celery"
    assert res.data is None


def test_action_executor_can_route_to_prefect_engine_when_registered(monkeypatch: pytest.MonkeyPatch):
    _block_imports(monkeypatch, {"prefect"})
    eng = PrefectActionEngine()
    eng._client = object()  # force non-fallback path
    action_engine_registry.register(eng)
    class Svc:
        @XWAction(engine="prefect", profile="workflow", roles=["*"])
        def ping(self) -> str:
            return "pong"
    s = Svc()
    ctx = ActionContext(actor="u", source="t", metadata={"roles": ["*"]})
    res = s.ping.execute(ctx, s)
    assert res.success is True
    assert res.metadata.get("engine") == "prefect"
    assert res.data is None
