# Stargo RevOps Brain

**RevOps Engineer take-home · Stargo · November 2026**  
An auditable, local-first GTM workbench: inbound signals → evidence extraction → deterministic qualification and routing → human Sales decisions → weekly KPI pack, with a source-grounded AI-visibility (GEO) workflow.

**Start here:** [Windows setup](#windows--powershell-quick-start) · [macOS / Linux setup](#macos--linux-quick-start) · [Reviewer guide](docs/REVIEWER_GUIDE.md) · [KPI pack](KPI_PACK.md) · [Engineering process & AI disclosure](PROCESS.md) · [Architecture](ARCHITECTURE.md).

## Reviewer overview

| What to assess | Where to start |
| --- | --- |
| Inbound → evidence → qualification → human Sales acceptance | [Reviewer guide](docs/REVIEWER_GUIDE.md) and the **Lead intelligence** view |
| Reproducible weekly reporting and source drill-down | [KPI_PACK.md](KPI_PACK.md) and the **Weekly performance** view |
| AI visibility, recorded GEO gaps, optional live Gemini | **AI visibility** view and [architecture](ARCHITECTURE.md) |
| Engineering decisions, defect recovery, testing | [PROCESS.md](PROCESS.md) and [QUALITY_REPORT.md](QUALITY_REPORT.md) |

**Development provenance:** The application was developed with extensive ChatGPT assistance, including substantial generated Python, React, tests and documentation. Candidate-led requirements, prioritization, local testing and defect-driven corrections are described in [PROCESS.md](PROCESS.md); Gemini is an optional *runtime* integration, not the implementation author. This repository preserves its normal commit history. The deliverable is a **single-operator localhost prototype**, not a deployed production service. The original employer-provided data is not publicly redistributed.

**Suggested evaluation path (about five minutes after setup):** import the supplied ZIP; check `/api/health`; inspect one lead's source quotes, five gates and manual acceptance; verify the **6 / 4 / 3 / 2** reference KPI and a drill-down row; inspect the recorded GEO snapshot; then run `python scripts/reviewer_smoke.py` against an isolated temporary database. No Gemini key is necessary for these steps.

> **Data availability:** The six original synthetic files from `Stargo_RevOps_Take_Home_Pack_v2.zip` are imported **locally**, rather than committed to this public repository. Reviewers already have the assignment ZIP; place it on the machine where the app will run. The application is functional without an LLM key, but the provided pack is necessary to reproduce the assignment's original KPI figures. CI uses independent synthetic fixtures; it does not need the employer pack.

## Requirements

- Python **3.11+** (`py` on Windows), Git, and Node.js **20+** with npm.
- The original Stargo take-home ZIP, supplied with the assignment. **Do not unpack it into Git-tracked files.**
- Two terminals; localhost ports **8000** (FastAPI) and **5173** (Vite).
- **No API key** for the initial end-to-end run.

## Windows / PowerShell quick start

Commands below assume a **fresh clone** and a copy of `Stargo_RevOps_Take_Home_Pack_v2.zip` in Downloads. Use your actual ZIP location if different.

**Terminal 1 — backend, from a directory of your choice:**

```powershell
git clone https://github.com/danielforface/stargo-revops-brain.git
cd stargo-revops-brain
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps/api/requirements.txt
python scripts/import_take_home.py "$env:USERPROFILE\Downloads\Stargo_RevOps_Take_Home_Pack_v2.zip"
$env:STARGO_DATA_DIR = (Resolve-Path ".\data\private").Path
$env:STARGO_DB_PATH = "runtime/revops.sqlite3"
$env:STARGO_LLM_PROVIDER = "rules-only"
python -m uvicorn api:app --app-dir apps/api --host 127.0.0.1 --port 8000
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process Bypass` **in that terminal only**, then retry `Activate.ps1`. Windows timezone support (`tzdata`) is installed with `requirements.txt`.

**Terminal 2 — frontend:**

```powershell
cd stargo-revops-brain\apps\web
npm ci
npm run dev
```

If Terminal 2 starts from another working directory, navigate to the actual cloned repository first. Open **http://127.0.0.1:5173/**. If port 5173 is busy, stop the other Vite process rather than accepting an auto-selected port.

## macOS / Linux quick start

```bash
git clone https://github.com/danielforface/stargo-revops-brain.git
cd stargo-revops-brain
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r apps/api/requirements.txt
python scripts/import_take_home.py /absolute/path/to/Stargo_RevOps_Take_Home_Pack_v2.zip
export STARGO_DATA_DIR="$PWD/data/private"
export STARGO_DB_PATH="$PWD/runtime/revops.sqlite3"
export STARGO_LLM_PROVIDER="rules-only"
python -m uvicorn api:app --app-dir apps/api --host 127.0.0.1 --port 8000
```

In a **second** terminal:

```bash
cd stargo-revops-brain/apps/web  # use the actual absolute path if necessary
npm ci
npm run dev
```

Open **http://127.0.0.1:5173/**. The frontend proxies `/api` to the backend on `127.0.0.1:8000`.

## First-run verification (no key)

1. Open **http://127.0.0.1:8000/api/health**. Expect `ok: true`, `seed.ready: true`, and seed counts: **19 contacts, 20 valid inbound, 11 Sales decisions, 12 pipeline events, 1 quarantined invalid record**.
2. Open the React app. **Lead intelligence** shows the queue, per-lead Agent A evidence, Agent B's five gates, score, owner, reply draft and manual Accept/Reject.
3. **Weekly performance** for **4–8 October 2026, Asia/Jerusalem** must report **6 Qualified Leads / 4 Meetings Booked / 3 Meetings Held / 2 Opportunities** against targets **25 / 15 / 12 / 5**. Drill into KPI records. `historical-reactivation` is **Unknown (feed not received)**, not zero. Expansion is shown separately.
4. **AI visibility** reads **24 recorded answers, 8 prompts, 3 engines**; rank gaps and generate a clearly labelled *offline, approved-context* brief without an LLM.
5. To check the **unaltered reference dataset without changing your working SQLite database**, run the isolated smoke command below.

**Isolated source-pack replay** (from repository root with the virtual environment activated):

```powershell
python scripts/reviewer_smoke.py
```

It creates and deletes a temporary SQLite file, verifies **6/4/3/2**, exercises historical Accept/Reject and a simulated model failure, then exits without contacting an LLM or modifying `runtime/revops.sqlite3`. The checked-in [KPI_PACK.md](KPI_PACK.md) is the **pristine seed export**; interactive test decisions in your own SQLite file may legitimately change the dashboard and a subsequently re-exported pack.

## Optional Gemini Live — no key is required to review the core

1. In the UI choose **Connect Gemini**, select `gemini-3.5-flash-lite` (the default) or another offered model, paste a **complete** Gemini API key from Google AI Studio, and select **Test connection & activate**.
2. Only after Google responds successfully does the app show **Gemini Live**. Use **New inbound** or **Re-analyze with Gemini** to ask the model for *Agent A* signals. **Agent B remains deterministic.** No seeded messages are sent to Google automatically on page load.
3. In **AI visibility**, **Generate with Gemini** produces an LLM-guided structure. Factual content is reconstructed from approved `BC` / `PP` claims and source-topic checks; unsupported or unrelated citations are blocked/flagged.
4. **Disconnect** or reload the tab to return to **rules-only** mode. Invalid keys, timeouts, unsafe/invalid model output, and quota errors never turn a failed analysis into QL. No message is sent to a customer.

The key is held **in the browser tab's memory only** and passed in a request header to the localhost FastAPI proxy, which contacts Google's **fixed HTTPS endpoint**. It is not saved in SQLite, Git, environment files or browser localStorage. This is a *local, single-operator demonstration*, not production credential management. Use only authorized/synthetic messages when sending content to Google. Gemini Free Tier and model availability depend on the Google AI Studio project.

## Run the automated checks

**Backend, in the activated virtual environment from repository root:**

```powershell
python -m pip install -r apps/api/requirements-dev.txt
python -m pytest -q apps/api/tests
python -m compileall -q apps/api
python -m ruff check apps/api --select E4,E7,E9,F63,F7,F82
```

**Frontend, from `apps/web`:**

```powershell
npm ci
npm run test
npm run build
```

The same gates run in [GitHub Actions](.github/workflows/ci.yml) with Windows/Python 3.14, Linux/Python 3.12, Node.js 22 and React/TypeScript. External LLM requests are mocked in CI; a successful local Gemini verification is a separate operator acceptance step. See [reviewer guide](docs/REVIEWER_GUIDE.md) for reproducible edge-case walkthroughs.

## Architecture and decisions

```text
Original ZIP -> private data import -> Pydantic inbound validation -> SQLite
New inbound -------------------------/                    |
                                                         v
                         Agent A: validated extraction (offline | Gemini)
                                                         |
                              exact quotes + grounded self-reported facts
                                                         v
                         Agent B: deterministic QL gates, score, route
                                                         |
                      human Sales decision / timestamp -> evidence snapshot
                                                         |
                           traceable weekly KPI + CRO note + drill-down

Recorded AI answers -> deterministic GEO gap ranking -> approved-source brief
```

- **Backend:** FastAPI (`apps/api/api.py`), domain rules and SQLite store (`apps/api/engine.py`), Gemini proxy (`apps/api/gemini.py`), GEO (`apps/api/geo.py`). React/TypeScript/Vite frontend in `apps/web/src/`. This *modular monolith* is simpler to reproduce and audit than a message-broker stack for a take-home.
- **Agent A:** produces validated language, intent, buyer role, problem, self-reported firmographics, verbatim evidence, and injection flag. With Gemini, unsupported firmographics are rejected and explicitly observable source facts are corroborated by a deterministic extraction pass **within Agent A**.
- **Agent B:** deterministic and independent of model instructions. Qualification requires (1) ICP company fit, (2) buyer authority, (3) specific data pain, (4) expressed interest and (5) **recorded Sales acceptance**. Exclusions/suppression override marketing decisions. The score is **25 company fit + 20 buyer + 20 problem + 25 interest + 10 evidence = 100**; source provenance and factors are shown in lead detail.
- **Historical truth:** store an immutable evidence snapshot at acceptance time. A later LLM failure may change the *current queue status* but cannot quietly rewrite an accepted KPI. KPI uses the **half-open Israel-local week** and exposes source records; expansion is not acquisition. A subsequent explicit historical Reject can change the result.
- **GEO:** use 24 *recorded*, not live-searched, answers. Per engine, gap score = **buyer priority × 20 + missing brand mention 22 + missing owned citation 12 + competitor mentions (4 each, max 12) + wrong claim 25 + brand confusion 15**. Sum by prompt, highest first. Brief output is grounded to approved company/product/pilot facts (`BC`/`PP`); human review is required before publication.
- **Persistence:** SQLite for contacts, inbound messages, outputs/history, decisions, evidence snapshots, and last KPI pack. Scope is a single-user localhost demo; not a multi-user production deployment.
- **Frontend:** plain CSS, restrained CSS motion, Lucide icons and React state. No heavyweight UI system; tables remain scrollable at a **390px viewport**.

**What I deliberately cut:** no real HubSpot/email/LinkedIn integrations, outbound sends, authentication, public hosting, Kubernetes, paid-key requirement or HubSpot dry-run. The small synthetic qualifier eval is included instead of the optional CRM integration. **With more time:** managed multi-user auth, audited production migrations, a dedicated evaluation corpus and provider metrics, secret management, and accessibility/device regression automation. These are deliberate scope limits, not features implicitly claimed to be present.

## Files, privacy and reproducibility

| Resource | Purpose |
|---|---|
| [KPI_PACK.md](KPI_PACK.md) | Source-backed baseline export with <=150-word note to CRO |
| [PROCESS.md](PROCESS.md) | Development provenance, candidate contribution, AI-generated implementation, validation, scope and reported working time |
| [docs/REVIEWER_GUIDE.md](docs/REVIEWER_GUIDE.md) | Reviewer test script, inputs, expected behaviors and troubleshooting |
| [docs/acceptance_matrix.md](docs/acceptance_matrix.md) | Original requirements mapped to evidence and tests |
| [docs/engineering-walkthrough.md](docs/engineering-walkthrough.md) | Code tour and small-change exercise |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Architecture, trust boundaries and trade-offs |
| [QUALITY_REPORT.md](QUALITY_REPORT.md) | Verified test evidence and explicit limitations |
| [SECURITY.md](SECURITY.md) | Privacy and single-user security model |

The employer-provided pack is intentionally excluded from Git. `.env`, API secrets, SQLite runtime files, caches and Node dependencies are ignored. **Never commit the ZIP, private input, live keys, or a database containing operator activity.**

If you update a local `KPI_PACK.md` with experimental decisions, do not submit that modified export as the original baseline. To export the *current* local database intentionally, run `python apps/api/export_kpi.py`; it overwrites the local working copy and includes the current counts and CRO note.

**Troubleshooting:** if `GET /api/health` is not `seed.ready`, confirm all six files were imported into `data/private`. For a Windows timezone error, reinstall `apps/api/requirements.txt` in `.venv`. If the UI shows an HTTP 500, inspect the backend terminal; a dev-server `Vite ready` message does not prove the API worker started. `npm ci` is recommended for an exact dependency graph. **Do not delete `runtime/` or run `git reset --hard` to fix an error; these operations can destroy decisions.**
