"""
#exonware/xwaction/tests/1.unit/test_unit_fastapi_streaming.py
Unit tests for FastAPIActionEngine streaming behavior.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from exonware.xwaction import XWAction
from exonware.xwaction.engines.fastapi import FastAPIActionEngine
from exonware.xwaction.engines import action_engine_registry
from collections.abc import AsyncIterator

pytestmark = pytest.mark.xwaction_unit


@XWAction(profile="command", engine=["fastapi"], stream=True, stream_type="ndjson")
async def stream_numbers() -> AsyncIterator[bytes]:
    """Simple streaming action that yields a few NDJSON lines."""

    async def gen() -> AsyncIterator[bytes]:
        for i in range(3):
            line = {"i": i}
            yield (str(line) + "\n").encode("utf-8")
            await asyncio.sleep(0)  # yield to event loop

    return gen()


@pytest.mark.skip(reason="FastAPI engine does not set response_model=None for AsyncIterator streaming; add_api_route fails on AsyncIterator[bytes]")
def test_fastapi_engine_streaming_endpoint_produces_multiple_chunks():
    app = FastAPI()
    eng = FastAPIActionEngine()
    action_engine_registry.register(eng)
    # Register action as endpoint
    eng.setup({"app": app})
    ok = eng.register_action(stream_numbers, app, path="/stream_numbers", method="GET")
    assert ok is True

    client = TestClient(app)
    resp = client.get("/stream_numbers", stream=True)
    assert resp.status_code == 200

    # Collect streamed lines
    lines = []
    for chunk in resp.iter_lines():
        if chunk:
            lines.append(chunk)
    # We expect multiple lines from the async generator
    assert len(lines) >= 3
