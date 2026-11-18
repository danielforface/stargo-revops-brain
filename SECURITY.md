# Security policy

This is an offline-capable, local single-operator take-home prototype — **not a hardened, internet-facing service**.

Do **not** include vulnerabilities, exploit payloads, credentials or employer-provided messages in public issues. Instead use GitHub's **Report a vulnerability** private advisory flow for this repository if available, or contact the repository owner privately. No public-response SLA is promised.

Threat boundaries: inbound messages and model results are untrusted; business rules are deterministic; private logs should not include message bodies, email addresses, full prompts, credentials or API keys. Only optional outbound traffic from the backend is to the configured, fixed Groq endpoint when explicitly enabled; no CRM, email or social services are contacted. The UI does not send drafts.

The backend is intended for `127.0.0.1`. Do not deploy publicly without authentication, HTTPS, rate limiting, abuse protection, secure secrets management and a data retention plan. Review security implications of dependency changes. Source-pack data is kept in ignored `data/private/`.


## User-entered Gemini keys

Only use this single-operator prototype on `127.0.0.1` in a trusted browser. The key is typed in an operator drawer and kept in React memory until disconnect/reload. It is passed in `X-Gemini-API-Key` to the same-origin local backend, then to Google's fixed HTTPS host in `x-goog-api-key` (never URL query parameters). The key is never saved in localStorage, SQLite, source, logs, or telemetry. The backend has no authentication; **do not expose it to the internet**. For real production use, deploy server-side managed secrets and authenticated access. Authorize the use of any lead message before sending it to Google's API.
