# Engineering process and AI usage disclosure

**Project:** Stargo RevOps Brain · RevOps Engineer take-home · 18 November 2026  
**Submission:** [public repository](https://github.com/danielforface/stargo-revops-brain) · [reviewer walkthrough](docs/REVIEWER_GUIDE.md) · [test evidence](QUALITY_REPORT.md)  
**Working time:** approximately **5 hours of active work (08:00–13:00, Israel time)**. Final repository packaging and GitHub checks continued shortly afterward.

## Approach and engineering responsibility

I approached the assignment as a bounded, single-operator RevOps application rather than a production SaaS launch. The priorities were traceable inbound evidence, predictable lead qualification, explicit human Sales decisions, reproducible weekly KPIs, and honest separation of offline AI-visibility snapshots from live model-assisted content.

I specified a small, reviewable architecture: Python/FastAPI and Pydantic for API and validation, SQLite for local audit history, React/TypeScript for the operator interface, and an optional Gemini adapter. The core works without a paid API key. I directed the implementation toward measurable correctness, understandable failure handling, an accessible local reviewer workflow, and isolation of the original assignment data from the public repository.

**The critical boundary:** AI may extract structured facts from inbound messages and propose GEO editorial organization, but it cannot unilaterally assign Qualified Lead status, bypass exclusions, choose Sales acceptance, rewrite KPI arithmetic, send customer communications, or invent approved product facts. These decisions are enforced by code and/or recorded human action.

## AI assistance — explicit division of work

I used **ChatGPT (GPT-6) extensively as an engineering implementation assistant**. ChatGPT generated substantial portions of the Python backend, React frontend, tests, and documentation, and helped investigate defects and prepare CI workflows. This was not a manually typed, line-by-line implementation by me, and I do not represent it as one.

My contributions were task framing, setting architectural and privacy constraints, selecting the delivery scope, directing the AI implementation, running the application on my local Windows machine, identifying issues from actual behavior, supplying failure evidence, requesting corrections, evaluating the resulting behavior, and deciding which trade-offs and limitations to accept. The public Git history contains the implementation and subsequent corrections; it has not been rewritten to disguise tool usage.

**Google Gemini API** served a different role: it is an optional runtime provider for live Agent A extraction and grounded GEO brief structure. I used a user-entered key for local integration verification. The backend and frontend CI suite runs with mocked provider traffic, not live Gemini calls.

Using AI accelerated implementation; it did not make generated outputs authoritative. In particular, user-visible failures and incorrect evidence attribution led to changes, regression tests, and reruns of automated checks. The implementation should be assessed on its behavior, contracts, and traceability, with the collaboration model disclosed above.

## Engineering workflow and decisions

| Stage | Technical decision | Validation or evidence |
| --- | --- | --- |
| Define system boundaries | Keep a local modular monolith; separate data extraction from qualification and human approvals | [Architecture](ARCHITECTURE.md), [requirements matrix](docs/acceptance_matrix.md) |
| Establish a reproducible baseline | Import the employer-supplied synthetic ZIP locally; exclude source files and credentials from Git | Import script, independent synthetic fixtures, [reviewer smoke](scripts/reviewer_smoke.py) |
| Build the RevOps path | Normalize identities; preserve source quotes; qualify with five explicit gates; record Sales decisions | [Backend tests](apps/api/tests), [reviewer guide](docs/REVIEWER_GUIDE.md) |
| Make reporting auditable | Use acceptance-time evidence snapshots and correct reporting-week boundaries; keep missing feeds Unknown | [KPI pack](KPI_PACK.md), persistence and replay tests |
| Add GEO with provenance controls | Score the supplied 24 recorded answers; build optional Gemini briefs only from approved BC/PP facts | GEO tests, source-topic checks, visible quality notes |
| Verify across environments | Test API behavior, frontend interactions, critical lint/compile and production build | [Quality report](QUALITY_REPORT.md), [GitHub Actions](https://github.com/danielforface/stargo-revops-brain/actions) |

### Defects surfaced through local acceptance

The following are concrete examples of how observed behavior, rather than accepting a generated implementation at face value, changed the design:

1. **Windows time-zone startup:** the API failed because the IANA `Asia/Jerusalem` database was missing. The correction added `tzdata` and Windows CI coverage; I checked the next local startup and health response.
2. **Concurrent API failure:** the dashboard exposed `/api/kpi/week` HTTP 500 under concurrent requests. Investigation traced unsafe shared SQLite access; serialized database operations and dedicated concurrency checks were added.
3. **Gemini credentials:** an initially over-restrictive local validator rejected a valid AI Studio key before a network request. The validation flow was corrected and I tested the live connection again.
4. **Historical KPI integrity:** re-analysis could change a lead's current assessment without preserving the accepted evidence behind a prior KPI. The design now snapshots acceptance-time evidence and distinguishes current queue state from historical reporting.
5. **Omitted self-reported company facts:** Gemini missed explicit size, industry and location in a source message. A constrained corroboration pass inside **Agent A** now checks only what the original text supports, marking it self-reported rather than verified CRM data; Agent B still uses validated evidence to make deterministic decisions.
6. **GEO source mismatch:** a generated brief associated an unrelated pilot reference with an invoice topic. Source/topic matching and conservative headline handling were tightened rather than silently allowing an unsupported business claim.

My role in these episodes was to reproduce and report the relevant user-visible failure, provide context and steer the desired correction. ChatGPT assisted with root-cause analysis and generated the code/test changes. The automated tests and code history provide further evidence of the resulting system behavior.

## Verification and what the evidence does not prove

**Automated CI:** GitHub Actions runs backend tests on Linux and Windows, frontend Vitest tests, Python syntax/critical lint checks and a TypeScript/Vite production build. Provider transport is mocked. Passing CI validates the tested contracts; it does **not** establish enterprise-scale production readiness or prove a live model connection.

**Local acceptance (operator-reported):** I imported the original ZIP, started both services on Windows, inspected lead and KPI views, and ran `python scripts/reviewer_smoke.py`. The reference pack yielded 19 contacts, 20 valid inbound messages, 11 Sales decisions, 12 pipeline events and one rejected malformed inbound; the reporting week yielded **6 / 4 / 3 / 2** for QLs / meetings booked / meetings held / opportunities. I also tested the optional Gemini connection, a grounded GEO brief and a re-analysis where explicit firmographics were retained. These observations are separate from CI's mocked-provider checks.

**Reproducibility:** the repository deliberately excludes the six original synthetic employer files. Reviewers can use their own copy of the assignment ZIP to reproduce the source-specific baseline. The public CI fixtures are independently synthetic, not a substitute for the private source pack.

## Scope trade-offs and future hardening

A local, auditable demonstration made FastAPI + SQLite + React preferable to distributed services. No real HubSpot synchronization, live email or LinkedIn sending, public hosting, multi-tenant authentication, production secrets vault, or unrestricted autonomous Sales approval is implemented. The optional HubSpot dry-run was deprioritized in favor of a repeatable, tested core.

The 24 AI-engine answers are **recorded offline captures**, not a fresh live crawl of three external engines. Gemini supplies an optional editorial plan; factual brief content is reconstructed from approved claims and reviewed before publication. The browser-memory API key is appropriate only for this local demo. A production service would need server-managed credentials, authentication, tenant isolation, retention controls and production monitoring.

## Code-review handoff

For a technical walkthrough, I can trace an inbound record through identity matching and Agent A's validated extraction to Agent B's five gates, a human acceptance snapshot and one weekly KPI source row. I can also explain the boundaries and limitations of the Gemini path, where an injection attempt or provider error must never create a Qualified Lead, and how a new routing requirement should be tested.

The code, commits, test cases and documentation are provided to support an independent review of the resulting work and the disclosed AI-assisted development process.
