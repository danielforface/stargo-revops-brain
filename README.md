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

Windows PowerShell, from the repository root:

```powershell
py scripts/import_take_home.py "C:\path\to\Stargo_RevOps_Take_Home_Pack_v2.zip"
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r apps/api/requirements.txt
$env:STARGO_DATA_DIR = (Resolve-Path data/private).Path
$env:STARGO_DB_PATH = 'runtime/revops.sqlite3'
uvicorn api:app --app-dir apps/api --reload
```

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
- **SQLite**: transparent relational state, stable IDs, transactional writes and additive migration tables; no concurrent-writer horizontal scaling is promised.
- **Rules-only fallback**: testable offline and resilient, but weaker than a multilingual model for unseen phrasing. All claims about model quality are bounded by this limitation.
- **Deliberate cuts**: no live HubSpot integration, outbound delivery, auth, heavy telemetry, Kubernetes, animation platform, paid LLM dependency, or unsupported claims about lead-company data.
- **Access model**: local single-operator demo. No authentication is required by the brief; **do not expose this API to the internet**. CORS is limited to local Vite origins.
- **GEO**: uses source-grounded template instead of speculative live copy if no model is configured. All BC/PP claims are explicit; any novel claims require separate approval.

See [ARCHITECTURE.md](ARCHITECTURE.md), [PROCESS.md](PROCESS.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [docs/engineering-walkthrough.md](docs/engineering-walkthrough.md).

## Gemini Live — session-only key in the operator UI

**Local demo; keep both servers bound to 127.0.0.1.** Open the UI, select **Connect Gemini** in the upper-right corner, paste your own Google AI Studio API key, select `gemini-3.5-flash-lite` (or `gemini-3.8-flash`; legacy 2.5 models remain optional for older projects), and click **Test connection & activate**. This performs a *real* Gemini API request. A verified key is held only in browser tab memory until disconnect/refresh/close. It is not saved in `localStorage`, SQLite, or GitHub, and it is never passed as a URL query parameter. Do not use this demo on a public network, shared browser, or as a production multi-user deployment. Google API quota/billing policy is governed by your AI Studio project and may differ from your consumer Gemini subscription.

After connecting, **New inbound** and **Re-analyze with Gemini** call the fixed Google endpoint through the localhost FastAPI proxy and pass Agent A's validated extraction to deterministic Agent B. Previously saved leads are *not* automatically bulk reprocessed; use Re-analyze explicitly for an existing lead. **Generate with Gemini** in AI visibility creates a live outline/content brief while factual paragraphs are reconstructed from source-approved `BC`/`PP` statements. Failures are visible, never silently treated as successful live AI. A malformed extraction is stored as `needs review`.

If you never enter a key, all original workflows remain functional in clearly labeled offline `rules-only` mode. The GEO brief is correspondingly labeled as the approved-context offline template. No real outbound email/CRM/social messaging is ever sent.

**Local API contracts** (not public internet endpoints):

- `GET /api/ai/providers`: supported models and data-handling policy (no key).
- `POST /api/ai/verify`: JSON `{ "model": "gemini-2.5-flash" }`, header `X-Gemini-API-Key: <your-key>`; responds only after a real Google test.
- `POST /api/inbound?model=gemini-2.5-flash`: same inbound JSON contract; optional key header selects Gemini extraction.
- `POST /api/leads/{id}/analyze?model=gemini-2.5-flash`: re-analyze a selected lead, with optional key header.
- `POST /api/visibility/brief`: optional key header + model JSON for live grounded GEO generation; without key, offline template.

The client never stores the API key. Google may process the inbound message content and approved marketing-context claims during live calls: use synthetic/demo data only unless you have authorization to send the content to the external provider. Backend outbound access is constrained to `generativelanguage.googleapis.com` and (for the pre-existing optional Groq environment mode) `api.groq.com`. Credentials are redacted from errors and excluded from persisted records. No retry loops are used.

**Quality gates:** `pytest -q apps/api/tests` (Gemini transport is mocked, no network/key), `npm run test` and `npm run build` under `apps/web`. The historical reporting pack uses frozen acceptance-time evidence; later Gemini re-analysis cannot silently rewrite QL counts. A later explicit human rejection or a new decision with an eligible `decided_at` can change the pack.


## Reviewer acceptance: migration, as-of decisions, and KPI consistency

**Update existing Windows checkout without losing decisions:** stop the two local servers, `git status --short`, then `git pull --ff-only` on `feat/revops-core`. Preserve `runtime/` and `data/private/`. Restart Python and Vite using the PowerShell commands above. The SQLite schema is extended automatically with `analysis_history` and `decision_evidence` tables; it does not erase existing contacts, messages or decisions. An old database imported from the supplied synthetic pack receives deterministic, immutable evidence snapshots for its recorded seed decisions.

**Why queue status can differ from weekly QL:** lead status reflects the latest validated analysis and explicit decision; the Oct 4–8 report counts acceptance-time evidence frozen in `decision_evidence`. A later, failed Gemini run must put the current lead in `needs review` but cannot erase a previously recorded, legitimate QL. Explicit business rejections within the week can still change the historical pack. The KPI computation also persists the latest report as `meta.latest_kpi_pack` in SQLite after seeding, after decisions and after report refresh.

**New inbound** now offers `Received at (optional)`: blank defaults to server now; an entered date/time is interpreted as **the browser's local timezone**, converted to ISO UTC and validated by the server. A past Sales acceptance timestamp before the inbound is rejected with a clear error. Do not fake historical events simply to hit a target. The queue separately labels **Unique Leads**, **Inbound Events**, and **Current QL**, with a note explaining why these counts need not equal the week's QLs.

**Current report export:** the `Copy KPI pack` control in Weekly performance obtains the same server-side report as `GET /api/kpi/pack`, with an automatically recomputed note to the CRO (<=150 words) and highest-ranked GEO prompt. Alternatively run `python apps/api/export_kpi.py` from the repository root to write `KPI_PACK.md` from local SQLite. This reflects *your local decisions*. Keep a pristine, unmodified input-data state for the take-home submission; if you have inserted trial decisions, do not commit those altered figures without a clear explanation. Never delete a populated `runtime/` to fix an unrelated issue.

**GEO source checks:** live Gemini chooses only editorial layout and BC/PP source IDs. Factual paragraphs are assembled from approved claims. Additional deterministic topic matching excludes unrelated evidence (for example air-waybill pilot `PP-3` from a carrier-invoice reconciliation section), and unsupported numeric/absolute statements in headings and FAQ questions are blocked. The UI displays source quality warnings. The original `ai_answers.json` captures remain offline snapshots; `Generate with Gemini` is a *separate*, real model call when a key is connected.

**Tests:** `python -m pytest -q apps/api/tests`, `python -m ruff check apps/api --select E4,E7,E9,F63,F7,F82`, `npm run test`, `npm run build`. Backend tests include decision-time evidence immutability, provider failures, as-of/rejection windows, KPI persistence, concurrent API reads, and current vs historical QL. Frontend tests include browser input time conversion, unique identities vs event counts, the new-inbound form, and Gemini connection. CI exercises Python on Windows and Linux and frontend TypeScript/Vitest.

**Manual final check (must be performed on the candidate's PC):** visit `/api/health` and `/api/kpi/week`, verify a clean seed yields 6/4/3/2, paste a genuinely unseen inbound using the React form, use Accept/Reject with valid timestamps, restart and verify persistence, connect a real Gemini key, generate a sourced brief and test a wrong key. Provide no key to GitHub or the chat. The reviewer should compare the exported pack with the current local database and ensure no demo-only decisions are inadvertently presented as original data.

## Remaining deliberate scope limits

This is a local, single-operator review application. There is no real CRM or email integration, authentication, external deployment, distributed transaction queue or large-scale monitoring. The optional HubSpot dry-run bonus is not implemented: assignment scoring explicitly prioritizes correctness and evidential traceability. LLM live tests in CI use mock transport; they do not spend a real user's quota. For production, add multi-user authorization, migrations through a managed migration tool, server-managed secrets, access logs without personal data, secret rotation, and a formal eval corpus across languages and models.


## Source-backed firmographics with Gemini (hybrid Agent A)

When Gemini extracts buyer role/intent/pain but omits explicit company-size, industry or region statements, a second deterministic pass **inside Agent A** independently extracts supported statements from the **same inbound message**. Supported facts enter the validated Extraction, marked self-reported and unverified (never written to CRM). An invented employee count or unsupported vertical from the model causes a safe `needs review`, rather than a false QL. Agent B checks the validated Agent A output against the matched CRM record and additionally requires a **relevant grounded quote** for both the data problem and expressed buying interest; an arbitrary quote cannot substantiate `intent=demo`. Unsupported languages, phrasing and places remain unknown, not guessed.

Basic patterns cover common English, Dutch, German and Hebrew examples; they do **not** guarantee complete multilingual understanding. Existing acceptance snapshots and historical KPIs remain immutable during re-analysis. The lead detail shows self-reported firmographics separately from CRM data.

**Existing local DB:** stop both servers, `git pull --ff-only`, restart FastAPI and Vite, reconnect Gemini, then explicitly click **Re-analyze with Gemini** on the affected lead. Old analyses are not silently sent to Google again. No `runtime/` deletion or source ZIP re-import is needed. On a pristine private pack, `python scripts/reviewer_smoke.py` remains 6/4/3/2.
