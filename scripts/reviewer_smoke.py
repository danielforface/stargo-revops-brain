"""Private pack acceptance smoke. Uses an isolated temporary database only.

Run `python scripts/reviewer_smoke.py` from the repo root after importing
source ZIP to git-ignored data/private. Does not contact an LLM or mutate the
operator's runtime database, and logs no names, emails or message contents.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from engine import Inbound, Store  # noqa: E402
from export_kpi import render  # noqa: E402
from geo import analyze_answers, build_brief  # noqa: E402


def main() -> int:
    source = ROOT / "data" / "private"
    if not all((source / name).exists() for name in ("crm_export.csv", "gtm_events.json", "ai_answers.json", "brand_context.md")):
        print("FAIL: private take-home pack missing; see README importer instructions")
        return 2
    with tempfile.TemporaryDirectory(prefix="stargo-review-") as temp:
        dbfile = Path(temp) / "demo.sqlite3"
        store = Store(str(dbfile))
        try:
            counts = store.seed(str(source))
            expected = {"contacts": 19, "inbound": 20, "decisions": 11, "pipeline": 12, "rejected": 1}
            assert counts == expected, "Seed count differs from supplied v2 pack"
            assert store.seed(str(source)) == expected, "Import was not idempotent"
            report = store.kpi()
            actual = {key: value["actual"] for key, value in report["metrics"].items()}
            expected_kpi = {"qualified_leads": 6, "meetings_booked": 4, "meetings_held": 3, "opportunities_created": 2}
            assert actual == expected_kpi, "Baseline KPI mismatches expected v2 pack"
            assert "historical-reactivation" in report["unknown_feeds"]
            state = analyze_answers(str(source))
            assert len(state["answers"]) == 24 and len(state["gaps"]) == 8
            assert 3 <= len(build_brief(str(source))["sections"]) <= 5
            # Simulate provider returning malformed JSON for a previously accepted lead.
            store.analyze("IN-011", lambda *_: {"language": "en", "intent": "fake-agent-output"})
            assert store.lead("IN-011")["analysis"]["qualification"]["status"] == "needs review"
            assert store.kpi()["metrics"]["qualified_leads"]["actual"] == 6, "Frozen QL evidence was overwritten"
            inbound = Inbound.model_validate({
                "channel": "email_reply", "from_name": "Synthetic Test Contact",
                "from_email": "smoke@example.com", "source": "organic/referral",
                "received_at": "2026-10-06T09:00:00+03:00",
                "body": "I'm the Head of Operations at a freight forwarder in Singapore with 65 employees. "
                        "We manually reconcile carrier invoices and contracts. Could we see a demo?",
            })
            uid = store.ingest(inbound)
            store.analyze(uid)
            store.decide(uid, "accepted", "2026-10-07T12:00:00+03:00", "Synthetic Reviewer")
            assert store.kpi()["metrics"]["qualified_leads"]["actual"] == 7
            store.decide(uid, "rejected", "2026-10-08T12:00:00+03:00", "Synthetic Reviewer")
            assert store.kpi()["metrics"]["qualified_leads"]["actual"] == 6
            markdown = render(store.kpi(), state)
            assert "6 against 25" in markdown and "## Note to CRO" in markdown
            store.close()
            replay = Store(str(dbfile))
            assert replay.kpi()["metrics"]["qualified_leads"]["actual"] == 6
            replay.close()
        finally:
            try:
                store.close()
            except Exception:
                pass
    print("PASS — private-pack seed/replay; 19 CRM, 20 inbound, 11 decisions, 12 pipeline, 1 rejected")
    print("PASS — QL/meetings/opportunities 6/4/3/2; unknown feeds preserved")
    print("PASS — Gemini-failure replay, historic Accept/Reject, restart and GEO contracts")
    print("No private input or operator SQLite was modified; no outbound network was used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
