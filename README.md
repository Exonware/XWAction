# xwaction

**Action-based workflow and automation.** Build, execute, and manage workflows with input validation, error handling, and performance monitoring. Integrates with xwschema for validation. Per project docs.

**Company:** eXonware.com · **Author:** eXonware Backend Team · **Email:** connect@exonware.com  
**Version:** See [version.py](src/exonware/xwaction/version.py) or PyPI. · **Updated:** See [version.py](src/exonware/xwaction/version.py) (`__date__`)

[![Status](https://img.shields.io/badge/status-beta-blue.svg)](https://exonware.com)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Install

```bash
pip install exonware-xwaction
```

---

## Quick start

```python
from exonware.xwaction import XWAction, ActionContext

@XWAction(profile="query")
def my_action(x: int) -> int:
    return x * 2

my_action(3)  # or my_action.execute(ActionContext(actor="user", source="cli"), x=3)
```

See [docs/](docs/) for pipelines, validation, and REF_* when present.

---

## What you get

| Area | What's in it |
|------|----------------|
| **Workflows** | Orchestration, action pipelines, error handling. |
| **Validation** | Schema-driven input validation (xwschema integration). |
| **Monitoring** | Performance tracking and optimization. |

---

## Docs and tests

- **Start:** [docs/INDEX.md](docs/INDEX.md) or [docs/](docs/).
- **Tests:** Run from project root per project layout.

---

## License and links

MIT - see [LICENSE](LICENSE). **Homepage:** https://exonware.com · **Repository:** https://github.com/exonware/xwaction  

Contributing → CONTRIBUTING.md · Security → SECURITY.md (when present).

*Built with ❤️ by eXonware.com - Revolutionizing Python Development Since 2025*
