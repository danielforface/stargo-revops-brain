# AI-assisted engineering process — factual draft for candidate review

> **Draft pending Daniel's first-person review and approval before submission.** This record identifies known events; it does not attribute unverified manual coding or tests to the candidate.

I received Stargo's synthetic take-home pack and created the public GitHub repository `danielforface/stargo-revops-brain`. I provided a detailed execution directive on 18 November 2026 requiring an auditable, human-in-the-loop system, deterministic business rules, full data provenance, source-pack privacy, meaningful tests and transparent AI usage.

## Tool use and task delegation

I used ChatGPT (GPT-6) as a coding and architectural assistant. I supplied the original take-home ZIP and asked it to read the assignment, inspect the repository, build the Python/FastAPI, SQLite and React/TypeScript project, write tests, and document engineering decisions. The assistant was instructed not to submit to the employer, send messages, publish source-pack files or claim tests it had not run. This is documented use of AI rather than a claim that every generated line was manually written.

## What I directed

- Business rules and KPI accounting remain deterministic and evidence-backed; LLM output is parsed only into a validated extraction schema.
- Human acceptance is required for a QL and for any outbound reply, which the application never sends.
- Pre-existing customers, open deals, duplicates and late UTC events must not inflate acquisition metrics.
- The repo must support contributors, tests, CI and a code walkthrough without AI.

## Verification and corrected failure

During the first local Pytest run, the assistant reported **14 passed, 1 failed**. The failing test revealed that a model failure was serialized as a JSON `null` string, which later broke `lead()` when it attempted to parse it as a valid Extraction object. The assistant corrected the storage and read path. A subsequent local run reported **15 passed**. This is a genuine example of verification catching an error in AI-assisted code.

## Pending candidate review

Before submission I will review the claims in this document, reproduce the startup instructions on my own machine, inspect representative QL and KPI calculations, check a failed-provider scenario and demonstrate a small code change without AI. These are **planned reviewer activities**, not claims that I have already performed them.

## Engineering verification update (18 Nov 2026)

The development assistant subsequently verified the original source-pack counts and the key API endpoints, added regression coverage for temporal qualification, unsubscribe precedence, a replayed sales rejection, and self-reported new-buyer detection, and corrected an `employees` plural parsing error found by a failed regression test. The local offline suite reached **25 passed** after these changes. This is tool-reported verification by the assistant, **not** a claim that Daniel personally ran it.

The local environment did not have React/TypeScript npm dependencies installed; frontend compilation in that environment is **not verified**. A GitHub Actions frontend job is configured but its actual status must be confirmed before declaring the project ready for submission.

## 18 Nov 2026 — Live Gemini and operator experience upgrade

The AI development assistant designed and implemented an optional operator-entered Gemini API-key workflow, a fixed-host HTTP backend adapter, schema/evidence checks, source-grounded GEO generation, an upgraded React UI and offline provider tests. The request to prioritize Gemini and a stronger corporate-grade experience came from the candidate. The implementation preserves deterministic QL decisions and never sends outbound customer messages.

The assistant consulted Google AI's current API/key documentation and tested Python contracts with mocked provider responses. Actual external model quality, billing-tier availability and end-to-end acceptance of a real key **cannot be claimed verified** until the candidate connects their own key and completes the live walkthrough. This paragraph documents assistant work, **not** code manually authored by the candidate. The first-person narrative above must be reviewed and approved by the candidate before external submission.


## Additional assistant-led engineering cycle — evidence for candidate review

The candidate directed the assistant to finish the identified P0/P1 backlog rather than asking for more design drafts. The assistant inspected the v2 assignment and QL standard, reproduced a missing Yossi QL (5 rather than the pristine pack's 6) and implemented a decision-time evidence ledger to prevent later LLM output changes from rewriting accepted weekly QLs. It also added an additive migration of existing SQLite state, a dynamic KPI Pack/CRO note, optional historical received-at entry in React, clearer identity/event counters, Gemini-aware source matching for GEO, and offline tests for these flows. The source pack was kept out of the public repository. The assistant performed a local clean-seed and legacy database migration smoke test and ran offline Pytest before preparing the PR change.

**Candidate review is still required:** verify this narrative matches what actually happened, record the total *actual time spent* and the coding/AI tools used, and be prepared to personally explain the implementation. Do not claim manual coding, manual tests, live Gemini traffic, production deployment or post-submission work that did not happen. The candidate's live UI test and GitHub Actions status for the final commit should be appended after they are independently verified.


## AI-assisted correction after real operator review — 18 November 2026 (candidate review required)

During a local walkthrough, the user showed a self-reported business owner whose live Gemini analysis correctly extracted buyer role and a document problem, but omitted employee count, business vertical and location even though those statements appeared in the source message. Historical accepted-evidence KPI remained stable, but the current queue showed `needs review`. This was a real false negative, not a reason to rewrite Sales Acceptance.

The development assistant implemented a bounded corroboration pass inside Agent A, verified evidence-specific Agent B gates, added synthetic hallucination/omission/unsolicited-interest/multilingual regressions, and updated the UI to distinguish self-reported firmographics from CRM facts. The assistant ran local offline tests and clean-pack replay and obtained separate GitHub Actions evidence. This report does not claim that the candidate manually wrote the code or that a new personal-key request was made from CI. The candidate must review this paragraph in their own voice and record true hours before submission.
