# xwaction — API Reference

**Library:** exonware-xwaction  
**Last Updated:** 07-Feb-2026  
**Requirements source:** [REF_01_REQ.md](REF_01_REQ.md) sec. 6, sec. 13

API reference for xwaction (output of GUIDE_15_API). See [REF_22_PROJECT.md](REF_22_PROJECT.md) and [REF_13_ARCH.md](REF_13_ARCH.md).

---

## Overview

- **Decorator and execution:** `@XWAction` decorator with profiles, engines, validation (xwschema), and pluggable handlers; call `fn()` or `fn.execute(context, **kwargs)`.
- **Multi-engine:** Same action runs via Native, FastAPI, Flask, Celery, or Prefect; OpenAPI 3.1 export.
- **For:** XW entity developers and advanced libraries; one function, many hosts (APIs, AI, commands).

---

## Quick Start (1–3 lines)

```python
from exonware.xwaction import XWAction, ActionContext

@XWAction(profile="query")
def my_action(x: int) -> int:
    return x * 2

# Call directly or with context
result = my_action(3)  # or my_action.execute(ActionContext(actor="user", source="cli"), x=3)
```

---

## Public Facades

### XWAction

- **Purpose:** Production-grade action decorator; smart inference, OpenAPI 3.1, security, workflow, validation (xwschema), pluggable engines and handlers.
- **Creation:** `@XWAction(...)` with optional: `operationId`, `api_name`, `summary`, `description`, `tags`, `profile`, `security`, `roles`, `rate_limit`, `audit`, `mfa_required`, `engine`, `handlers`, `readonly`, `idempotent`, `cache_ttl`, `background`, `timeout`, `method`, `retry`, `circuit_breaker`, `steps`, `monitor`, `rollback`, `contracts`, `in_types`, `out_types`, `responses`, `examples`, `deprecated`. See REF_01_REQ sec. 13.1.
- **Key methods:** `execute(context, instance, **kwargs)` → `ActionResult`; `to_openapi()` → dict; `to_native()` → dict; `from_native(data)` (classmethod) → action; `set_authorizer(authorizer)`; `check_permissions(context)` → bool.
- **Wrapper attributes:** `fn.xwaction`, `fn.execute`, `fn.api_name`, `fn.roles`, `fn.engines`, `fn.to_native`, `fn.in_types`.
- **Errors:** XWActionValidationError, XWActionSecurityError, XWActionPermissionError, XWActionExecutionError, XWActionWorkflowError, XWActionEngineError.

### ActionRegistry

- **Purpose:** Global registry; discovery by entity type, profile, tag; OpenAPI export; metrics.
- **Key methods:** `register(entity_type, action)`; `get_actions_for(entity_type)`; `get_actions_by_profile(profile)`; `get_actions_by_tag(tag)`; `get_security_schemes()`; `get_metrics()`; `export_all()`; `export_openapi_spec(title, version, description)`; `find_actions(entity_type, profile, tag, security_scheme, readonly, audit_enabled)`; `clear()`.

### ActionContext / ActionResult

- **ActionContext:** `ActionContext(actor, source, trace_id, metadata)`; `to_dict()`; `add_metadata`, `get_metadata`, `has_metadata`.
- **ActionResult:** `ActionResult.success(data, duration, **metadata)`, `ActionResult.failure(error, duration, **metadata)`; `success`, `data`, `error`, `duration`, `metadata`, `to_dict()`.

### Engines

- **Registry:** `action_engine_registry`; `ActionEngineRegistry` — register, get_engine, get_engines_by_type, select_engine, get_all_engines, enable_engine, disable_engine, clear.
- **Implementations:** `NativeActionEngine`, `FastAPIActionEngine`, `FlaskActionEngine`, `CeleryActionEngine`, `PrefectActionEngine` (Flask/Celery/Prefect optional).
- **Types:** `ActionEngineType` (EXECUTION, STORAGE, COMMUNICATION, PROCESSING); `ActionEngineConfig`.

### Handlers

- **Registry:** `action_handler_registry`; `ActionHandlerRegistry`.
- **Built-in:** `ValidationActionHandler`, `SecurityActionHandler`, `MonitoringActionHandler`, `WorkflowActionHandler`.
- **Phases:** `ActionHandlerPhase` (BEFORE, AFTER, ERROR, FINALLY).

### Discovery and serialization

- **extract_actions(obj)** — List of XWAction instances from a class or instance.
- **load_actions(obj, actions)** — Attach XWAction instances to an instance as callable methods.
- **XWAction.query(query_string, data, format, **kwargs)** — Execute via XWQuery when exonware-xwquery installed.

### Authorization

- **IActionAuthorizer** — `authorize(action, context)` → `AuthzDecision`.
- **AuthzDecision:** `allowed`, `reason`, `subject`, `scopes`, `roles`, `permissions`, `policy_id`.
- **Action:** `set_authorizer(authorizer)`, `check_permissions(context)`.

### Config and profiles

- **XWActionConfig**, **ProfileConfig**, **PROFILE_CONFIGS**; **get_profile_config(profile)**, **register_profile(name, config)**, **get_all_profiles()**.
- **Profiles:** ACTION, QUERY, COMMAND, TASK, WORKFLOW, ENDPOINT (defaults in REF_01_REQ sec. 13.4).

### Workflow visualization

- **WorkflowVisualizer.generate_graphviz(nodes, edges, title)** → Graphviz DOT string.
- **WorkflowNode**, **WorkflowEdge**.

### OpenAPI

- **openapi_generator.generate_spec(action)**; **OpenAPISpec**, **OpenAPIGenerator**.

---

## Configuration

- **XWActionConfig:** default_profile, auto_detect_profile, default_security, default_engine, default_handlers, enable_openapi, enable_metrics, enable_caching, cache_ttl, max_retry_attempts, default_timeout.
- **ProfileConfig:** readonly, cache_ttl, audit, background, rate_limit, security, retry_attempts, timeout, engine. Built-in PROFILE_CONFIGS per profile.

---

## Errors

| Error | Meaning | Next step |
|-------|---------|-----------|
| XWActionError | Base for all xwaction errors | Check details; subclass for specific handling. |
| XWActionValidationError | Input/output validation failed (xwschema) | Fix input or in_types/out_types; check issues in details. |
| XWActionSecurityError | Auth/authz/rate limit failed | Check security config, authorizer, roles. |
| XWActionPermissionError | User lacks permission | Set authorizer; ensure context has roles. |
| XWActionExecutionError | Action execution failed | Check original_error in details. |
| XWActionWorkflowError | Workflow step failed | Check workflow_step, step_number in details. |
| XWActionEngineError | Engine execution failed | Check engine_name, engine_type; ensure engine deps installed. |

---

## Not in public API (REF_01_REQ sec. 6)

- Executor/validator implementation details; debug wiring; engine/handler internals not meant for direct mutation.

---

## Compatibility & links

- **Python:** ≥3.12. Optional: Flask, Celery, Prefect, exonware-xwquery (see pyproject.toml).
- **Related:** [REF_01_REQ.md](REF_01_REQ.md), [REF_22_PROJECT.md](REF_22_PROJECT.md), [REF_13_ARCH.md](REF_13_ARCH.md), [GUIDE_01_USAGE.md](GUIDE_01_USAGE.md).

---

*Per GUIDE_00_MASTER and GUIDE_15_API.*
