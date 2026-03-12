# xwaction — Usage Guide

**Last Updated:** 07-Feb-2026

How to use xwaction (output of GUIDE_41_DOCS). See [REF_01_REQ.md](REF_01_REQ.md), [REF_11_COMP.md](REF_11_COMP.md), [REF_22_PROJECT.md](REF_22_PROJECT.md), [REF_14_DX.md](REF_14_DX.md) (key code), [REF_15_API.md](REF_15_API.md), [REF_21_PLAN.md](REF_21_PLAN.md) (milestones). Full set: [INDEX.md](INDEX.md).

---

## Quick start (REF_01_REQ sec. 5–6)

One function, many engines: decorate once, run as native call, FastAPI, Flask, Celery, or Prefect.

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

## With validation (xwschema)

Use `in_types` / `out_types` (XWSchema) for input/output validation. See [REF_15_API.md](REF_15_API.md) for decorator parameters and [REF_01_REQ.md](REF_01_REQ.md) sec. 13.1.

---

## Running under an engine

- **Native:** call `fn(...)` or `fn.execute(context, **kwargs)`.
- **FastAPI / Flask / Celery / Prefect:** register the action with the corresponding engine; same function runs without rewriting. See examples and [REF_13_ARCH.md](REF_13_ARCH.md).

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
