# exonware/xwaction/tests/1.unit/test_unit_fastapi_intypes_form_params_regression.py
"""
Regression: actions with ``Request`` + explicit ``Form(...)`` or ``Query(...)`` **and** ``in_types``
for the same names must register without ``ValueError: duplicate parameter name`` (GUIDE_51).

Previously the FastAPI engine treated ``Form``/``Query`` defaults like dependencies, set
``has_only_request``, then appended ``in_types`` fields again. OAuth/SAML-style callbacks use
this pattern.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Form, Query, Request
from fastapi.testclient import TestClient

from exonware.xwaction import XWAction
from exonware.xwaction.defs import ActionProfile
from exonware.xwaction.engines import action_engine_registry
from exonware.xwaction.engines.fastapi import FastAPIActionEngine

pytestmark = pytest.mark.xwaction_unit


@XWAction(
    operationId="regression_form_intypes_echo",
    summary="Echo SAML-style form fields",
    method="POST",
    engine="fastapi",
    profile=ActionProfile.ENDPOINT,
    in_types={
        "SAMLResponse": {"type": "string", "description": "SAML payload"},
        "RelayState": {"type": "string", "description": "Relay state"},
    },
)
async def saml_like_form_callback(
    request: Request,
    SAMLResponse: str | None = Form(default=None),
    RelayState: str | None = Form(default=None),
) -> dict[str, str | None]:
    return {"SAMLResponse": SAMLResponse, "RelayState": RelayState}


def test_fastapi_register_post_with_request_form_and_intypes_no_duplicate_params() -> None:
    """Registration succeeds; OpenAPI/signature must not duplicate Form field names."""
    app = FastAPI()
    eng = FastAPIActionEngine()
    action_engine_registry.register(eng)
    eng.setup({"app": app})
    ok = eng.register_action(saml_like_form_callback, app, path="/v1/auth/saml/callback", method="POST")
    assert ok is True

    with TestClient(app) as client:
        resp = client.post(
            "/v1/auth/saml/callback",
            data={"SAMLResponse": "abc", "RelayState": "rs"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("SAMLResponse") == "abc"
        assert body.get("RelayState") == "rs"


@XWAction(
    operationId="regression_query_intypes_echo",
    summary="Echo OAuth-style query params",
    method="GET",
    engine="fastapi",
    profile=ActionProfile.ENDPOINT,
    in_types={
        "code": {"type": "string", "description": "Auth code"},
        "state": {"type": "string", "description": "CSRF state"},
    },
)
async def oauth_like_query_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
) -> dict[str, str | None]:
    return {"code": code, "state": state}


def test_fastapi_register_get_with_request_query_and_intypes_no_duplicate_params() -> None:
    """Same dedupe rule as form fields: explicit ``Query`` must not collide with ``in_types``."""
    app = FastAPI()
    eng = FastAPIActionEngine()
    action_engine_registry.register(eng)
    eng.setup({"app": app})
    ok = eng.register_action(oauth_like_query_callback, app, path="/v1/auth/example/callback", method="GET")
    assert ok is True

    with TestClient(app) as client:
        resp = client.get("/v1/auth/example/callback", params={"code": "c1", "state": "s1"})
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") == "c1"
        assert body.get("state") == "s1"
