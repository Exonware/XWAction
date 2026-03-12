# Project Reference — xwaction

**Library:** exonware-xwaction  
**Last Updated:** 07-Feb-2026  
**Requirements source:** [REF_01_REQ.md](REF_01_REQ.md)

Requirements and project status (output of GUIDE_22_PROJECT). Per REF_35_REVIEW.

---

## Vision (REF_01_REQ sec. 1)

xwaction is a **library and decorator** with multiple engines to execute actions; used for APIs, AI, commands, and xw entity / explaining actions. You supply code (W query, Python, or any code XWQuery supports) and it executes it. **One function** can be transported in a file, imported, and executed in any option (FastAPI, Flask, Telegram bot, etc.) without rewriting.

---

## Goals (REF_01_REQ sec. 1–2)

1. **Reuse XW data** for everything xwaction does.
2. **Use xwschema** for validation of parameters in/out.
3. **One function, many engines:** same action runs as native, FastAPI, Flask, Celery, Prefect (and future hosts).
4. **Explain and execute:** success = “I can explain any action and execute it”; easy DX and decorators.
5. **No reinvention:** do not implement what belongs in XWData, XWSchema, or XWQuery; avoid circular referencing.

---

## Success criteria (REF_01_REQ sec. 1)

- **6 mo / 1 yr:** Can explain any action and execute it; developer experience is easy; decorators are easy to use.
- **Primary users:** XW entity developers and advanced libraries.

---

## Scope (REF_01_REQ sec. 2)

| In scope | Out of scope |
|----------|--------------|
| Same features as today: OpenAPI, Flask, execution of queries, validation, engines, handlers, IActionAuthorizer, to_native/from_native, extract_actions/load_actions, WorkflowVisualizer, profile-based defaults. | Anything implemented in XWData, XWSchema, or XWQuery. |
| **Dependencies:** xwdata ([docs](../../xwdata/docs/INDEX.md)), xwschema, xwquery; authorization provider (future xwauth). | **Anti-goals:** Circular referencing. |

---

## Firebase Functions parity (backend replacement goal)

xwaction provides the **action/workflow execution layer** that maps to Firebase Functions in the ecosystem “backend replacement” goal:

- **Callable / HTTP-triggered:** xwaction callables and HTTP-triggered actions (e.g. via FastAPI or Flask engine) replace **Firebase Callable Functions** and **HTTP functions**; one decorated function can be exposed as an endpoint without rewriting.
- **Scheduled / event-driven:** Scheduled or event-driven flows align with **Firebase Functions triggers** (e.g. Pub/Sub, Firestore, Storage); the same action can be run by different engines (native, Celery, Prefect) for background or scheduled execution.
- **Auth/context:** IActionAuthorizer and ActionContext provide auth and request context analogous to Firebase request context; a future xwauth provider can supply identity and permissions.

This is vision/scope only; no new features required. Implementation details remain in REF_13_ARCH and REF_15_API.

---

## Functional Requirements (Summary)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-001 | Core workflow orchestration and action pipeline | High | Done |
| FR-002 | XWAction decorator and profiles (ACTION, QUERY, COMMAND, TASK, WORKFLOW, ENDPOINT) | High | Done |
| FR-003 | Input/output validation (xwschema), handlers (validation, security, monitoring, workflow) | High | Done |
| FR-004 | Engines: native, Flask, FastAPI, Celery, Prefect | High | Done |
| FR-005 | OpenAPI 3.1 generation (registry + per-action) | Medium | Done |
| FR-006 | 4-layer tests (0.core–3.advance) | High | Done |
| FR-007 | XWAction.query() (XWQuery integration when installed) | Medium | Done |
| FR-008 | IActionAuthorizer, set_authorizer, check_permissions | High | Done |
| FR-009 | to_native / from_native; extract_actions, load_actions | Medium | Done |
| FR-010 | ActionRegistry (register, find_actions, export_openapi_spec, export_all) | Medium | Done |
| FR-011 | WorkflowVisualizer, profile-based defaults | Low | Done |
| FR-012 | Script/query and context (REF_01_REQ sec. 14: XWAction.query context/language, action.script/execute, context default to parent self) | Medium | To implement |

---

## Non-Functional Requirements (REF_01_REQ sec. 8 — Five Priorities)

1. **Security:** Handlers (SecurityActionHandler, ValidationActionHandler); IActionAuthorizer; roles, rate_limit, audit, mfa_required; no unsafe execution from data.
2. **Usability:** Clear API; REF_22, usage docs; structured errors (XWAction*Error hierarchy); examples (authorization, actions_json).
3. **Maintainability:** Contracts/base/facade; REF_* and logs under docs/; 4-layer tests.
4. **Performance:** Monitoring and optimization tools; test_performance, test_security in 3.advance.
5. **Extensibility:** Pluggable engines and handlers; ActionEngineRegistry, ActionHandlerRegistry; optional engines and xwquery.

---

## Project Status Overview

- **Current phase:** Alpha (Medium). Aligns with **Version 0 (Experimental):** core workflow orchestration, action pipeline, input schema validation, workflow composition, error handling, performance monitoring, comprehensive tests, xwschema integration. Foundation complete; all M1–M3 deliverables done.
- **Docs:** REF_01_REQ (14/14, sec. 14 script/query requirements), REF_11_COMP, REF_12_IDEA, REF_13_ARCH, REF_14_DX, REF_15_API, REF_21_PLAN, REF_22_PROJECT (this file), REF_35_REVIEW, REF_51_TEST, REF_54_BENCH; logs under docs/logs/reviews/.
- **Traceability:** Requirements source REF_01_REQ; review evidence REF_35_REVIEW, logs/reviews/.

---

## BaaS (xwbase) capabilities (scope)

As part of the eXonware BaaS platform (xwbase), xwaction provides the execution layer for: real-time (WebSocket), serverless functions, scheduler/cron, hub/event bus, messaging/push, in-app messaging, interactions, and test lab. Persistence, event graph, and platform specifics are provided by xwstorage, xwnode, xwbots, xwchat, xwai; xwbase orchestrates. Details: [REF_13_ARCH.md](REF_13_ARCH.md#baas-xwbase-integration).

---

## Development principles

- **Phase transitions:** Each phase builds on the previous; no phase skipped (quality over speed); continuous integration; community feedback drives improvements.
- **Quality standards:** High test coverage (>95%), performance benchmarks per phase, security audit at milestones, documentation completeness, API stability guarantees.
- **Success metrics:** Performance improvements per phase, security vulnerability reduction, API adoption, enterprise satisfaction, Mars Standard compliance score.

---

## Milestones (REF_01_REQ sec. 9)

| Milestone | Target | Status |
|-----------|--------|--------|
| M1 — Core framework and pipelines | v0.x | Done |
| M2 — Engines and OpenAPI | v0.x | Done |
| M3 — REF_* and doc placement | v0.x | Done |
| Version 1 — Production ready | Q1 2026 | Planned |
| Version 2 — Mars Standard draft | Q2 2026 | Planned |
| Version 3 — RUST Core & Facades | Q3 2026 | Planned |
| Version 4 — Mars Standard implementation | Q4 2026 | Planned |

---

## Risks (REF_01_REQ sec. 10)

- **Top risks:** Circular dependencies (xwaction ↔ xwdata/xwschema/xwquery/xwauth); optional engine deps not installed; API drift when adding “explain any action” / AI/command use cases.
- **Assumptions:** Python 3.12+ and ecosystem packages available; one function runs across engines; xwschema/xwdata/xwquery own their domains; authorization pluggable (xwauth later).
- **Kill/pivot:** If we must duplicate xwdata/xwschema/xwquery logic; if circular refs cannot be resolved; if sponsor pivots away from “one function, many engines.”

---

## Traceability

- **Requirements source:** [REF_01_REQ.md](REF_01_REQ.md) (sections 1–10, 13, 14 script/query).
- **Compliance:** [REF_11_COMP.md](REF_11_COMP.md) | **Ideas:** [REF_12_IDEA.md](REF_12_IDEA.md) | **DX:** [REF_14_DX.md](REF_14_DX.md) | **API:** [REF_15_API.md](REF_15_API.md) | **Planning:** [REF_21_PLAN.md](REF_21_PLAN.md).
- **Review evidence:** [REF_35_REVIEW.md](REF_35_REVIEW.md), [logs/reviews/](logs/reviews/).

---

*See GUIDE_22_PROJECT.md for requirements process.*
