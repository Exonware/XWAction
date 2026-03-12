# xwaction - Benchmark / Performance Reference (REF_54_BENCH)

**Library:** exonware-xwaction  
**Last Updated:** 07-Feb-2026  
**Requirements source:** [REF_01_REQ.md](REF_01_REQ.md) sec. 8 (Performance)  
**Producing guide:** [GUIDE_54_BENCH.md](../../docs/guides/GUIDE_54_BENCH.md)

---

## Purpose

Performance stance and traceability for xwaction. There is **no standalone benchmark suite** or benchmark directory; performance is covered by the 4-layer test suite, specifically **3.advance** tests.

---

## Performance coverage

| Aspect | Location | Notes |
|--------|----------|--------|
| **Performance tests** | [tests/3.advance/test_performance.py](../../tests/3.advance/test_performance.py) | Action execution, registry, OpenAPI generation; run via `python tests/runner.py --performance` or `--advance`. |
| **Security tests** | tests/3.advance/test_security.py | Run via `python tests/runner.py --security` or `--advance`. |
| **Standalone benchmarks** | None | No `benchmarks/` directory; no REF_54 SLAs or benchmark runs. |

REF_01_REQ sec. 8 and REF_22 state: “Monitoring and optimization tools; test_performance, test_security in 3.advance.” This document records that performance is asserted via tests only; when release criteria require benchmark SLAs or a dedicated benchmark suite, add `benchmarks/` and extend this REF accordingly.

---

## Traceability

- **Requirements:** REF_01_REQ sec. 8 (Performance); REF_22 NFR-004.
- **Test runner:** [REF_51_TEST.md](REF_51_TEST.md) — Running tests includes `--advance`, `--performance`, `--security`.

---

*Per GUIDE_00_MASTER and GUIDE_54_BENCH.*
