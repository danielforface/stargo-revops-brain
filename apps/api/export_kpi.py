"""Export the authoritative, traceable KPI report as Markdown (not hand-entered numbers)."""
from __future__ import annotations
import os
from pathlib import Path
from engine import Store
from geo import analyze_answers

ROOT = Path(__file__).resolve().parents[2]
DB = Path(os.environ.get("STARGO_DB_PATH", str(ROOT / "runtime" / "revops.sqlite3")))


def render(report: dict, visibility: dict | None = None) -> str:
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
    lines += ["## Assumptions / boundaries", "", "- Source attribution is the earliest inbound event for a person matched by normalized email or LinkedIn ID.", "- QLs count once per person on first accepted decision date using the immutable evidence snapshot captured at that decision.", "- Pipeline events are counted by their own event timestamps; existing customer events appear in expansion.", "- Dates with `Z` are converted to Asia/Jerusalem before half-open window comparison.", "- The synthetic seed's malformed inbound `IN-019` is quarantined, not silently made into a lead.", "- The exported pack represents the local database at export time and may differ from the pristine submitted sample if operator decisions were recorded.", "", "## Note to CRO", ""]
    metric = report["metrics"]
    def against(name):
        row = metric[name]
        return f"{row['actual']} against {row['target']} (shortfall {max(0,row['target']-row['actual'])})"
    top = (visibility or {}).get("gaps", [])
    if top:
        gap = top[0]
        gap_summary = f"The top GEO gap is '{gap['prompt']}' (score {gap['score']}): low brand mentions and/or owned citations make vendor discovery less reliable."
        action = "Next week, publish one human-approved, BC/PP-cited answer page for this buyer question and recapture the same prompts to measure mentions and citations."
    else:
        gap_summary = "GEO snapshot was unavailable: the priority visibility gap is unknown, not zero."
        action = "Next week, restore the recorded answer feed before selecting an approved content action."
    note = (f"This reporting week delivered {against('qualified_leads')} QLs, "
            f"{against('meetings_booked')} meetings booked, "
            f"{against('meetings_held')} meetings held and "
            f"{against('opportunities_created')} opportunities. "
            f"Unavailable feeds: {', '.join(report.get('unknown_feeds', [])) or 'none'}. "
            f"{gap_summary} {action}")
    assert len(note.split()) <= 150, "CRO note must stay within the brief's 150-word limit"
    lines += [note, ""]
    return "\n".join(lines)


if __name__ == "__main__":
    if not DB.exists():
        raise SystemExit(f"Database not found at {DB}; start the API with the source data first")
    store = Store(str(DB))
    dest = ROOT / "KPI_PACK.md"
    data_dir = Path(os.environ.get("STARGO_DATA_DIR", str(ROOT / "data" / "private")))
    visibility = analyze_answers(str(data_dir)) if (data_dir / "ai_answers.json").exists() else None
    dest.write_text(render(store.kpi(), visibility), encoding="utf-8")
    print(f"Wrote {dest}")
    store.close()
