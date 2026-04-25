#exonware/xwaction/src/exonware/xwaction/http_annotations.py
"""
HTTP framework injection typing helpers (OpenAPI-safe, no engine imports).

WHY: ``from __future__ import annotations`` and partial ``get_type_hints`` failures
would otherwise treat ``Request`` like ``Any`` and leak bogus ``request`` fields into
OpenAPI; engines and ``XWAction`` auto-``in_types`` use this module without importing
heavy engine packages from ``facade``.
"""

from __future__ import annotations

import inspect
from typing import Any, Union, get_args, get_origin

try:
    from types import UnionType as _UnionType  # Python 3.10+
except ImportError:  # pragma: no cover
    _UnionType = None  # type: ignore[misc, assignment]

try:
    from typing import Annotated
except ImportError:  # pragma: no cover
    Annotated = None  # type: ignore[misc, assignment]


def unwrap_annotation_for_openapi(annotation: Any) -> Any:
    """
    Strip Annotated / optional unions so engines can recognize Starlette/FastAPI
    injection types even when callers wrap them for DI.
    """
    if annotation is None or annotation is inspect.Parameter.empty:
        return annotation
    if Annotated is not None:
        origin = get_origin(annotation)
        if origin is Annotated:
            args = get_args(annotation) or ()
            return unwrap_annotation_for_openapi(args[0]) if args else annotation
    origin = get_origin(annotation)
    if origin is Union or (_UnionType is not None and origin is _UnionType):
        args = [a for a in (get_args(annotation) or ()) if a is not type(None)]
        if len(args) == 1:
            return unwrap_annotation_for_openapi(args[0])
    return annotation


def is_http_framework_injection_type(annotation: Any) -> bool:
    """True for Starlette/FastAPI request/response lifecycle parameters (not API fields)."""
    ann = unwrap_annotation_for_openapi(annotation)
    if ann is None or ann is inspect.Parameter.empty:
        return False
    mod = getattr(ann, "__module__", "") or ""
    name = getattr(ann, "__name__", "") or ""
    targets = {
        ("starlette.requests", "Request"),
        ("fastapi.requests", "Request"),
        ("starlette.responses", "Response"),
        ("starlette.responses", "StreamingResponse"),
        ("fastapi.responses", "Response"),
        ("starlette.websockets", "WebSocket"),
        ("starlette.background", "BackgroundTasks"),
        ("fastapi.background", "BackgroundTasks"),
    }
    if (mod, name) in targets:
        return True
    if name == "Request" and mod.endswith("requests"):
        return True
    if name in ("Response", "StreamingResponse") and mod.endswith("responses"):
        return True
    if name == "WebSocket" and mod.endswith("websockets"):
        return True
    if name == "BackgroundTasks" and "background" in mod:
        return True
    return False
