# Architecture / trust boundaries

```text
Original take-home data (private) ─┐
                                   ├──> Inbound Pydantic validation ──> SQLite
New inbound UI -> POST /api/inbound┘                      │
                                                       identity matching
                                                       (email/LinkedIn only)
                                                               │
                           Agent A (rules-only | optional Gemini/Groq extraction)
                                                               │
                                    Pydantic schema + evidence quote checks
                                                               │
                              Agent B (deterministic policy, score & routing)
                                                               │
                             human Accept/Reject -> append-only decisions
                                                               │
                        server-side weekly KPI report + evidence drill-down

AI answer captures -> deterministic GEO scoring -> approved-context brief
```

- `apps/api/engine.py`: types, identity, normalization, domain rules, SQLite repository, KPI and decision audit.
- `apps/api/api.py`: HTTP boundary, provider adapter, input validation and error envelopes.
- `apps/api/geo.py`: snapshot analysis and BC/PP-only content brief.
- `apps/api/export_kpi.py`: renders authoritative SQLite KPI evidence as Markdown.
- `apps/web/src/App.tsx` + `main.tsx`: thin operator UI; no independent qualification or KPI arithmetic.
- `apps/api/tests/`: offline functional contracts and failure cases.

## Core contracts

**Extraction** (`Extraction` Pydantic schema): language, enumerated intent, buyer role, data problem, stated company facts, evidence quotes, injection flag, run mode. Untrusted model responses are rejected if any quote does not occur in the actual message. The original input is JSON data in a user message, never placed into system instructions.

**Qualification** (`Qualification` schema): 0–100 score with per-factor explanation, five boolean/evidence QL gates, valid status, routing owner, rationale, optional reply draft. Even if an LLM invents a priority or route, those fields are not accepted. A deterministic implementation produces them.

**Identity**: normalized email or LinkedIn `/in/{slug}` identifies a person; name, city, organization and domain never unify identities. Company information from a free email is never asserted. Self-reported facts are explicitly marked unverified.

**Safety**: `needs review` on extraction/provider errors or recognized prompt injection. Unsubscribe → `suppressed`, no outbound draft. Historical/real decisions persist; there is no message sending capability.

**Reporting**: fixed half-open interval `[2026-10-04T00:00+03:00, 2026-10-09T00:00+03:00)`, with timestamp conversion to `Asia/Jerusalem`. Unique person accepted during the period, with first touch attribution; pre-existing open deals and existing customers excluded from acquisition. Meetings/opportunities have their own occurred timestamps. Feed absence is `Unknown`.

## ADR-001 — Modular monolith
**Context:** single-operator take-home needs auditable cross-domain workflows, no distributed scale. **Decision:** Python API + isolated React UI + SQLite file. **Consequences:** simple setup and local consistency, intentionally not multi-tenant or internet-facing.

## ADR-002 — Deterministic qualification gate
**Context:** language models can hallucinate business facts and accept malicious instructions. **Decision:** LLM extracts only; business gates, routing, decisions and KPI are code-driven. **Consequences:** explicit rules and replayability; semantic fallback may produce false negatives.

## ADR-003 — Decision-time evidence and append-only audit
**Context:** a live Gemini re-run can reinterpret an inbound after sales accepted it; weekly KPIs must not change because an extractor failed or a prompt changed. **Decision:** store each analysis attempt in `analysis_history` and freeze evidence for an accepted decision in `decision_evidence`. Seed decisions migrate to rules-only snapshots from their original synthetic source messages. Operator decisions snapshot the latest successful, validated extraction available **at the time of acceptance**. The reporting engine uses only accepted snapshots, with the recorded first-touch source and historical acceptance clock. Explicit rejection in the reporting week still supersedes an acceptance. **Consequences:** historical replay is stable, but a new business decision is needed to reverse a false past acceptance. Blank/unavailable evidence never becomes a QL.

The latest recomputation is persisted in `meta.latest_kpi_pack`, and `/api/kpi/pack` exports the exact in-memory report as Markdown. The CRO note is generated from actual counts and the top GEO gap, never fixed numbers.

## ADR-004 — No outbound automation
**Context:** human-in-the-loop is explicit. **Decision:** draft text only, no email/CRM transports. **Consequences:** safe demo surface; no send button or credentials to real accounts.

## Known limitations

- Date-only CRM `open_deal_created` is interpreted at local midnight; same-day ordering is ambiguous and should be reconciled in a production CRM integration.
- The offline extraction is intentionally heuristic and weaker for unseen languages; production requires eval-set calibration and human correction.
- The no-auth local demo is not an appropriate internet deployment without access controls, rate limiting and privacy review.
- A new source without verified firmographics is held for review rather than inferred by brand name or email domain.

## Operator-supplied Gemini API key (local demo)

A key is pasted into a browser drawer, used only after an actual server-side connection test, and retained in React memory for this tab's lifetime. The browser sends it to local FastAPI in `X-Gemini-API-Key` on explicitly triggered operations. The server sends it as `x-goog-api-key` to Google's fixed `generateContent` host. The key is never included in URLs, persisted state, logs or test artifacts. This is a conscious single-operator local-demo trade-off, **not a production secret-management strategy**. Production systems should use server-side managed secrets and real authentication.

`api.py -> gemini.py -> Google` now provides three bounded flows: connection verification, schema-constrained Agent A extraction, and an approved-context GEO content plan. Only Gemini's extraction output enters deterministic `engine.assess()`; ungrounded evidence triggers a `needs review` failure. The GEO model chooses source IDs, headings and FAQ questions; the server composes all factual copy from the canonical `COMPANY_CLAIMS` set and rejects unknown source IDs. Existing stored decisions and KPI timestamps are unchanged. 


## ADR-005 — Shared SQLite connection and nonblocking LLM calls

FastAPI requests run concurrently, and SQLite cursors cannot share a connection unsynchronized. `Store` serializes logical database operations through a reentrant lock. Crucially, `analyze()` captures input state under the lock, releases the lock for the network-bound Gemini call, then re-acquires it to persist the result and append its immutable history entry. This keeps dashboard reads responsive during a 30-second LLM timeout. A single local process/single operator is in scope; multiple worker processes, WAL contention and large scale require a database designed for concurrent writers.

## ADR-006 — User-entered historical timestamps, audit and UI counts

React keeps `Received at` optional with browser-local semantics converted to an offset-bearing UTC timestamp; FastAPI rejects naive timestamps. Acceptance cannot predate the first inbound. The queue reports unique identities, inbound touches and current QLs separately; the KPI view reports the half-open reporting week based on decision-clock evidence, so Priya's later accepted status does not make her a QL inside Oct 4–8.

## ADR-007 — GEO claim/topic controls

Google selects editorial structure only. Factual paragraphs are concatenated from approved `COMPANY_CLAIMS`. Sections filter cited BC/PP IDs for topical relevance; numeric or absolute claims in generated headings are rejected before display. This guards the mismatch between invoice reconciliation and an unrelated AWB pilot. The offline 24-answer snapshot is not misrepresented as live search.
