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

The development assistant verified the original source-pack counts and the key API endpoints, added regression coverage for temporal qualification, unsubscribe precedence, replayed sales rejection, and self-reported new-buyer detection, and corrected an employees-plural parsing defect found by a failed regression test. The local offline suite reached **25 passed** after these changes. This is tool-reported verification by the assistant, **not** a claim that Daniel personally ran it.

The local environment did not have React/TypeScript npm dependencies installed; frontend compilation was **not verified locally**. The prior GitHub Actions run #5 on the old commit was successful. The new commit must be certified by a subsequent run before declaring the PR ready for review.
