# Verification snapshot — 18 November 2026

Status: engineering candidate; **not final submission**.

## Executed locally

- `pytest -q apps/api/tests`: **25 passed** (offline; 0.44 sec on this runtime).
- `python -m compileall -q apps/api`: **passed**.
- Seeded API smoke via FastAPI `TestClient`: health, leads, weekly KPI, GEO visibility, GEO gaps returned HTTP 200; brief endpoint also returned HTTP 200.
- SQLite seed replay: 19 contacts, 20 valid inbound, 11 decisions, 12 pipeline events, 1 rejected inbound remained unchanged after a second import.
- Data-backed report regenerated from stored records: acquisition QLs 6; booked 4; held 3; opportunities 2; historical-reactivation feed remains unknown.

## Engineering defects detected and fixed

1. Analysis failure had been stored as JSON null instead of a null SQL field, preventing safe readback.
2. KPI qualification was able to see messages received **after** acceptance. It now only uses evidence received on or before the acceptance timestamp.
3. Unsubscribe now suppresses even an existing customer and prevents reply draft creation.
4. Offline extraction now detects a self-reported `Head of Operations` for unseen buyers. A regression test revealed plural `employees` did not parse and was corrected.

## Not verified in this runtime

- React/Vite frontend dependency install, typecheck and build: **NOT RUN to success** because npm dependencies are unavailable in this network-restricted environment.
- Ruff: **NOT RUN** (tool unavailable locally).
- GitHub Actions: **NOT RUN** until all source files have been published and a pull request triggers CI.
- Production deployment: **NOT ATTEMPTED**, outside the assignment.

## Source pack handling

No original employer-supplied CSV/JSON/Markdown source pack is included in the public source distribution. The repository import script reads the ZIP locally into an ignored `data/private/` directory.

These results are laboratory evidence only; independently reproduce the setup and frontend build on a fresh machine before submitting to Stargo.