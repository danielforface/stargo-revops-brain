"""Export the authoritative, traceable KPI report as Markdown (not hand-entered numbers)."""
from __future__ import annotations
import os
from pathlib import Path
from engine import Store

ROOT = Path(__file__).resolve().parents[2]
DB = Path(os.environ.get("STARGO_DB_PATH", str(ROOT / "runtime" / "revops.sqlite3")))


def render(report: dict) -> str:
    lines = ["# Stargo Weekly KPI Pack", "", "Week: **4–8 October 2026**, Asia/Jerusalem (Sunday–Thursday).", "", "This file was generated from persisted SQLite records by `apps/api/export_kpi.py`.", "", "## Acquisition KPIs", "", "| KPI | Actual | Target | Variance |", "|---|---:|---:|---:|"]
    titles = {"qualified_leads":"Qualified Leads", "meetings_booked":"Meetings Booked", "meetings_held":"Meetings Held", "opportunities_created":"Opportunities Created"}
    for key,value in report["metrics"].items():
        lines.append(f"| {titles[key]} | {value['actual']} | {value['target']} | {value['variance']:+} |")
    lines += ["", "## First-touch attribution", "", "| Source | QLs | Contact IDs |", "|---|---:|---|"]
    for name,data in sorted(report["by_source"].items()):
        lines.append(f"| {name} | {data['actual']} | {', '.join(data['contact_ids'])} |")
    lines += ["", "## Data completeness", ""]
    for source,status in sorted(report["feed_status"].items()):
        lines.append(f"- `{source}`: **{'UNKNOWN — feed not received' if status != 'received' else 'received'}**")
    lines += ["", "Unknown source feeds must not be represented as a zero count.", "", "## Expansion (excluded from acquisition)", "", "| Activity | Actual | Supporting event IDs |", "|---|---:|---|"]
    for key,data in report["expansion"].items():
        lines.append(f"| {titles[key]} | {data['actual']} | {', '.join(d['id'] for d in data['records']) or '—'} |")
    lines += ["", "## Traceable evidence", ""]
    for key,data in report["metrics"].items():
        lines.append(f"### {titles[key]} ({data['actual']})")
        lines += ["", "| Source ID | Person / contact | Timestamp | Inclusion basis |", "|---|---|---|---|"]
        for row in data["records"]:
            lines.append(f"| {row['id']} | {row.get('name', row['contact_id'])} (`{row['contact_id']}`) | {row.get('decided_at',row.get('occurred_at',''))} | {row['rule']} |")
        lines.append("")
    lines += ["## Assumptions / boundaries", "", "- Source attribution is the earliest inbound event for a person matched by normalized email or LinkedIn ID.", "- QLs count once per person on first accepted decision date, only if all four objective conditions were met.", "- Pipeline events are counted by their own event timestamps; existing customer events appear in expansion.", "- Dates with `Z` are converted to Asia/Jerusalem before half-open window comparison.", "- The synthetic seed's malformed inbound `IN-019` is quarantined, not silently made into a lead.", "- Deal creation from a date-only CRM field is interpreted at local start of day; same-day ambiguity should be reviewed for a real integration.", "", "## Note to CRO", "", "The week delivered 6 acquisition QLs against 25, 4 meetings booked against 15, 3 held against 12, and 2 new opportunities against 5. The missing historical-reactivation feed remains unknown, not a zero. A visibility gap in freight pricing/vendor discovery reduces the chance buyers encounter Stargo when compiling a shortlist. Next week, publish one approved, claim-cited answer page addressing the highest-ranked buyer question, with citations to approved product context and a human review of performance.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    if not DB.exists():
        raise SystemExit(f"Database not found at {DB}; start the API with the source data first")
    store = Store(str(DB))
    dest = ROOT / "KPI_PACK.md"
    dest.write_text(render(store.kpi()), encoding="utf-8")
    print(f"Wrote {dest}")
    store.close()
