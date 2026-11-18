# Stargo RevOps Brain

*A compact, auditable GTM workbench for lead qualification, human sales decisions, weekly KPIs and AI visibility.*

**Status:** Engineering candidate solution. The employer-provided data pack is **not** committed to this public repository; only original application code and independent test fixtures are included. All names and figures in the take-home pack are synthetic, but publication rights were not explicitly established. Provide the original pack locally to reproduce the assignment's KPI report.

## Architecture in one minute

A **modular monolith**: one Python/FastAPI API, SQLite persistence, one React/TypeScript UI. Data enters through either the seed importer or `/api/inbound`, and is normalized by the same Pydantic contract. Agent A extracts evidence from untrusted text, Agent B applies deterministic QL, scoring, exclusion and routing logic; humans explicitly Accept/Reject. Reports derive from stored facts and decisions, not browser calculations. GEO analysis reads the 24 recorded AI answers; brief text uses only approved BC/PP claims. No user message is automatically sent.

## Requirements

- Python 3.11 or newer, `pip`, `venv`
- Node.js 20+ and npm
- Original `Stargo_RevOps_Take_Home_Pack_v2.zip` provided by Stargo

## Quick start (no LLM key)

```bash
# From the repo root. Import the employer-provided ZIP privately (never committed):
python scripts/import_take_home.py /path/to/Stargo_RevOps_Take_Home_Pack_v2.zip
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r apps/api/requirements.txt
STARGO_DATA_DIR=./data/private STARGO_DB_PATH=./runtime/revops.sqlite3 uvicorn api:app --app-dir apps/api --reload
```

In a **second terminal**:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The backend serves `http://127.0.0.1:8000/api/health` and OpenAPI documentation at `http://127.0.0.1:8000/docs`.

Windows PowerShell, from the repository root (the path may be anywhere, not necessarily your Desktop):

```powershell
py scripts/import_take_home.py "$env:USERPROFILE\Downloads\Stargo_RevOps_Take_Home_Pack_v2.zip"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps/api/requirements.txt
$env:STARGO_DATA_DIR = (Resolve-Path ".\data\private").Path
$env:STARGO_DB_PATH = "runtime/revops.sqlite3"
$env:STARGO_LLM_PROVIDER = "rules-only"
python -m uvicorn api:app --app-dir apps/api --reload --host 127.0.0.1 --port 8000
```

**Windows time-zone support:** The backend uses `ZoneInfo("Asia/Jerusalem")` for the reporting window. Windows/Python may not provide the IANA time-zone database. `requirements.txt` now installs the official Python `tzdata` package automatically on Windows. If you installed requirements before this fix, while the project's `.venv` is activated run `python -m pip install tzdata`, stop the old Uvicorn process with Ctrl+C, and restart it. A line saying “Uvicorn running” is not proof that the worker initialized: verify `http://127.0.0.1:8000/api/health` returns `{"ok":true,...}` and `seed.ready` is true.

If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope Process Bypass` once in the current window and try again. When `$HOME\Desktop` is missing (e.g., OneDrive-redirected Desktop), work in any existing directory; all commands are relative to the repo root.

Once seeded, the SQLite database can be restarted safely; the importer uses stable source IDs and does **not** overwrite human decisions. The original malformed `IN-019` record is quarantined with an error class; it does not crash setup. The 19 CRM records, 20 valid inbound records, 11 sales decisions and 12 pipeline events are stored at clean import.

## Optional live LLM mode

Fallback is **rules-only**, labelled in the API/UI as `rules-only`. It does not simulate a live model. For a free-tier Groq key:

```bash
export STARGO_LLM_PROVIDER=groq
export GROQ_API_KEY='your-key-here'
# restart the API
```

Only Agent A makes LLM requests, via a fixed HTTPS endpoint at `api.groq.com`; output must pass the Pydantic extraction schema and evidence verification. Agent B *never* delegates QL authority to a model. On invalid JSON, timeout, invalid credentials or a disconnected provider, the stored status becomes `needs review`, preserving human control. Automatic retry is intentionally disabled to avoid duplicate charges or runaway wait times. The model is never used during CI. The application makes no CRM, email or social-network calls. Reply drafts are **never sent**.

## What you can do

- Import CRM, inbound messages, sales decisions, opportunities and meeting events idempotently.
- Paste an arbitrary new inbound, including Hebrew and LinkedIn messages, and run the same analysis pipeline.
- Match identities by normalized email or LinkedIn profile; never merge by company or name.
- Inspect evidence, five QL gates, score factors, owner and draft response.
- Accept/Reject with editable decision timestamp and persistent audit events.
- View weekly acquisition KPI actuals, targets, variance, per-record drill-down, source attribution and separate expansion.
- Inspect 24 synthetic AI-answer captures, competitor mentions and ranked GEO gaps. Generate an *offline approved-context template brief* with BC/PP citations; this is not advertised as live LLM generation.

## Tests and artifacts

```bash
pip install -r apps/api/requirements-dev.txt
pytest -q apps/api/tests
python -m compileall -q apps/api
ruff check apps/api --select E4,E7,E9,F63,F7,F82
cd apps/web && npm install && npm run build
```

Generate the data-backed report **after** seeding the database:

```bash
python apps/api/export_kpi.py
```

The checked-in `KPI_PACK.md` is generated from the original seed. It is not hand-entered. It should be regenerated after decision changes. For a clean-state replay, remove only the local `runtime/` directory; **this discards operator decisions** and must not be done in normal operations.

## Design choices and trade-offs

- **No microservices or message broker**: unnecessary in a self-contained assignment, easier to audit.
- **SQLite**: transparent relational state, stable IDs, quick local setup; no migrations or concurrent writer scale promised.
- **Rules-only fallback**: testable offline and resilient, but weaker than a multilingual model for unseen phrasing. All claims about model quality are bounded by this limitation.
- **Deliberate cuts**: no live HubSpot integration, outbound delivery, auth, heavy telemetry, Kubernetes, animation platform, paid LLM dependency, or unsupported claims about lead-company data.
- **Access model**: local single-operator demo. No authentication is required by the brief; **do not expose this API to the internet**. CORS is limited to local Vite origins.
- **GEO**: uses source-grounded template instead of speculative live copy if no model is configured. All BC/PP claims are explicit; any novel claims require separate approval.

See [ARCHITECTURE.md](ARCHITECTURE.md), [PROCESS.md](PROCESS.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [docs/engineering-walkthrough.md](docs/engineering-walkthrough.md).

## Windows browser returns `Internal Server Error` / KPI JSON parse error

If the health endpoint is ready but `http://127.0.0.1:5173/api/kpi/week` shows HTTP 500, update to the latest `feat/revops-core` branch and restart **both** Python and Vite after `git pull --ff-only`. This issue was caused by concurrent `/api/leads` and `/api/kpi/week` requests sharing an unlocked SQLite connection. Store operations are now serialized using a reentrant lock and tested with concurrent requests. The UI also handles non-JSON server failures without crashing other tabs. Existing SQLite decisions are preserved; **do not delete `runtime/`**. The `favicon.ico` 404 and React DevTools suggestion in the browser console are not KPI errors.


## Live Gemini connector — operator quick start

Run the Backend and Frontend normally, with `STARGO_LLM_PROVIDER=rules-only`. Open the UI on `http://127.0.0.1:5173`, choose **Connect Gemini** in the top-right, paste a Google AI Studio API key and click **Test connection & activate**. This triggers a real Google API call. A success indicator means the key was accepted for the selected model.

While the key is connected, **New inbound** and **Re-analyze with Gemini** use Gemini for evidence extraction; deterministic Agent B still enforces all five QL gates. The existing seeded leads are *not* automatically reprocessed; select a lead to run live analysis deliberately. In **AI visibility**, **Generate with Gemini** produces a live content plan whose factual text is reconstructed only from approved BC/PP source IDs. **Disconnect** or reload the browser to return to offline, rules-only mode.

**Security:** The key is stored in memory for the current browser tab only, never in localStorage, SQLite, .env, source, logs or URLs. It is sent to the local FastAPI server in a request header, and from there to a fixed Google HTTPS endpoint. **Only use this on your own computer at 127.0.0.1**; browser-entered keys are not a production secret management solution. Google may process the submitted lead messages and approved brand claims; use only demo/authorized data. API free-tier availability and quota are controlled by the Google AI Studio project, not by a consumer Gemini subscription.

Recommended models: `gemini-2.5-flash` (default) or `gemini-2.5-flash-lite`. If Google rejects the model or key, the connection is not marked active. A live extraction failure leaves the lead in `needs review`, with no reply sent.

API endpoints: `GET /api/ai/providers`, `POST /api/ai/verify` (JSON model + `X-Gemini-API-Key`), optional key on `POST /api/inbound`, `POST /api/leads/{id}/analyze`, and `POST /api/visibility/brief`.

No user text is automatically sent to Gemini on page load or during KPI refresh. Only an explicit operator action sends lead content. Screens are animated with restrained CSS transitions and honor `prefers-reduced-motion`.

Test:
```powershell
python -m pytest -q apps/api/tests
cd apps/web
npm install
npm run test
npm run build
```


## Gemini API keys minted after 2026 (AQ. format)

Google AI Studio now issues authorization keys beginning with `AQ.` as well as legacy `AIza` keys. A previous local validator rejected dots and incorrectly displayed “Enter a valid Gemini API key” *before contacting Google*. This has been fixed: both key formats pass safe, minimal syntax checks, and only Google decides whether a key is valid. Use the **copy icon** on the AI Studio API Keys page; the shortened key preview is not the secret.

For new projects prefer **Gemini 3.5 Flash-Lite** (the UI default) or **Gemini 3.8 Flash**. Some newly created projects cannot call legacy 2.5 models. HTTP 401 indicates an authentication problem, HTTP 403 project access/permissions, HTTP 404 model unavailable, and HTTP 429 quota/rate limiting. A key's billing tier alone does not prove access to a selected model. The application does not auto-cycle through keys or models; choose the model explicitly and verify it.

No secrets are checked into the repository or used in automated tests. Live connectivity remains a separate test to perform on the local operator machine. For security, don't paste a key into chat, issue comments, logs, or screenshots.
