# xwaction — Usage Guide

**Last Updated:** 07-Feb-2026

How to use xwaction (output of GUIDE_41_DOCS). `xwaction` is the automation/workflow base for action execution across API, command/chat, and async task/workflow hosts. See [REF_01_REQ.md](REF_01_REQ.md), [REF_11_COMP.md](REF_11_COMP.md), [REF_22_PROJECT.md](REF_22_PROJECT.md), [REF_14_DX.md](REF_14_DX.md) (key code), [REF_15_API.md](REF_15_API.md), [REF_21_PLAN.md](REF_21_PLAN.md) (milestones). Full set: [INDEX.md](INDEX.md).

---

## Quick start (decorator-first)

One function, many hosts: decorate once, run as native call, FastAPI/Flask endpoint, Celery task, or Prefect flow.

```python
from exonware.xwaction import XWAction, ActionContext

@XWAction(profile="query")
def my_action(x: int) -> int:
    return x * 2

# Call directly
result = my_action(3)

# Or with context (e.g. for auth/audit)
ctx = ActionContext(actor="user", source="cli")
result = my_action.execute(ctx, x=3)
```

---

## Validation + OpenAPI metadata

Use `in_types` / `out_types` (XWSchema) for input/output validation and OpenAPI-ready operation metadata.

```python
from exonware.xwaction import XWAction
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
)
def create_invoice(customer_id: str, total: float):
    return {"invoice_id": "inv_001", "customer_id": customer_id, "total": total}
```

---

## Running under engines

- **Native:** call `fn(...)` or `fn.execute(context, **kwargs)`.
- **FastAPI / Flask:** register decorated actions as HTTP routes.
- **Celery / Prefect:** run the same action as background/orchestrated execution.
- **Event-driven use:** treat actions as event handlers for API requests, command/chat events, and internal automation triggers.
- **Query-in-context use:** run `xwquery` execution from inside an action using `XWAction.query(...)`.

```python
from fastapi import FastAPI
from exonware.xwaction import XWAction, extract_actions
from exonware.xwaction.engines.fastapi import FastAPIActionEngine

class UserActions:
    @XWAction(profile="endpoint", method="GET")
    def health(self):
        return {"ok": True}

app = FastAPI()
engine = FastAPIActionEngine()
engine.setup({"app": app})

for action in extract_actions(UserActions):
    engine.register_action(action, app, path=f"/users/{action.api_name}", method="GET")
```

---

## Query execution within action context (LLM/agent/server friendly)

`xwaction` supports executing queries from inside an action while still using action context, validation, and security hooks.

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

This pattern is useful for LLM/agent/server workflows because query execution can be wrapped with:
- action-level validation
- role/security checks
- monitoring/audit handler lifecycle

---

## Security, monitoring, workflow handlers

Attach handlers to apply cross-cutting concerns without rewriting business code.

```python
from exonware.xwaction import XWAction

@XWAction(
    profile="command",
    roles=["admin"],
    security="bearer",
    rate_limit="60/min",
    audit=True,
    rollback=True,
    handlers=["validation", "security", "monitoring", "workflow"],
)
def rotate_api_keys():
    return {"status": "rotated"}
```

---

## Bot/command-ready actions

Use `cmd_shortcut` metadata for chat/bot routing layers (for example in xwbots/xwchat integrations).

```python
from exonware.xwaction import XWAction, extract_actions

class BotCommands:
    @XWAction(profile="command", cmd_shortcut="price")
    def get_price(self, symbol: str):
        return {"symbol": symbol, "price": 123.45}

commands = {
    a.cmd_shortcut: a
    for a in extract_actions(BotCommands)
    if getattr(a, "cmd_shortcut", None)
}
```

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [REF_01_REQ.md](REF_01_REQ.md) | Requirements, vision, scope, full feature list (sec. 13) |
| [REF_12_IDEA.md](REF_12_IDEA.md) | Idea context and evaluation |
| [REF_22_PROJECT.md](REF_22_PROJECT.md) | Project vision, goals, FR/NFR, milestones |
| [REF_13_ARCH.md](REF_13_ARCH.md) | Architecture and boundaries |
| [REF_14_DX.md](REF_14_DX.md) | Developer experience and key code |
| [REF_15_API.md](REF_15_API.md) | Public API reference |
| [REF_21_PLAN.md](REF_21_PLAN.md) | Milestones and roadmap |
| [INDEX.md](INDEX.md) | Full REF set and navigation |
| [examples/README.md](../examples/README.md) | Examples index (authorization, actions_json) |

---

*Per GUIDE_00_MASTER and GUIDE_41_DOCS.*
