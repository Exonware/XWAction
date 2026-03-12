# Review: Archive extraction — value merged to REFs and logs

**Date:** 07-Feb-2026  
**Artifact type:** Review (docs standard cleanup)  
**Scope:** xwaction docs/_archive — extract value into REF_* and logs; remove redundant files  
**Standard:** GUIDE_41_DOCS; only REF_*, INDEX, GUIDE_01_USAGE at docs root; evidence in logs.

---

## Summary

**Outcome:** Pass. Both files previously in `docs/_archive/` were reviewed; their added value was merged into REF_01_REQ, REF_22_PROJECT, REF_13_ARCH, and REF_21_PLAN. A new FR (FR-012) and REF_01_REQ sec. 14 capture script/query requirements. BaaS integration and development principles are in REF_22 and REF_13. Version 0 (Experimental) is explicit in REF_21 roadmap. Original archive files were removed; no content was discarded without placement.

---

## 1. Archive contents reviewed

| File | Purpose | Value extracted to |
|------|---------|---------------------|
| **PROJECT_PHASES.md** | 5-phase roadmap (V0–V4), BaaS capabilities, development principles, get-involved | REF_22_PROJECT (Version 0 status, BaaS scope, development principles); REF_13_ARCH (BaaS/xwbase integration table); REF_21_PLAN (Version 0 row in roadmap) |
| **REQUIREMENTS_SCRIPT_AND_QUERY.md** | Authoritative script/query and context requirements (XWAction.query, action.script/execute, R1–R8) | REF_01_REQ sec. 14 (full checklist and conceptual model); REF_22 FR-012 (traceability to sec. 14) |

---

## 2. Changes made to REFs

- **REF_01_REQ:** Added **sec. 14 Script and query requirements** (conceptual model, static/instance API, interaction with decorated code, R1–R8 checklist, references to XWQuery and facade).
- **REF_22_PROJECT:** Project status overview updated to align current phase with Version 0 (Experimental) and key deliverables; added **BaaS (xwbase) capabilities** subsection (summary + link to REF_13); added **Development principles** subsection; added **FR-012** (script/query and context, to implement, ref REF_01_REQ sec. 14).
- **REF_13_ARCH:** Added **BaaS (xwbase) integration** section with table (capability, xwaction role, provided by others) for WebSocket, serverless, scheduler, hub/event bus, messaging, in-app messaging, interactions, test lab.
- **REF_21_PLAN:** Added **v0 (Experimental)** row to roadmap table (current; M1–M3 done).

---

## 3. Archive disposition

- **PROJECT_PHASES.md** — Deleted from `docs/_archive/` after value merged to REF_22, REF_13, REF_21.
- **REQUIREMENTS_SCRIPT_AND_QUERY.md** — Deleted from `docs/_archive/` after value merged to REF_01_REQ sec. 14 and REF_22 FR-012.

No other files were in xwaction `_archive`. `_archive/` folder remains for future non-standard doc placement per GUIDE_41_DOCS.

---

## 4. Traceability

- **Requirements:** [REF_01_REQ.md](../../REF_01_REQ.md) sec. 14
- **Project / roadmap:** [REF_22_PROJECT.md](../../REF_22_PROJECT.md), [REF_21_PLAN.md](../../REF_21_PLAN.md)
- **Architecture:** [REF_13_ARCH.md](../../REF_13_ARCH.md#baas-xwbase-integration)
- **Docs standard:** GUIDE_41_DOCS; INDEX.md, logs/reviews/

---

*Per GUIDE_41_DOCS. Archive cleared 07-Feb-2026; value preserved in REFs and this review log.*
