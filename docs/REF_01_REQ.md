# Requirements Reference (REF_01_REQ)

**Project:** xwaction  
**Sponsor:** ExonWare  
**Version:** 0.0.1  
**Last Updated:** 07-Feb-2026  
**Produced by:** [GUIDE_01_REQ.md](../../docs/guides/GUIDE_01_REQ.md)

---

## Purpose of This Document

This document is the **single source of raw and refined requirements** collected from the project sponsor and stakeholders. It is updated on every requirements-gathering run. When the **Clarity Checklist** (section 12) reaches the agreed threshold, use this content to fill REF_12_IDEA, REF_22_PROJECT, REF_13_ARCH, REF_14_DX, REF_15_API, and REF_21_PLAN (planning artifacts). Template structure: [GUIDE_01_REQ.md](../../docs/guides/GUIDE_01_REQ.md).

---

## 1. Vision and Goals

| Field | Content |
|-------|---------|
| One-sentence purpose | XWAction is a library and decorator with multiple engines to execute actions; used for APIs, AI, commands, and xw entity / explaining actions—you can supply code (W query, Python, or any code XWQuery supports) and it executes it. |
| Primary users/beneficiaries | XW entity developers and advanced libraries. |
| Success (6 mo / 1 yr) | I can explain any action and execute it; developer experience is easy; decorators are easy to use. |
| Top 3–5 goals (ordered) | (1) Reuse XW data for everything xwaction does. (2) Use xw schema for validation of parameters in/out. |
| Problem statement | Different models or platforms require changing functions every time (e.g. FastAPI vs Telegram bot vs Flask). I want one function that can be transported in a file, imported, and executed in any of those options. |

## 2. Scope and Boundaries

| In scope | Out of scope | Dependencies | Anti-goals |
|----------|--------------|--------------|------------|
| Same features as today: OpenAPI supported, Flask supported, execution of queries, validation, etc. | Anything already implemented in XWData, XWSchema, or XWQuery—do not reinvent the wheel. | xwdata, xwschema, xwquery; for authorization an authorization provider (in future xwauth as that provider). | Avoid circular referencing. |

## 3. Stakeholders and Sponsor

| Sponsor (name, role, final say) | Main stakeholders | External customers/partners | Doc consumers |
|----------------------------------|-------------------|-----------------------------|---------------|
| ExonWare (same as other projects). | Developers; product uses of the advanced libraries. | None for now; maybe in future Python sponsorship and showcase of this library. | Mostly developers and other users. |

## 4. Compliance and Standards

| Regulatory/standards | Security & privacy | Certifications/evidence |
|----------------------|--------------------|--------------------------|
| None in mind for now; this version stays like that; will review when we reach a version that requires MARS standard. | Developed with highest standards in mind; will review when version requires MARS standard. | Same as above—will review when version requires MARS standard. |

## 5. Product and User Experience

| Main user journeys/use cases | Developer persona & 1–3 line tasks | Usability/accessibility | UX/DX benchmarks |
|-----------------------------|------------------------------------|--------------------------|------------------|
| (From codebase.) Register action with @XWAction; run via native/Flask/FastAPI/Celery/Prefect; export OpenAPI 3.1; execute with validation and handlers (security, monitoring, workflow); XWAction.query() for XWQuery; extract_actions/load_actions; IActionAuthorizer; to_native/from_native; WorkflowVisualizer; profile-based defaults (QUERY, COMMAND, TASK, WORKFLOW, ENDPOINT). **Full list:** sec. 13. | XW entity / library developer: @XWAction(profile=…), call fn() or fn.execute(context, **kwargs); plug into any engine. | Clear errors (XWAction*Error hierarchy); REF_22, usage, examples (authorization, actions_json). | Same DX as other xw packages; decorator-based, minimal boilerplate. |

## 6. API and Surface Area

| Main entry points / "key code" | Easy (1–3 lines) vs advanced | Integration/existing APIs | Not in public API |
|--------------------------------|------------------------------|---------------------------|-------------------|
| **Full list in sec. 13.2.** Main: @XWAction (all params in sec. 13.1); .execute(context, **kwargs); ActionRegistry (register, get_actions_for, get_actions_by_profile/tag, find_actions, export_openapi_spec, export_all); action_engine_registry & ActionHandlerRegistry; all five engines; openapi_generator; extract_actions, load_actions; to_native, from_native; XWAction.query(); IActionAuthorizer, set_authorizer, check_permissions; WorkflowVisualizer; config (XWActionConfig, ProfileConfig, PROFILE_CONFIGS). | Easy: @XWAction() def fn(x): ...; fn(x) or fn.execute(**kwargs). Advanced: profiles, engines, handlers, in_types/out_types, security/roles/rate_limit/audit/mfa, OpenAPI, engine selection, from_native/load_actions. | xwschema, xwdata, xwquery (optional), xwsystem (sec. 13.3); FastAPI/Flask/Celery/Prefect; authorization provider (future xwauth). | Executor/validator internals; debug wiring; engine/handler implementation details. |

## 7. Architecture and Technology

| Required/forbidden tech | Preferred patterns | Scale & performance | Multi-language/platform |
|-------------------------|--------------------|----------------------|-------------------------|
| Python ≥3.12; exonware-xwsystem, xwschema, xwdata; FastAPI core; optional Flask/Celery/Prefect/xwquery. No forbidden stack stated. | Facade (XWAction); registry for engines and handlers; pipeline (validation → handlers before → permission → engine execute → handlers after); contracts (IAction, IActionEngine, IActionHandler, IActionAuthorizer). | Monitoring and optimization tools in codebase; no explicit SLAs in REF. | Python-only for current implementation; roadmap (REF_22/README) mentions Version 3 RUST Core & Facades later. |

## 8. Non-Functional Requirements (Five Priorities)

| Security | Usability | Maintainability | Performance | Extensibility |
|----------|-----------|-----------------|-------------|---------------|
| Handlers (SecurityActionHandler, ValidationActionHandler); IActionAuthorizer, check_permissions; no unsafe execution from data; roles, rate_limit, audit, mfa_required on decorator. | Clear API, REF_22/PROJECT_PHASES/docs; structured errors; examples. | Contracts/base/facade; REF_* and logs under docs/; 4-layer tests (0.core–3.advance). | Monitoring and optimization tools; tests include test_performance, test_security. | Pluggable engines and handlers; ActionEngineRegistry, ActionHandlerRegistry; optional engines (Flask/Celery/Prefect) and xwquery. |

## 9. Milestones and Timeline

| Major milestones | Definition of done (first) | Fixed vs flexible |
|------------------|----------------------------|-------------------|
| (From REF_22/README.) M1 Core framework and pipelines — Done. M2 Engines and OpenAPI — Done. M3 REF_* and doc placement — Done. Version 1 (Q1 2026) Production ready; Version 2 (Q2 2026) Mars Standard draft; Version 3 (Q3 2026) RUST Core & Facades; Version 4 (Q4 2026) Mars Standard implementation. | First milestone (M1) DoD: core workflow orchestration, action pipeline, decorator and profiles, validation and handlers, engine support. All done per REF_22. | Dates (Q1–Q4 2026) are targets; scope can be refined; avoid circular references and reinventing xwdata/xwschema/xwquery. |

## 10. Risks and Assumptions

| Top risks | Assumptions | Kill/pivot criteria |
|-----------|-------------|----------------------|
| Circular dependencies (xwaction ↔ xwdata/xwschema/xwquery/xwauth); optional engine deps (Flask/Celery/Prefect) not installed; API drift when adding “explain any action” / AI/command use cases. | Python 3.12+ and ecosystem packages available; one function runs across engines without rewriting; xwschema/xwdata/xwquery own their domains; authorization is pluggable (xwauth later). | If we must duplicate xwdata/xwschema/xwquery logic; if circular refs cannot be resolved; if sponsor pivots away from “one function, many engines” goal. |

## 11. Workshop / Session Log (Optional)

| Date | Type | Participants | Outcomes |
|------|------|---------------|----------|
| 07-Feb-2026 | Batch 1 — Vision and scope | Sponsor | Sections 1–2 filled; clarity 5/14. |
| 07-Feb-2026 | Batch 2 — Stakeholders and compliance | Sponsor | Sections 3–4 filled; clarity 7/14. |
| 07-Feb-2026 | Batch 3 — Product through risks | Sponsor + reverse‑engineer | Sections 5–10 filled from codebase (REF_22, README, facade, engines, handlers, tests, pyproject); clarity 14/14. |
| 07-Feb-2026 | Sponsor confirmation + full reverse‑engineer | Sponsor | Criterion 14 confirmed; section 13 added (full features and ecosystem integration from xwaction + xwdata/xwschema/xwquery/xwsystem). |
| 07-Feb-2026 | Downstream refresh (PROMPT_01_REQ_03_UPDATE) | Agent | REF_22_PROJECT, REF_13_ARCH, REF_15_API refreshed/created from REF_01_REQ; REF_35_REVIEW updated; REVIEW_164000_000_REQUIREMENTS.md written. |
| 07-Feb-2026 | Cont downstream (INDEX, REF_51, GUIDE_01_USAGE, README) | Agent | REF_51_TEST expanded (DoD, 4-layer); INDEX added REF_01_REQ, REF_13_ARCH, fixed _archive links; GUIDE_01_USAGE happy path + REF links; README docs section and PROJECT_PHASES link updated. |

## 12. Clarity Checklist

| # | Criterion | ☐ |
|---|-----------|---|
| 1 | Vision and one-sentence purpose filled and confirmed | ☑ |
| 2 | Primary users and success criteria defined | ☑ |
| 3 | Top 3–5 goals listed and ordered | ☑ |
| 4 | In-scope and out-of-scope clear | ☑ |
| 5 | Dependencies and anti-goals documented | ☑ |
| 6 | Sponsor and main stakeholders identified | ☑ |
| 7 | Compliance/standards stated or deferred | ☑ |
| 8 | Main user journeys / use cases listed | ☑ |
| 9 | API / "key code" expectations captured | ☑ |
| 10 | Architecture/technology constraints captured | ☑ |
| 11 | NFRs (Five Priorities) addressed | ☑ |
| 12 | Milestones and DoD for first milestone set | ☑ |
| 13 | Top risks and assumptions documented | ☑ |
| 14 | Sponsor confirmed vision, scope, priorities | ☑ |

**Clarity score:** 14 / 14. **Ready to fill downstream docs?** ☑ Yes

---

## 13. Features and Ecosystem Integration (Reverse-Engineered)

*Full inventory from xwaction codebase and ecosystem libraries (xwdata, xwschema, xwquery, xwsystem).*

### 13.1 XWAction decorator parameters (facade)

| Category | Parameters |
|----------|------------|
| Identity / OpenAPI | operationId, api_name, cmd_shortcut, summary, description, tags |
| Profiles & inference | profile (ACTION, QUERY, COMMAND, TASK, WORKFLOW, ENDPOINT), smart_mode |
| Security | security, roles, rate_limit, audit, mfa_required |
| Execution | engine, handlers, readonly, idempotent, cache_ttl, background, timeout, method (HTTP) |
| Resilience | retry, circuit_breaker |
| Workflow | steps, monitor, rollback |
| Validation | contracts, in_types (XWSchema), out_types (XWSchema) |
| OpenAPI / docs | responses, examples, deprecated; dependencies (FastAPI-style) |

### 13.2 Public API surface (key code)

- **Decorator & execution:** `XWAction`, `fn()` / `fn.execute(context, **kwargs)`, `wrapper.xwaction`, `wrapper.execute`, `wrapper.api_name`, `wrapper.roles`, `wrapper.engines`, `wrapper.to_native`, `wrapper.in_types`
- **Context & result:** `ActionContext(actor, source, trace_id, metadata)`, `ActionResult.success(data, duration, **metadata)`, `ActionResult.failure(error, duration, **metadata)`, `context.to_dict()`, `result.to_dict()`
- **Registry:** `ActionRegistry.register(entity_type, action)`, `get_actions_for(entity_type)`, `get_actions_by_profile(profile)`, `get_actions_by_tag(tag)`, `get_security_schemes()`, `get_metrics()`, `export_all()`, `export_openapi_spec(title, version, description)`, `find_actions(entity_type, profile, tag, security_scheme, readonly, audit_enabled)`, `clear()`
- **Engines:** `ActionEngineRegistry` (register, get_engine, get_engines_by_type, select_engine, get_all_engines, get_engine_configs, enable_engine, disable_engine, clear); `action_engine_registry`; `NativeActionEngine`, `FastAPIActionEngine`, `FlaskActionEngine`, `CeleryActionEngine`, `PrefectActionEngine`; `ActionEngineType` (EXECUTION, STORAGE, COMMUNICATION, PROCESSING); `ActionEngineConfig`
- **Handlers:** `ActionHandlerRegistry`; `action_handler_registry`; `ValidationActionHandler`, `SecurityActionHandler`, `MonitoringActionHandler`, `WorkflowActionHandler`; `ActionHandlerPhase` (BEFORE, AFTER, ERROR, FINALLY)
- **Config & profiles:** `XWActionConfig`, `ProfileConfig`, `PROFILE_CONFIGS`, `get_profile_config(profile)`, `register_profile(name, config)`, `get_all_profiles()`; `ValidationConfig`, `WorkflowStep`, `MonitoringConfig`, `SecurityConfig`, `ContractConfig`
- **OpenAPI:** `openapi_generator.generate_spec(action)`, `action.to_openapi()`, `OpenAPISpec`, `OpenAPIGenerator`
- **Serialization & discovery:** `action.to_native()`, `XWAction.from_native(data)`, `action.to_descriptor()`; `extract_actions(obj)`, `load_actions(obj, actions)`; `ActionRegistry.export_all()`, `ActionRegistry.export_openapi_spec()`
- **Query (xwquery):** `XWAction.query(query_string, data, format, **kwargs)` (delegates to XWQuery.execute when exonware-xwquery installed)
- **Authorization:** `IActionAuthorizer`, `AuthzDecision(allowed, reason, subject, scopes, roles, permissions, policy_id)`, `action.set_authorizer(authorizer)`, `action.check_permissions(context)`
- **Helpers:** `register_action_profile(name, config)`, `get_action_profiles()`, `create_smart_action(func, **overrides)`
- **Errors:** `XWActionError`, `XWActionValidationError`, `XWActionSecurityError`, `XWActionWorkflowError`, `XWActionEngineError`, `XWActionPermissionError`, `XWActionExecutionError`
- **Workflow visualization:** `WorkflowVisualizer.generate_graphviz(nodes, edges, title)`, `WorkflowNode`, `WorkflowEdge`
- **Version:** `__version__`, `get_version()`, `get_version_info()`, `get_version_dict()`, `is_dev_version()`, `is_release_version()`

### 13.3 Ecosystem integration (reuse, no reinvention)

| Library | Usage in xwaction |
|---------|--------------------|
| **xwschema** | `XWSchema`, `XWSchemaValidationError`; `in_types`/`out_types`; validation in core/validation and ValidationActionHandler; OpenAPI schema derivation from types. |
| **xwdata** | `XWData.from_native()`, `to_native()` in base (AAction), facade (to_native), workflow handler (workflow_state), Celery/Prefect engines (task payload serialization); IAction extends IData; actions as serializable nodes. |
| **xwquery** | Optional: `XWAction.query()` calls `XWQuery.execute(query_string, query_data, format, **kwargs)`; all XWQuery-supported formats (SQL, JSONPath, Cypher, etc.); optional dependency exonware-xwquery. |
| **xwsystem** | `get_logger()`, `XWObject` (facade base); serialization registry used in examples (actions_json load from JSON/YAML/TOML/XML). |

### 13.4 Use cases (from code and examples)

1. Decorate a function with `@XWAction(profile=..., engine=...)` and call it or `.execute(context, **kwargs)`.
2. Register actions with ActionRegistry; export OpenAPI 3.1 via `ActionRegistry.export_openapi_spec()` or per-action `to_openapi()`.
3. Run the same action via Native, FastAPI, Flask, Celery, or Prefect engine (engine selection by profile and registry).
4. Validate inputs/outputs with xwschema (`in_types`/`out_types`); run validation, security, monitoring, workflow handlers in pipeline.
5. Authorize via pluggable `IActionAuthorizer` (e.g. future xwauth); `check_permissions(context)` before execute.
6. Execute W query / XWQuery-supported code inside an action via `XWAction.query(query_string, data, format)`.
7. Discover actions on a class/instance with `extract_actions(obj)`; attach actions to an instance with `load_actions(instance, list_of_actions)`.
8. Serialize/deserialize actions: `to_native()`, `from_native(data)`; load from JSON/YAML/TOML/XML using xwsystem serialization (see examples/actions_json).
9. Build workflow graphs with `WorkflowVisualizer`, `WorkflowNode`, `WorkflowEdge`.
10. Profile-based defaults: QUERY (readonly, cache, rate_limit, api_key), COMMAND (audit, roles), TASK (background, celery, retry), WORKFLOW (prefect, oauth2), ENDPOINT (fastapi, oauth2).

---

## 14. Script and query requirements (XWAction.query / action.script)

*Authoritative source for script/query behavior and context handling (to implement).*

- **XWAction.query(code, context, language=...)** — Single entry point: runs either a **query** (declarative, e.g. `sql`, `xwqs`, `jsonpath`) or a **script** (imperative, e.g. `python`) on the given context. Query execution **MUST** reuse XWQuery; script execution runs code with `context` (and optionally `data`) in scope.
- **Instance API:** **action.script(code=..., context=..., language=...)** stores code, context, and language; **action.execute()** runs the stored query/script. When the action is bound to a parent object, **context defaults to that parent's `self`** if not provided.
- **Interaction with decorated code:** If XWAction has **no** decorated Python function, `action.script` code is used when `action.execute()` is called. If it has a decorated function, that function is the code and script-set code is not used for execution.

**Requirements checklist (to implement):**

| ID | Requirement | Status |
|----|-------------|--------|
| R1 | `XWAction.query(code, context, language=...)` runs query or script depending on `language`. | To implement |
| R2 | Query execution **MUST** reuse XWQuery (SQL, xwqs, JSONPath, etc.). | To implement |
| R3 | Script execution supports at least `language="python"` with `context` (and `data`) in scope. | To implement |
| R4 | `action.script(code=..., context=..., language=...)` stores code, context, and language on the action. | To implement |
| R5 | `action.execute()` runs the stored query/script using stored or default context. | To implement |
| R6 | When action is bound to a parent, **context defaults to parent's `self`** if not provided. | To implement |
| R7 | If XWAction has no decorated function, `action.script` code is used when `action.execute()` is called. | To implement |
| R8 | If XWAction has a decorated function, that function is the code; script-set code is not used. | To implement |

*References: XWQuery (query execution); current XWAction.query in facade (extend for context/language and script execution); XWEntity action definitions (context defaulting to entity data).*

---

## Traceability (downstream REFs)

- **REF_12_IDEA:** [REF_12_IDEA.md](REF_12_IDEA.md) — Idea context (sec. 1–2)
- **REF_22_PROJECT:** [REF_22_PROJECT.md](REF_22_PROJECT.md) — Vision, FR/NFR, milestones
- **REF_13_ARCH:** [REF_13_ARCH.md](REF_13_ARCH.md) — Architecture (sec. 7)
- **REF_14_DX:** [REF_14_DX.md](REF_14_DX.md) — Developer experience (sec. 5–6)
- **REF_15_API:** [REF_15_API.md](REF_15_API.md) — API reference (sec. 6, sec. 13)
- **REF_21_PLAN:** [REF_21_PLAN.md](REF_21_PLAN.md) — Milestones and roadmap (sec. 9)

---

*Per GUIDE_01_REQ. Collect thoroughly, then feed downstream REFs.*
