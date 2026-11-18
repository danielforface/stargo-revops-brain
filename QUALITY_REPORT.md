# Quality and release evidence — Stargo RevOps Brain

**Status:** candidate submission candidate, subject to the author's personal review of `PROCESS.md` and actual hours before emailing. The application is a localhost prototype, not a deployed production service.

## Automated verification (repository evidence)

Final engineering pre-packaging run: [GitHub Actions 44289126662](https://github.com/danielforface/stargo-revops-brain/actions/runs/44289126662) on branch `feat/revops-core`, commit `43f091d0dadcb296ee4e8da3528b279cd19e1c0c`.

| Gate | Observed result |
|---|---|
| Backend Linux, Python 3.12 | **84 passed**, 1 nonblocking dependency warning; compile and Ruff passed |
| Backend Windows, Python 3.14 | **84 passed**, 1 nonblocking dependency warning; compile and Ruff passed |
| Frontend Node.js 22, Vitest | **10 passed** |
| TypeScript + Vite production build | **Passed** |

Release-packaging commits require a **new final `main` Actions run** before submission. The historical numbers above belong to the exact feature commit, and should not be falsely presented as results of a different commit.

## Private source-pack acceptance (operator-reported)

The operator ran `python scripts/reviewer_smoke.py` with the supplied v2 ZIP. It reported: **19 CRM contacts, 20 valid inbound messages, 11 decisions, 12 pipeline events, one rejected invalid inbound; 6/4/3/2 KPI counts**, missing historical-reactivation remains Unknown; failure/restart/historical replay passed. The smoke uses a temporary SQLite database and does not send outbound network traffic.

The operator also reported a successful **Gemini live connection**, generated a source-grounded GEO brief and re-analyzed one source-backed lead to five verified QL gates, owner Noa and score 100. These are **manual operator observations**, not claims that CI used a real key.

## Defects found and corrected during development

- Missing Windows IANA timezone package caused server startup failure. Windows-only `tzdata` dependency and a Windows CI job now cover it.
- Sharing an unlocked SQLite connection across FastAPI threads caused intermittent HTTP 500 during concurrent dashboard loads. Storage operations are serialized; long live Gemini calls do not block all dashboard reads.
- Historical QLs could drift when Gemini re-analysis failed or changed the current extraction. Immutable acceptance-time evidence and additive migration protect the frozen weekly report.
- A self-reported owner at a customs brokerage was incorrectly marked `needs review` when Gemini omitted company-size/vertical/location. Agent A now corroborates those details against the original source message; unsupported model claims remain untrusted.
- GEO output sometimes associated unrelated pilot evidence with workflow copy, or implied compliance in a mixed heading. Approved claim topic checks now remove/rewrite unsupported editorial text, with visible quality notes.
- The frontend originally assumed every HTTP response was JSON and hid the underlying server 500; it now displays meaningful errors.

## Known limitations and manual acceptance

- Existing employer-provided synthetic source files are **not** published in this repository. Reviewers need their original ZIP to reproduce the reference KPI pack.
- The optional Gemini connection uses a temporary browser-entered API key and localhost proxy. No full production auth, vault, multitenancy, rate limiter or external CRM integration is included.
- Offline multilingual extraction is heuristic; novel messages may remain `needs review`. LLM transport tests run offline with mocks, not live quotas.
- The KPI artifact checked into the repo represents a **clean source-pack state**; a reviewer who accepts/rejects test leads can intentionally change their local working database.
- The author must verify first-person claims and honest time report in `PROCESS.md` and in the submission email. No screenshot can substitute for this final human approval.

See [README.md](README.md), [docs/REVIEWER_GUIDE.md](docs/REVIEWER_GUIDE.md), [docs/acceptance_matrix.md](docs/acceptance_matrix.md) and [KPI_PACK.md](KPI_PACK.md).
