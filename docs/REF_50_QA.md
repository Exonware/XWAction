# QA Reference — xwaction

**Library:** exonware-xwaction  
**Version:** See [`src/exonware/xwaction/version.py`](../src/exonware/xwaction/version.py) (`__version__`; single source of truth).  
**Last Updated:** Synchronized with project version module at doc maintenance time.  
**Requirements source:** [REF_01_REQ.md](REF_01_REQ.md) sec. 8 (Five Priorities)

---

## Purpose

Single source of truth for **xwaction** quality gates and release readiness (GUIDE_50_QA / GUIDE_00_MASTER).

---

## Readiness state (Go / No-Go)

| Gate | Requirement | Status | Evidence |
|------|-------------|--------|----------|
| Tests | All layers pass (0.core, 1.unit, 2.integration, 3.advance) | ✅ | [logs/tests/INDEX.md](logs/tests/INDEX.md) (newest `TEST_*_SUMMARY.md` after full `python tests/runner.py`) |
| Coverage | Overall ≥ 90% and core critical paths 100% | ⏳ | `REF_51_TEST.md` |
| Lint/Types | Formatting + type checks pass | ⏳ | CI / local `black`, `isort`, `mypy` |
| Security | Security suites pass; no known critical vulnerabilities | ⏳ | `REF_11_COMP.md` + advance security tests |
| Performance | Benchmarks meet SLA when applicable; no regressions | ⏳ | `REF_54_BENCH.md` (3.advance performance tests; no standalone bench tree) |
| Docs | Required REFs exist and are current | ⏳ | `docs/INDEX.md` |

**Decision:** ⏳ Pending (update table when gates are green)

---

## Quality gates (canonical)

### Gate 1 — Test execution
- No skipped/rigged tests; evidence under `docs/logs/tests/` from `tests/runner.py`

### Gate 2 — Coverage
- Target: ≥ 90% overall (per GUIDE_50_QA / project policy)

### Gate 3 — Code quality
- Lint and type-check clean per `pyproject.toml` tool config

### Gate 4 — Performance
- Per `REF_54_BENCH.md` when performance-sensitive paths change

### Gate 5 — Security
- Input validation and dependency posture per REF_11_COMP / REF_01_REQ

### Gate 6 — Optional `[full]` extra
- Opt-in; audit third-party packages before production use

---

## Required evidence locations

- Tests: `docs/logs/tests/TEST_*.md` + `docs/logs/tests/INDEX.md`
- Benchmarks: `REF_54_BENCH.md` (project policy: tests-only unless campaigns added at repo root)
- Releases: `docs/logs/releases/` + index when used
- Feedback: `docs/logs/feedback/` + index when used

**Release checklist:** Gates above define go/no-go. Update the readiness table when evidence moves from ⏳ to ✅.
