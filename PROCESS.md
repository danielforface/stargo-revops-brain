# PROCESS — How I used AI-assisted engineering

> **Author review required before submission.** I prepared this narrative with AI assistance; before emailing it I need to read and own every first-person statement, make any necessary corrections, and report my **actual total hours** in my reply. I have not represented generated code as code I typed myself.

## Goal, constraints and plan

I received a Stargo RevOps Engineer take-home focused on a qualified inbound queue, two chained agents, trustworthy weekly KPIs, and a GEO/LLM-SEO snapshot. I prioritized **correctness, auditable evidence, offline reproducibility and privacy** over additional integrations. I set up the public GitHub repository and supplied the original v2 task ZIP to ChatGPT (GPT-6) as my engineering assistant, with a detailed directive emphasizing production-minded design, predictable task ownership, testing and source confidentiality.

The core architecture I requested was intentionally small: Python/FastAPI for HTTP, Pydantic contracts, SQLite for durable state, React/TypeScript for the operator UI, and a fixed-host optional LLM adapter. The model may interpret inbound text but it does **not** own the five QL gates, exclusions, KPI arithmetic, Sales acceptance, routing, or outbound communication. I asked for a rules-only path that needs **no API key**. I also asked to keep the original source data out of the public Git history and to build tests with independent synthetic examples.

## What I delegated to the assistant, and what I controlled

I used ChatGPT to inspect the assignment and source pack, implement most of the Python/React code, draft architecture and reviewer documentation, create automated tests and run GitHub Actions checks. I reviewed the user-facing behavior and gave corrections based on real local results rather than accepting generated code on the strength of a description.

Representative steering instructions I gave included: making the repository understandable to other developers, designing a complete professional submission rather than isolated scripts, using a Gemini API key entered through the frontend instead of requiring a paid or hardcoded key, and keeping the user interface restrained and responsive. I insisted that the assistant complete the substantial engineering work before asking me for local verification steps.

I did **not** manually author every file, and I do not claim that I did. The AI-assisted code, tests and documents are visible in the Git history. My own contribution includes task framing, constraints, architecture priorities, real-world validation, defect reports and the review/decision to use the resulting design. The code walkthrough must be done by me without an AI assistant.

## Where verification changed the design

1. **Server boot on Windows.** My first local start failed because `ZoneInfo('Asia/Jerusalem')` did not find IANA timezone data. I shared the Python traceback. The assistant added a Windows-specific `tzdata` dependency and a Windows/Python 3.14 CI job. I re-ran the server and received a healthy seed response.
2. **Concurrent dashboard HTTP 500.** The React frontend surfaced `Unexpected token 'I'`, while the browser showed `/api/kpi/week` returning 500. This exposed a shared SQLite connection used across FastAPI request threads. The assistant added serialized database operations, regression tests, and non-JSON API error handling; the API recovered.
3. **Gemini key compatibility.** I requested live Gemini through a browser-entered key and tested actual Google AI Studio keys. The initial local key validator rejected modern `AQ.` credentials before any network call. The assistant updated credential validation and the supported model list, and I later observed successful `/api/ai/verify` and live GEO generation.
4. **Historical QL integrity.** A lead with an original Sales acceptance was displayed as `needs review` after newer extraction. An LLM response was effectively changing the visible evidence behind a historical KPI. The assistant added immutable acceptance-time evidence snapshots, an additive SQLite migration, replay tests and a current-status-versus-historical-KPI distinction.
5. **Gemini omission of source facts.** In the local Yossi Mizrahi detail, the model understood buyer role and manual document work but omitted an explicitly stated team size, vertical and city, incorrectly weakening current qualification. I supplied the full UI evidence. The assistant added a deterministic corroboration pass *inside Agent A* for explicitly stated, self-reported firmographics; I then observed all five QL conditions, score 100, correct owner and unchanged historical KPI.
6. **GEO evidence quality.** A live Gemini brief linked an unrelated air-waybill pilot to an invoice-reconciliation paragraph and later used an overly broad compliance heading. The assistant implemented topic-matched source IDs, visible safety notes and conservative canonical headline replacement rather than silently publishing unsupported claims.

I deliberately treated these defects as evidence to investigate, not as reasons to hide tests or inflate metrics. Generated patches were followed by source review, regressions and repeat CI runs.

## Automated vs personal verification

The repository's test suite uses **mocked LLM transport** so CI does not consume keys or assume Internet access to Google. It covers identity normalization, schema validation, prompt injection, suppression, time-zone boundaries, unique-count KPIs, historical decisions, SQLite replay/migration, concurrent API behavior, GEO claim grounding, and React interactions. The CI run and its exact commit are linked in `QUALITY_REPORT.md`.

On my local Windows machine I imported the original pack, ran the backend and frontend, inspected the three screens and lead detail, used the Gemini connection workflow, and ran `python scripts/reviewer_smoke.py`. Its output confirmed 19/20/11/12/1 source counts and 6/4/3/2 weekly KPIs. I observed successful live Gemini verification, a live GEO content brief and the subsequent five-gate QL analysis after the source-firmographic correction. A live model acceptance test is **separate** from the mocked CI tests.

## Technical trade-offs and what I cut

I favored a readable modular monolith over microservices and a message queue. SQLite is suitable for the local single-operator workflow, but not a scalable, authenticated multi-tenant service. No actual HubSpot/CRM synchronization, live emails, social messaging, externally hosted deployment, automated human approval or generic paid-model requirement was built. The optional HubSpot dry-run was cut because the assignment favors robust core semantics. A small synthetic qualifier eval was added as a narrower optional exercise.

The recorded answer set supports offline snapshot analysis. I did **not** claim to have queried all three external answer engines live. Live Gemini generates GEO *editorial structure*; the factual body uses approved BC/PP statements so source provenance remains auditable. An API key in browser tab memory through a localhost proxy is a review/demo convenience; I would replace it with authenticated server-side secret management for production.

## Human ownership before delivery

I will personally check that this account accurately represents my involvement and revise any wording that overstates manual work. I will include the honest total time in the submission email, and I will not push additional changes after submission without notifying Stargo. For the live interview I plan to explain a new geographic routing case and trace one QL and one KPI result directly in code **without using AI assistance**.
