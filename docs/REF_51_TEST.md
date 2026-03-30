# xwaction - Test Status and Coverage

**Last Updated:** 07-Feb-2026  
**Requirements source:** [REF_01_REQ.md](REF_01_REQ.md) sec. 9, [REF_22_PROJECT.md](REF_22_PROJECT.md)

Test status and coverage (output of GUIDE_51_TEST). Evidence: repo `tests/`, docs/logs/.

---

## Definition of done (REF_01_REQ sec. 9)

First milestone (M1) DoD: core workflow orchestration, action pipeline, decorator and profiles, validation and handlers, engine support. **All done** per REF_22. Test expectation: 4-layer test suite (0.core–3.advance) in place and passing.

---

## Test layers

| Layer | Path | Purpose |
|-------|------|---------|
| 0.core | tests/0.core/ | Core imports, facade, action utilities, wrapper vs execute |
| 1.unit | tests/1.unit/ | Config, context, engine registry, handlers, OpenAPI, validation contracts, registry filters |
| 2.integration | tests/2.integration/ | Built-in handlers, engines coverage, execution pipeline, Flask engine, registry/OpenAPI export, workflow handler state |
| 3.advance | tests/3.advance/ | OpenAPI compliance, performance, security |

---

## Running tests

```bash
python tests/runner.py
python tests/runner.py --core
python tests/runner.py --unit
python tests/runner.py --integration
python tests/runner.py --advance
python tests/runner.py --security
python tests/runner.py --performance
```

---

## Evidence

- **Location:** `tests/` (suite), `docs/logs/tests/` (`TEST_*_SUMMARY.md`, [INDEX.md](logs/tests/INDEX.md)), `docs/logs/reviews/` (review evidence).
- **Traceability:** REF_22 FR-006 (4-layer tests); REF_01_REQ sec. 8 Maintainability (test coverage, structure)

---

*Per GUIDE_00_MASTER and GUIDE_51_TEST.*
