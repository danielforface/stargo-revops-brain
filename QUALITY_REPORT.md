# Quality and review evidence — Stargo RevOps Brain

**Delivery type:** reviewable, single-operator localhost prototype. It is **not** an authenticated, hosted production application.

## Reproducible automated checks

The last verified baseline before this documentation-only presentation update was [main Actions run 44292678441](https://github.com/danielforface/stargo-revops-brain/actions/runs/44292678441), commit `1387cfd4169c2fabfe6d1f4ed421745dbb768e7d`. It completed **3/3 jobs successfully**. For newer commits, inspect the [live GitHub Actions history](https://github.com/danielforface/stargo-revops-brain/actions) rather than assuming old evidence applies to them.

| Gate | Baseline evidence |
| --- | --- |
| Backend — Linux, Python 3.12 | **84 tests passed**; compile and critical Ruff checks passed |
| Backend — Windows, Python 3.14 | **84 tests passed**; IANA timezone validation, compile and critical Ruff checks passed |
| Frontend — Node.js 22 | **10 Vitest tests passed**; TypeScript and Vite production build passed |

The test environment uses **independently synthetic fixtures** and **mocked LLM transport**. Automated success is not evidence that a live Gemini key was used in CI, nor a claim about large-scale production performance.

## Original source-pack verification — local operator report

A separate Windows run with the original private v2 source pack was reported by the project operator:

- **19** contacts, **20** valid inbound records, **11** Sales decisions, **12** pipeline events, **1** malformed inbound quarantined.
- Weekly baseline **6 Qualified Leads / 4 meetings booked / 3 meetings held / 2 opportunities**; `historical-reactivation` reported as **Unknown**, not zero.
- `python scripts/reviewer_smoke.py` validated the source baseline in a temporary SQLite file, including historical decision replay and failure cases; the existing working database was not modified by this smoke check.
- A live Gemini connection, grounded GEO brief and corrected five-gate qualification flow were also observed during local acceptance.

**Evidence classification matters:** those last four points are *operator-reported local observations*, not repeatable external API assertions by GitHub CI. Reviewers can reproduce the source-specific results using their own assignment ZIP and key if desired.

## Significant failure modes addressed

| Observed problem | Engineering response | Regression or evidence path |
| --- | --- | --- |
| Windows could not resolve `Asia/Jerusalem` | Add Windows `tzdata` and CI boot coverage | `test_timezone_portability.py`, Windows job |
| Concurrent dashboard reads returned HTTP 500 | Serialize shared SQLite operations; keep external model network wait outside DB lock | `test_concurrent_api.py`, API integration |
| Gemini key validation rejected a supported key form | Correct local validation and provider model handling | `test_gemini.py`, separate live operator check |
| Re-analysis could disturb accepted historical KPIs | Append analysis history and freeze evidence at Sales acceptance | `test_decision_snapshots.py` |
| Model omission of explicit company facts changed current qualification | Corroborate only text-supported, self-reported firmographics inside Agent A | `test_live_firmographics.py` |
| GEO brief cited an unrelated pilot or overstated a claim | Enforce claim-topic compatibility and safe editorial headings | `test_geo_semantics.py` |

## Deliberate boundaries

- Employer-provided synthetic source records are **not public in this repository**. Reviewers need the original ZIP for the reference KPI baseline.
- There is no real HubSpot/CRM synchronization, customer email sender, multi-tenant authorization, production secret vault or public deployment.
- The 24 GEO answers are an **offline recorded snapshot**; live Gemini is optional and cannot convert that snapshot into live measurements of three external engines.
- Human acceptance is required. A provider failure or prompt-injection text cannot autonomously create a Qualified Lead.
- A reviewer's own local Accept/Reject decisions can change the working database's KPI; the committed `KPI_PACK.md` represents the pristine source-pack export.

## Reviewer handoff and provenance

- [Setup and project scope](README.md)
- [Step-by-step reviewer guide](docs/REVIEWER_GUIDE.md)
- [Requirements ↔ evidence matrix](docs/acceptance_matrix.md)
- [Engineering process and AI collaboration disclosure](PROCESS.md)
- [KPI source evidence](KPI_PACK.md)
- [Architectural boundaries](ARCHITECTURE.md)
- [Full commit history](https://github.com/danielforface/stargo-revops-brain/commits/main)

The feature implementation and initial reviewer materials were merged through [PR #1](https://github.com/danielforface/stargo-revops-brain/pull/1). The original commits remain available for inspection. No private source ZIP or API key is intentionally included in the public repository.
