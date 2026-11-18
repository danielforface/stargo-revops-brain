# Changelog

## Unreleased

- Initial modular monolith with deterministic QL, audit decisions, traceable reporting, GEO snapshot, and local operator UI.
- Offline test suite and opt-in Groq extraction adapter.
- Repository governance, walkthrough and generated KPI pack.


## 2026-11-18 — Acceptance-time evidence hardening
- Add immutable `decision_evidence` and append-only `analysis_history` tables, plus seed migration.
- Make historical KPI independent of later re-analysis; keep explicit Rejections effective.
- Recompute and store KPI reports after human decisions; render dynamic CRO note.
- Release SQLite lock during outbound Gemini requests, while serializing DB operations.
- Add optional Received At in inbound UI, current-versus-historical reporting explanations and separate queue identity/event counts.
- Improve GEO semantic citation matching and include source-safety notes.
- Expand offline contracts and front-end reviewer journey tests.


## 2026-11-18 — Source-backed live Gemini firmographics

- Corroborate explicit size/industry/location in Agent A; do not promote unsupported model facts to Company Fit.
- Require separate relevant evidence for Agent B's Problem and Interest gates; preserve QL criteria and immutable decision snapshots.
- Add bounded Hebrew/Dutch/German phrases for self-reported business facts and owner roles.
- Show corroborated yet **unverified** firmographics in the lead detail, separately from CRM.
- Add synthetic Gemini omission, hallucination, prompt-safety, multilingual and historical replay tests.
