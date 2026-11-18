# Security policy

This is an offline-capable, local single-operator take-home prototype — **not a hardened, internet-facing service**.

Do **not** include vulnerabilities, exploit payloads, credentials or employer-provided messages in public issues. Instead use GitHub's **Report a vulnerability** private advisory flow for this repository if available, or contact the repository owner privately. No public-response SLA is promised.

Threat boundaries: inbound messages and model results are untrusted; business rules are deterministic; private logs should not include message bodies, email addresses, full prompts, credentials or API keys. Only optional outbound traffic from the backend is to the configured, fixed Groq endpoint when explicitly enabled; no CRM, email or social services are contacted. The UI does not send drafts.

The backend is intended for `127.0.0.1`. Do not deploy publicly without authentication, HTTPS, rate limiting, abuse protection, secure secrets management and a data retention plan. Review security implications of dependency changes. Source-pack data is kept in ignored `data/private/`.

### Local Gemini key safety

The live connector accepts a key only in a same-origin request header supplied by the operator. The UI holds it only in tab memory and clears it on disconnect, reload, or close; no `localStorage`/cookies/SQLite or Git commit. Do not run the unauthenticated demo on a public interface. Real production use needs server-side encrypted secret management, authentication, per-user authorization, and TLS. Do not put secrets into screenshots, issue reports, browser console logs, or PR descriptions. Live inference sends the entered lead's text to Google: use authorized/synthetic data only.


### Decision integrity, operator privacy, and failure logging

A failed or malicious model call cannot turn a lead into QL/disqualified. The latest analysis may move to `needs review`, but original sales acceptance is preserved in an immutable `decision_evidence` snapshot so historical KPI does not silently shift. A human rejection is a separate append-only event. The `analysis_history` table stores structured, validated output and a safe error class (not raw provider errors, user prompts, messages or credentials). Keys are never persisted. CORS is restricted to localhost Vite origins, and the development API is not authenticated: do not bind it beyond loopback. Data sent to Gemini may be processed by Google; do not send real third-party personal data without authorization. No outbound communication from AI drafts is implemented.
