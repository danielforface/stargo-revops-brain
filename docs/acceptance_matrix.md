# Stargo Take-Home v2 — Requirements & Acceptance Matrix

**Source of truth:** `Stargo_RevOps_Engineer_Take_Home.md` and `data/ql_standard.md` from the **private** take-home pack. This document summarizes deliverables without copying employer records or credentials into the public repo.

| Requirement | Implementation | Evidence / how to verify | Remaining human check |
|---|---|---|---|
| Seed CRM, inbound, decisions, pipeline idempotently | `engine.Store.seed`, `scripts/import_take_home.py` | `tests/test_import.py`, `scripts/reviewer_smoke.py` | Run importer with original private ZIP |
| Paste new inbound, optional source and received time | React `App.tsx`, `operator.ts`, `POST /api/inbound` | `operator.test.ts`, `App.test.tsx`, API tests | Try with a previously unseen message |
| Normalize identity and domains | `email_norm`, `linkedin_norm`, `domain_norm`, `contact_for` | `test_engine.py` | Check LinkedIn duplicate and free Gmail case |
| Agent A structured extraction & schema validation | `Extraction`, `fallback_extract`, `gemini.extract` | `test_engine.py`, `test_gemini.py` | Try Hebrew and a live Gemini key |
| Agent B does not delegate QL, scoring or routing to model | `assess`, `Qualification`, source-evidence checks | `test_engine.py` | Inspect 5 gates for a borderline message |
| Provider invalid JSON, timeout, injection, offline mode | `Store.analyze`, Gemini transport error path | `test_gemini.py`, `test_decision_snapshots.py` | Turn off live provider and see `needs review` |
| Acceptance must be recorded; immutable as-of evidence | `decisions`, `decision_evidence`, `analysis_history` | `test_decision_snapshots.py` | Accept and re-analyze with bad provider |
| Fixed Israel week, unique QL, source, expansion, unknown | `engine.Store.kpi` | `test_engine.py`, private pack smoke | View two drill-downs |
| Source-traceable file and current CRO note | `export_kpi.py`, `/api/kpi/pack`, `KPI_PACK.md` | `test_decision_snapshots.py` | Export from fresh seed, then test data |
| GEO snapshot 24 captures and eight prompts | `geo.py` | `test_geo.py`, private smoke | Inspect lookalikes and wrong claims |
| Live LLM content brief with BC/PP facts only | `gemini.brief`, topic matching, editorial checks | `test_geo_semantics.py`, `test_gemini.py` | Use own key to generate two briefs |
| Persist all state across restart | SQLite `Store`, append-only decision and analysis history | `test_api.py`, `test_decision_snapshots.py` | Restart Python and Vite |
| React+TS readable at 390px, refined UI | `App.tsx`, responsive `style.css`, `main.tsx` | Vitest App+operator tests, Vite build | Open DevTools at width 390px |
| No outbound messaging, no CRM connection | API only returns reply drafts, no sending code | Code inspection, `SECURITY.md` | Confirm no real send action exists |
| No-key setup and reproducible tests | `.env.example`, README, Actions CI | Linux/Windows and frontend CI | Follow README without a key |
| AI coding workflow in first person | `PROCESS.md` | Source record provided as **draft** | Candidate must review and supply true hours |

## Honest boundaries

- Live Gemini is validated with mocks in CI; successful provider authorization and quota must be tested on the operator's machine. Recorded answer snapshots are *not* live searches of third-party answer engines.
- The candidate's local DB contains experimentation and must not be confused with a pristine exported KPI pack from the supplied source.
- No real HubSpot, email or LinkedIn service integration or automated reply delivery. Dry-run HubSpot bonus deliberately omitted because the assignment rewards depth on the core.
- No authenticated, internet-facing deployment or enterprise multi-tenant secret management. The single-user localhost demo is not suitable for handling third-party live PII without authorization.

## Readiness

Passing CI alone is not human acceptance. The author must review `PROCESS.md`, record honest hours and Gemini use, walk through two KPI numbers, perform one historical Accept/Reject and one forced provider failure in their local environment, and withhold any post-submission pushes unless disclosed to Stargo.


## New evidence after operator walkthrough

- Agent A now corroborates model company facts against **the original message** with explicit self-reported provenance, never CRM enrichment guesses (`gemini.extract`, `fallback_extract`).
- Agent B only passes Problem and Interest gates when each is grounded by a corresponding relevant quote in validated Agent A data (`assess`).
- New `test_live_firmographics.py` covers missing ICP data, unsupported counts/verticals, invented buyer roles/interest/problems, unsubscribe, immutable accepted evidence, restart, Hebrew and Dutch.
- Candidate should repeat live analysis using an authorized key and confirm current queue status separately from immutable historical KPI; no original source data or personal key is committed.
