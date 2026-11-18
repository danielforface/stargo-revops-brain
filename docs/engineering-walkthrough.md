# Engineering walkthrough — independent code review preparation

The purpose of this file is to explain the code to a reviewer **without AI assistance**. It is a reading plan, not a substitute for understanding the implementation.

## Map of the system

1. `scripts/import_take_home.py` validates the original v2 ZIP and imports its six data files into `data/private/` (ignored by Git). `engine.Store.seed()` normalizes and persists contacts, inbound, decisions, pipeline, and feed completeness. The malformed `IN-019` is quarantined without crashing the import.
2. `apps/api/engine.py`: `Inbound` validates inputs, email and LinkedIn normalization identifies **people**, and `Store.ingest` writes to SQLite. Names or company domains never trigger identity merges.
3. `apps/api/gemini.py`: optional **live** model output is schema-validated and source quotes are checked verbatim. A deterministic reconciliation pass **inside Agent A** fills in only explicitly stated, corroborated self-reported firmographics. In offline mode, `fallback_extract` makes the source evidence deterministic and labels the mode accurately.
4. `engine.assess()` (Agent B) consumes validated extraction and CRM data for five gates, score **25+20+20+25+10**, exclusions, owner and a human-approval-only reply draft. The language model never assigns QL or owner.
5. `Store.decide()` writes an append-only decision with timestamp and identity; the accepted evidence is frozen in `decision_evidence`. An LLM failure later may move the **current** queue to `needs review` without rewriting the accepted historical KPI.
6. `Store.kpi()` applies the half-open **4–9 Oct 2026 Israel-local** window to accepted decisions and recorded pipeline events; existing customers and pre-existing deals are excluded from acquisition, expansion separated. `GET /api/kpi/pack` and `apps/api/export_kpi.py` share the same renderer, including the CRO note.
7. `geo.analyze_answers()` evaluates 24 **recorded** answer captures using a published gap formula. `gemini.brief()` generates a live editorial plan (or fallback template), checks claim-topic compatibility and builds factual copy from canonical approved BC/PP facts.
8. `apps/web/src/App.tsx` consumes server API results. React does not reimplement QL/KPI arithmetic; the UI shows distinct current queue, accepted-in-week and historic counts.

## Three evidence-backed cases to explain

- **Yossi (IN-011):** personal Gmail is not firmographic proof. The message explicitly states a 40-person customs brokerage in Haifa; those facts are labelled *self-reported*, not verified CRM. `SD-008` is the separate human Sales acceptance. Gemini may omit a fact, but source-grounded Agent A corroboration and frozen accepted evidence preserve consistent results.
- **Duplicate channel contact:** multiple inbound touches for one normalized email/LinkedIn identity contribute one unique lead and at most one QL by the first eligible accepted decision. Attribution follows the first touch.
- **Time zone edge:** `2026-10-08T21:30:00Z` is **2026-10-09T00:30:00+03:00**, outside the 4–8 October reporting week. Compare aware timestamps in `Asia/Jerusalem`, not string dates.

## Failure and security walkthrough

- Force an invalid extraction (`test_gemini.py`) and observe current `needs review`, not QL/disqualified. No automatic sender is implemented.
- Unsubscribe overrides owner and draft. Prompt-injection text cannot change the deterministic policies; discuss limitations of pattern-based detection.
- Explain why an API key is passed only through a loopback proxy in a header, why it is not stored, and why this is **not** sufficient for public deployment.
- Inspect the protected private source import, no-key fallback, and the `QUALITY_REPORT.md` distinction between CI mocks and actual operator Gemini verification.

## A safe small-change exercise

Add a new **explicitly supported** geographic mapping in `REGION_MAP`, write a synthetic unit test for a corresponding owner, and rerun `python -m pytest -q apps/api/tests`. Explain why unknown geographies must remain triage rather than being inferred from personal email domains. Do **not** change a production route or a synthetic employer decision simply to satisfy a demo.

Also practice explaining why immutable decision evidence is necessary and how you would migrate from single-user SQLite to a managed database in a real RevOps service.
