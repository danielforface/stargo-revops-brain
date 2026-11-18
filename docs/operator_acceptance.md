# Local operator acceptance — Windows 10/11

This is a repeatable Windows-based acceptance protocol. It describes checks a reviewer or operator can run, not assertions that a new reviewer has already completed them.

1. Stop backend and Vite with Ctrl+C. From `D:\CODE\tasks\01\stargo-revops-brain`, run `git status --short`; if clean, run `git pull --ff-only` on `feat/revops-core`. Do not discard local work or delete the DB.
2. Start Backend in PowerShell:
   ```powershell
   cd D:\CODE\tasks\01\stargo-revops-brain
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r apps/api/requirements.txt
   $env:STARGO_DATA_DIR = (Resolve-Path .\data\private).Path
   $env:STARGO_DB_PATH = "runtime/revops.sqlite3"
   $env:STARGO_LLM_PROVIDER = "rules-only"
   python -m uvicorn api:app --app-dir apps/api --reload --host 127.0.0.1 --port 8000
   ```
3. In a separate PowerShell, start the frontend:
   ```powershell
   cd D:\CODE\tasks\01\stargo-revops-brain\apps\web
   npm install
   npm run dev
   ```
4. Check `http://127.0.0.1:8000/api/health` and `http://127.0.0.1:8000/api/kpi/week` return JSON, and open `http://127.0.0.1:5173` (Ctrl+Shift+R). The 6/4/3/2 KPI baseline applies only to a pristine source replay. Existing test Accept/Reject events may change the local counts.
5. Run isolated validation safely without resetting your existing DB: from repo root, `python scripts/reviewer_smoke.py`. It creates a temporary SQLite and **never touches** `runtime/revops.sqlite3`. Expected: 6/4/3/2, unchanged after forced Gemini failure, temporary 7 after accepted synthetic lead and back to 6 after rejection.
6. In Lead Intelligence, compare `UNIQUE LEADS` against `INBOUND EVENTS`, open a QL and inspect its five conditions and current-vs-historical banner. Use new `Received at (optional)` in the form: date/time is from your browser's local timezone, default blank means now.
7. Create a synthetic lead, Accept at a valid time after the original inbound, verify KPI, then Reject with a later within-week time and verify KPI reverts. Restart both servers and confirm history persists. Do not write an acceptance timestamp earlier than the source inbound.
8. Connect a **full** Google AI Studio Gemini API key via the UI; never share it. Verify `gemini-live` extraction on one synthetic lead. Force a wrong key and confirm `needs review`/provider error without any outbound reply. Try `Generate with Gemini` and inspect source ID relevance and warnings. No simulated confirmation counts as a real live test.
9. In AI visibility, check 8 gaps and 24 recorded answers. Generate a brief without a key and then with one; in both, facts should use BC/PP source IDs. Verify that invoice reconciliation does not cite an unrelated air-waybill pilot.
10. Test 390px viewport using browser DevTools; ensure buttons, key entry and metric panels remain accessible without horizontal page overflow (tables may scroll in their own containers). Run `python -m pytest -q apps/api/tests` and `npm run test && npm run build` on local machine if desired.
11. Export `KPI_PACK.md` from **clean data** to submit using `python apps/api/export_kpi.py` or `Copy KPI pack` from Weekly Performance. The note to CRO must match current counts and mention the top gap. If your local DB contains trial decisions, do not represent it as the untouched source pack.
12. Consult `PROCESS.md` for the disclosed ChatGPT/Gemini roles and reported five hours of active work. Before treating any particular commit as validated, inspect the corresponding GitHub Actions run; use the submission instructions and dates from your original task pack.

**Never send** your Gemini key, local private ZIP or employer documents in public GitHub issues, screenshots or source commits.


## Focused acceptance — re-analysis after firmographic repair

1. Preserve `runtime/` and `data/private/`; update the development branch, restart API/UI, reconnect Gemini explicitly.
2. Choose a previously `needs review` inbound where the **original** message clearly provides employee count, ICP vertical and location, and the Sales Acceptance has already been recorded. Click **Re-analyze with Gemini** once.
3. Verify the lead detail now displays **Company facts · self-reported** (not CRM-verified), Company Fit and Relevant Buyer with evidence, and the correct geographic owner. The current status may become `QL` if all five gates are met; historical KPI remains unchanged.
4. With **independently synthetic** inbound, verify no QL for a fabricated employee count, unsupported industry, fabricated interest with an irrelevant quote, unsubscribe, and invalid model output. Missing facts should remain unknown.
5. Ensure the original clean-pack smoke still reports 6/4/3/2 without touching your actual operator SQLite. Live Google access is a separate manual check; CI uses mocked responses only.
