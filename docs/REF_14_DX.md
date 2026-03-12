# Developer Experience Reference — xwaction (REF_14_DX)

**Library:** exonware-xwaction  
**Last Updated:** 07-Feb-2026  
**Requirements source:** [REF_01_REQ.md](REF_01_REQ.md) sec. 5–6  
**Producing guide:** [GUIDE_14_DX.md](../../docs/guides/GUIDE_14_DX.md)

---

## Purpose

DX contract for xwaction: happy paths, "key code," and ergonomics. Filled from REF_01_REQ.

---

## Key code (1–3 lines)

| Task | Code |
|------|------|
| Define and call action | `@XWAction(profile="query")\ndef my_action(x: int): return x * 2` then `my_action(3)` |
| Execute with context | `my_action.execute(ActionContext(actor="user"), x=3)` |
| Register and run in engine | Register with FastAPI/Flask/Celery/Prefect; same function runs without rewriting. |

---

## Developer persona (from REF_01_REQ sec. 5)

XW entity / library developer: @XWAction(profile=…), call fn() or fn.execute(context, **kwargs); plug into any engine.

---

## Easy vs advanced

| Easy (1–3 lines) | Advanced |
|------------------|----------|
| @XWAction() def fn(x): ...; fn(x) or fn.execute(**kwargs) | Profiles, engines, handlers, in_types/out_types, security/roles/rate_limit/audit/mfa, OpenAPI, engine selection, from_native/load_actions. |

---

## Main entry points (from REF_01_REQ sec. 6, sec. 13)

- **Decorator:** @XWAction (operationId, api_name, summary, description, tags, profile, security, roles, rate_limit, audit, mfa_required, engine, handlers, etc.)
- **Execution:** .execute(context, **kwargs); ActionRegistry; action_engine_registry, action_handler_registry
- **Engines:** Native, FastAPI, Flask, Celery, Prefect
- **Integration:** extract_actions, load_actions; to_native, from_native; XWAction.query(); IActionAuthorizer; WorkflowVisualizer; openapi_generator

---

## Usability expectations (from REF_01_REQ sec. 8)

Clear API, REF_22/docs; structured errors (XWAction*Error); examples (authorization, actions_json).

---

- **Auth:** IActionAuthorizer, set_authorizer, check_permissions
- **Config:** XWActionConfig, ProfileConfig, PROFILE_CONFIGS
- **Viz:** WorkflowVisualizer

---

**Examples:** [examples/authorization_example.py](../examples/authorization_example.py), [examples/actions_json/](../examples/actions_json/) (see README there). The authorization example uses mock authorizers from `test_auth_helpers` (repo root) for demonstration; production code would use a real IActionAuthorizer (e.g. future xwauth).

---

*See [REF_01_REQ.md](REF_01_REQ.md), [REF_15_API.md](REF_15_API.md), [REF_21_PLAN.md](REF_21_PLAN.md). Per GUIDE_14_DX.*
