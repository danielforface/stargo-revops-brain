# Security boundaries

**This is a local single-operator take-home application, not an internet-facing or multi-tenant service.** Bind the backend to `127.0.0.1`; never put an unauthenticated demo API on a public address.

## Data and credentials

- The six employer-supplied synthetic source files are imported into Git-ignored `data/private/`. Runtime SQLite databases, `.env` files, package caches and secrets are not committed.
- No CRM, email, LinkedIn or marketing destination is contacted. The app generates a **reply draft only**; every actual Sales decision is manual and recorded.
- If enabled, **Gemini Live** sends the selected inbound content to Google's **fixed** `generativelanguage.googleapis.com` HTTPS endpoint through the local backend. A user-supplied key stays in React tab memory; it is never placed in request URLs, browser storage, logs, source code or SQLite. Headers can be visible in that user's own browser network inspector; avoid shared computers and untrusted extensions. Do not process real third-party personal data with Google without authorization.
- The pre-existing optional Groq mode, when configured by OS environment variables, also uses a fixed HTTPS endpoint. The default `rules-only` mode requires **no provider key or network calls to an LLM**.
- Logs should contain request methods/statuses and safe error classes, **not** full message bodies, emails, prompts, API keys, or supplier documents. Do not post customer material in public issues or PR comments.

## Model and input trust boundaries

- Inbound messages and model outputs are untrusted. Pydantic validates structure. Verbatim source evidence, deterministic firmographic corroboration and injection checks constrain Agent A.
- Agent B applies QL gates, scoring, routing, suppression and exclusion **deterministically**. An LLM cannot accept a lead, modify weights or send any reply.
- A failed model response moves the *current* analysis to `needs review`; it never silently creates or deletes a historical Sales acceptance. `decision_evidence` stores immutable acceptance-time snapshots.
- GEO prose is assembled from approved `BC`/`PP` text. Unrelated source associations and unsupported editorials are filtered or rejected; source-grounded does not mean publication without human approval.

## Out-of-scope protections for production

The app has no authentication or authorization, secure server-side key vault, public deployment hardening, durable queue, rate limiting or GDPR retention policy. Before any real production use, add these alongside managed migrations, access isolation, HTTPS, audit/privacy monitoring and threat review. CORS alone does not authenticate requests.

Report security concerns privately to the repository owner; do not include vulnerabilities, live keys or personal data in a public GitHub issue. No incident-response SLA is implied by this take-home project.
