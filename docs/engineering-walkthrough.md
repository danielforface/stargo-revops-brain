# Engineering walkthrough — live review preparation

1. **Start at `engine.py`**: Inbound → normalize identity by email/LinkedIn, never by company/name; SQLite has separate contacts, inbound, decisions, pipeline, analysis and source-status tables.
2. **Trace IN-002 (Pieter)**: CRM Commercial Director + freight carrier + document re-keying problem + call request are four objective gates. The recorded acceptance adds the fifth. An additional LinkedIn message is matched to the same person and is not a second QL.
3. **Trace IN-011 (Yossi)**: personal Gmail is not a company domain. The message itself self-reports a 40-person customs brokerage in Haifa; values are flagged unverified and need human acceptance.
4. **Trace IN-010 (injection)**: extraction marks untrusted instructions, so the status is `needs review`; the text cannot rewrite score weights, owner routing or policy.
5. **Trace UTC window**: `2026-10-08T21:30:00Z` is `2026-10-09T00:30:00+03:00` and excluded. Use `stamp()` and `in_week()` rather than comparing strings.
6. **Audit a KPI**: `Store.kpi()` selects first accepted decision per unique identity, excludes existing customers and prior open deals, and exposes each source identifier for drilldown; pipeline events use their own occurred time. Missing feeds stay `Unknown`.
7. **Trace GEO**: `geo.py` uses exact brand/competitor detection and owned citations from provided domains; the content brief is a labelled approved-context template, not ungrounded live copy.
8. **Explain failure**: Provider parse, timeout and malformed evidence errors are converted to persisted `needs review`; no auto-send or unintended network traffic.

## Questions to practice

- Why is human acceptance necessary but not sufficient?
- Why are two messages from the same company not automatically the same person?
- How can a new user decision change a past weekly report?
- Which timestamp decides whether a QL is in this week: inbound or acceptance?
- How would you replace SQLite and add migrations while preserving stable identity keys?

## Small change exercise (independent)

Introduce an alternate region mapping for a new supported territory in `REGION_MAP`, add a unit test for routing with `assess()`, and check that out-of-scope territories still route to Triage. No LLM or UI change should be necessary.
