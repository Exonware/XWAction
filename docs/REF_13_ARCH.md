# Architecture Reference — xwaction

**Library:** exonware-xwaction  
**Last Updated:** 07-Feb-2026  
**Requirements source:** [REF_01_REQ.md](REF_01_REQ.md)

Per REF_01_REQ sec. 7, sec. 6, sec. 5. See [REF_22_PROJECT.md](REF_22_PROJECT.md) for project status.

---

## Overview

xwaction provides **action-based workflow and execution** with one function running across multiple engines (native, FastAPI, Flask, Celery, Prefect). **Reuse xwdata, xwschema, xwquery**—do not reinvent; avoid circular referencing. Facade (XWAction), registries (engines, handlers), and execution pipeline expose the public API.

---

## Required / forbidden tech (REF_01_REQ sec. 7)

- **Python ≥3.12.** Required: exonware-xwsystem, exonware-xwschema, exonware-xwdata; FastAPI core. Optional: Flask, Celery, Prefect, exonware-xwquery (lazy/full extras). No forbidden stack stated.

---

## Preferred patterns (REF_01_REQ sec. 7)

- **Facade (XWAction):** Single decorator entry; extends AAction, XWObject; delegates validation to xwschema, serialization to xwdata.
- **Registries:** ActionRegistry (actions by entity/profile/tag); ActionEngineRegistry (engines by type/priority); ActionHandlerRegistry (handlers by phase).
- **Pipeline:** validation → handlers BEFORE → permission check → engine execute → handlers AFTER; contracts IAction, IActionEngine, IActionHandler, IActionAuthorizer.
- **Reuse:** xwschema (in_types/out_types, validation), xwdata (to_native/from_native, workflow state, task payloads), xwquery (optional query execution), xwsystem (logging, XWObject, serialization registry).

---

## Boundaries

- **Public API:** REF_01_REQ sec. 6, sec. 13.2: XWAction, ActionRegistry, ActionContext, ActionResult, action_engine_registry, action_handler_registry, engines, handlers, config/profiles, extract_actions, load_actions, to_native, from_native, XWAction.query, IActionAuthorizer, WorkflowVisualizer, openapi_generator, errors. See [REF_15_API.md](REF_15_API.md).
- **Not public:** Executor/validator implementation details; debug wiring; engine/handler internals not meant for direct mutation.
- **Delegation:** xwdata (serialization, IData); xwschema (validation); xwquery (query execution when installed); authorization provider (future xwauth) via IActionAuthorizer.

---

## Scale and performance (REF_01_REQ sec. 7)

- Monitoring and optimization tools in codebase; no explicit SLAs in REF. Tests include test_performance, test_security in 3.advance.

---

## Multi-language / platform (REF_01_REQ sec. 7)

- Python-only for current implementation. Roadmap (REF_22): Version 3 RUST Core & Facades later; Version 2/4 Mars Standard.

---

## BaaS (xwbase) integration

xwaction provides the **action/workflow execution layer** for the eXonware BaaS platform (xwbase). Other components supply persistence, event graph, and platform integration; xwbase orchestrates.

| Capability | xwaction role | Provided by others |
|------------|----------------|---------------------|
| **Real-time (WebSocket)** | WebSocket infrastructure, connection lifecycle, event handling | Pub/sub backend: xwstorage (Redis, RabbitMQ); event graph: xwnode; orchestration: xwbase |
| **Serverless functions** | Function invocation, deployment, env vars, logs, background execution | NativeActionEngine, FastAPIActionEngine, CeleryActionEngine |
| **Scheduler / cron** | Task execution, cron parsing, one-time tasks, job workflow | Job persistence: xwstorage; distributed scheduling: xwbase |
| **Hub / event bus** | Event processing workflows, handler registration, event transformation | Event graph: xwnode; persistence: xwstorage; orchestration: xwbase |
| **Messaging / push** | Push notification workflows, message processing | Platform: xwbots (FCM, APNs); queue: xwstorage; preferences: xwauth |
| **In-app messaging** | Chat message processing, delivery, typing/read receipts | Chat: xwchat; persistence: xwstorage; xwbots; xwbase |
| **Interactions** | Interaction workflows, conversation flow and state | AI/conversation: xwai; platform: xwbots; xwbase |
| **Test lab** | Test execution workflows, runner lifecycle, result processing | Storage: xwstorage; test APIs: xwapi; orchestration: xwbase |

---

*See REF_01_REQ.md sec. 5–7. Review: REF_35_REVIEW.md.*
