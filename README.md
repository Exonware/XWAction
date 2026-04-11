# xwaction

**Decorator-first automation and workflow foundation for real apps.** `xwaction` lets you define one function once, then run it as a native call, API endpoint, background task, workflow step, or bot/command action - with validation, security, monitoring, and OpenAPI-ready metadata built in.

**Company:** eXonware.com · **Author:** eXonware Backend Team · **Email:** connect@exonware.com  

[![Status](https://img.shields.io/badge/status-beta-blue.svg)](https://exonware.com)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

---

## 📦 Install

```bash
pip install exonware-xwaction
pip install exonware-xwaction[lazy]
pip install exonware-xwaction[full]
```

---

## 🚀 Quick start

```python
from exonware.xwaction import XWAction, ActionContext

@XWAction(profile="query")
def my_action(x: int) -> int:
    return x * 2

my_action(3)  # or my_action.execute(ActionContext(actor="user", source="cli"), x=3)
```

See [docs/](docs/) for pipelines, validation, and any `REF_*` files.

---

## 🧩 Engine and handler coverage

`xwaction` is not only a server decorator. The codebase includes:

- **Execution engines:** `native`, `fastapi`, `flask`, `celery`, `prefect`
- **Cross-cutting handlers:** `validation`, `security`, `monitoring`, `workflow`
- **OpenAPI generation:** per action (`to_openapi()`) and registry-level (`export_openapi_spec(...)`)
- **Authorization contract:** pluggable `IActionAuthorizer` + `AuthzDecision`
- **Action discovery/loading:** `extract_actions(...)`, `load_actions(...)` for class/instance action wiring
- **Event-driven execution style:** actions can be triggered by HTTP events, command/chat events, and async task/workflow execution paths
- **In-context query execution:** `XWAction.query(...)` lets actions run `xwquery` logic inside action workflows

---

## 🤖 Automation + event-driven positioning

- `xwaction` is the base layer for action automation across the eXonware stack.
- You can wire the same action into event sources (API requests, bot commands, internal triggers) without rewriting business logic.
- Handler phases (`BEFORE`, `AFTER`, `ERROR`, `FINALLY`) provide an event-style lifecycle around each action execution.
- Query-in-action support (`XWAction.query`) makes it a strong orchestration layer for LLM/agent/server scenarios where tool calls need controlled execution context.
- Validation + security + authorization hooks provide safer boundaries for agentic/server-side automation.

## ✨ What you get

| Area | What's in it |
|------|----------------|
| **Decorator-first DX** | Define once with `@XWAction`, execute directly or via engine adapters. |
| **Validation** | `xwschema`-backed input/output validation with caching and handler pipeline support. |
| **Security** | Role checks, pluggable authorizer, auth token hooks, rate-limit and audit flow support. |
| **Workflows** | Workflow state/checkpoints, rollback paths, and handler-driven orchestration. |
| **In-context queries** | Run query execution inside actions via `XWAction.query(...)` (powered by `xwquery`). |
| **Monitoring** | Per-action timing/error metrics, thresholds, and alert hooks. |
| **API docs** | OpenAPI operation metadata and full spec export from the registry. |
| **Multi-host** | Native function call, FastAPI/Flask endpoints, Celery tasks, Prefect flows. |

---

## 📘 Better developer examples

### 1) Action with schema validation + OpenAPI metadata

```python
from exonware.xwaction import XWAction, ActionContext
from exonware.xwschema import XWSchema

@XWAction(
    profile="endpoint",
    operationId="createInvoice",
    summary="Create invoice",
    tags=["billing"],
    in_types={
        "customer_id": XWSchema({"type": "string", "minLength": 3}),
        "total": XWSchema({"type": "number", "minimum": 0}),
    },
    out_types={
        "return": XWSchema({"type": "object"})
    },
)
def create_invoice(customer_id: str, total: float):
    return {"invoice_id": "inv_001", "customer_id": customer_id, "total": total}

ctx = ActionContext(actor="billing-service", source="internal")
result = create_invoice.execute(ctx, customer_id="cust_123", total=99.5)
openapi_operation = create_invoice.xwaction.to_openapi()
```

### 2) Expose class actions as FastAPI endpoints

```python
from fastapi import FastAPI
from exonware.xwaction import XWAction, extract_actions
from exonware.xwaction.engines.fastapi import FastAPIActionEngine

class UserActions:
    @XWAction(profile="endpoint", method="GET", summary="Health check")
    def health(self):
        return {"ok": True}

    @XWAction(profile="endpoint", method="POST", summary="Create user")
    def create_user(self, email: str):
        return {"id": "u_1", "email": email}

app = FastAPI()
engine = FastAPIActionEngine()
engine.setup({"app": app})

for action in extract_actions(UserActions):
    route = f"/users/{action.api_name}"
    method = "GET" if action.api_name == "health" else "POST"
    engine.register_action(action, app, path=route, method=method)
```

### 3) Security-focused action with custom authorizer

```python
from exonware.xwaction import XWAction, ActionContext, AuthzDecision

class RBACAuthorizer:
    def authorize(self, action, context):
        roles = context.metadata.get("roles", [])
        required = getattr(action, "roles", [])
        allowed = (not required) or any(r in roles for r in required)
        return AuthzDecision(allowed=allowed, reason="role_check", roles=roles)

@XWAction(
    profile="command",
    roles=["admin"],
    security="bearer",
    rate_limit="60/min",
    audit=True,
    handlers=["security", "monitoring"],
)
def rotate_api_keys():
    return {"status": "rotated"}

rotate_api_keys.xwaction.set_authorizer(RBACAuthorizer())
ctx = ActionContext(actor="ops-user", source="cli", metadata={"roles": ["admin"]})
result = rotate_api_keys.execute(ctx)
```

### 4) Command/chat style action metadata

```python
from exonware.xwaction import XWAction, extract_actions, ActionContext

class BotCommands:
    @XWAction(profile="command", cmd_shortcut="price")
    def get_price(self, symbol: str):
        return {"symbol": symbol, "price": 123.45}

bot = BotCommands()
commands = {
    a.cmd_shortcut: a
    for a in extract_actions(BotCommands)
    if getattr(a, "cmd_shortcut", None)
}

ctx = ActionContext(actor="telegram-user", source="chat")
result = commands["price"].execute(ctx, bot, symbol="XW")
```

### 5) Export one OpenAPI spec for all registered actions

```python
from exonware.xwaction import ActionRegistry

spec = ActionRegistry.export_openapi_spec(
    title="My Action API",
    version="1.0.0",
    description="Generated from registered @XWAction definitions",
)
```

### 6) Query execution inside action context

```python
from exonware.xwaction import XWAction, ActionContext

@XWAction(profile="query", handlers=["validation", "security"])
def find_high_value_users(data: dict):
    return XWAction.query(
        "SELECT * FROM users WHERE spend > 1000",
        data,
        format="sql",
    )

ctx = ActionContext(actor="agent-service", source="automation", metadata={"roles": ["analyst"]})
result = find_high_value_users.execute(ctx, data={"users": [...]})
```

---

## 🌐 Ecosystem functional contributions

`xwaction` is the orchestration layer; sibling XW libraries provide the typed contracts it executes against.
You can use `xwaction` standalone for decorator-based execution and engine adapters.
Additional XW integrations are optional and are primarily useful when building enterprise and mission-critical automation infrastructure under your own operational control.

| Supporting XW lib | What it provides to xwaction | Functional requirement it satisfies |
|------|----------------|----------------|
| **XWSchema** | Schema-backed input/output validation for actions and OpenAPI metadata generation. | Contract-safe action invocation and predictable payload validation. |
| **XWQuery** | Query execution surface callable from action context (`XWAction.query`). | In-action data retrieval/transform workflows without custom query adapters. |
| **XWSystem** | Shared runtime primitives (logging, errors, async/utilities, base object/contracts). | Engine-neutral action behavior and consistent operational semantics. |
| **XWAuth** | Authorization/token context integration for protected actions. | Enforceable security boundaries for command/endpoint automation paths. |
| **XWEntity** | Entity-bound action workflows over domain objects. | Domain-centric automation instead of function-only orchestration. |
| **XWAPI** | Endpoint hosting pattern and middleware ecosystem for action-exposed APIs. | Production API deployment for actions with standardized middleware/error handling. |

Competitive edge: action definitions stay portable across native calls, APIs, workers, and workflow engines because validation, query, and security contracts are provided by shared XW layers.

---

## 📖 Docs and tests

- **Start:** [docs/INDEX.md](docs/INDEX.md) or [docs/](docs/).
- **Tests:** From repo root, follow the project's test layout.

---

## 📜 License and links

Apache-2.0 - see [LICENSE](LICENSE). **Homepage:** https://exonware.com · **Repository:** https://github.com/exonware/xwaction  

## ⏱️ Async Support

<!-- async-support:start -->
- xwaction includes asynchronous execution paths in production code.
- Source validation: 15 async def definitions and 26 await usages under src/.
- Use async APIs for I/O-heavy or concurrent workloads to improve throughput and responsiveness.
<!-- async-support:end -->
Version: 0.9.0.11 | Updated: 11-Apr-2026

*Built with ❤️ by eXonware.com - Revolutionizing Python Development Since 2025*