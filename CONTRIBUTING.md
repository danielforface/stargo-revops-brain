# Contributing

Thanks for improving the project. Contributions should make **business decisions more correct, auditable, or usable**, not add complexity for its own sake.

1. Open an issue describing the user-visible behavior, expected outcomes, boundary conditions and scope. Avoid putting employer-provided messages or personal data into issues.
2. Create a branch from `main`: `feat/<topic>`, `fix/<topic>`, `test/<topic>`, or `docs/<topic>`. No direct pushes to `main`.
3. Use focused commits such as `feat: persist sales decision audit` and add/adjust offline tests for any changed business policy.
4. Run `pytest -q apps/api/tests`, `python -m compileall -q apps/api`, `ruff check apps/api --select E4,E7,E9,F63,F7,F82`, and `cd apps/web && npm install && npm run build` before requesting review.
5. Keep public data synthetic and independently authored. Never commit `.env`, original employer files, SQLite runtimes, keys or PII.
6. Open a PR with problem, scope, tests, risks, evidence, contract/docs impact and rollback. Resolve review threads before merging.
7. Changes to QL policy, identity matching, KPI boundaries, agent schemas or security rules need owner review and dedicated regression tests; update ARCHITECTURE and the engineering walkthrough.
8. Document dependency additions and avoid external services in CI. Tests must run without a live LLM or external CRM.

The repository owner is the initial code owner. CODEOWNERS is advisory until branch protection and required reviews are enabled in GitHub settings.
