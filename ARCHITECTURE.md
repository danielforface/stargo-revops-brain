# Architecture / trust boundaries

```text
Original take-home data (private) ─┐
                                   ├──> Inbound Pydantic validation ──> SQLite
New inbound UI -> POST /api/inbound┘                      │
                                                       identity matching
                                                       (email/LinkedIn only)
                                                               │
                           Agent A (rules-only | optional Groq extraction)
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
- `apps/web/src/main.tsx`: thin operator UI; no independent qualification or KPI arithmetic.
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

## ADR-003 — Event/audit persistence
**Context:** decision timestamps determine historical reports. **Decision:** append decisions with `decided_at` and `recorded_at`, keep seed source IDs stable, derive KPI on request. **Consequences:** no cache invalidation ambiguity; read-time computation fine for small data.

## ADR-004 — No outbound automation
**Context:** human-in-the-loop is explicit. **Decision:** draft text only, no email/CRM transports. **Consequences:** safe demo surface; no send button or credentials to real accounts.

## Known limitations

- Date-only CRM `open_deal_created` is interpreted at local midnight; same-day ordering is ambiguous and should be reconciled in a production CRM integration.
- The offline extraction is intentionally heuristic and weaker for unseen languages; production requires eval-set calibration and human correction.
- The no-auth local demo is not an appropriate internet deployment without access controls, rate limiting and privacy review.
- A new source without verified firmographics is held for review rather than inferred by brand name or email domain.
