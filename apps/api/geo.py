"""Read-only GEO analysis. Facts for briefs are from approved BC/PP claims only."""
from __future__ import annotations
import json
import re
from pathlib import Path
from urllib.parse import urlparse

COMPANY_CLAIMS = {
    "BC-1": "Stargo uses agentic AI to turn documents, emails and datasets into operational transactions; people approve agent drafts.",
    "BC-2": "Stargo serves forwarders, carriers, 3PLs, air-cargo and ground handlers, customs brokers, shippers and trade-finance teams.",
    "BC-3a": "The Rate Quoting Agent reads emailed rate requests and tariffs or contracts, then drafts quotes for approval.",
    "BC-3b": "Document Extraction validates structured fields from bills of lading, air waybills, invoices and customs paperwork for TMS/ERP.",
    "BC-3c": "Invoice and Contract Reconciliation matches carrier invoices to contracted rates and flags discrepancies.",
    "BC-3d": "Trade Document Checking validates trade documents for finance teams before funds move.",
    "PP-1": "A European forwarder pilot reduced median spot-quote turnaround from about three hours to under fifteen minutes.",
    "PP-2": "Document extraction pilots reached 97% field-level accuracy on bills of lading after human review.",
    "PP-3": "An air cargo handler removed manual AWB re-keying at two stations.",
}

def analyze_answers(source_dir: str) -> dict:
    payload = json.loads((Path(source_dir)/"ai_answers.json").read_text(encoding="utf8"))
    owned = set(payload["meta"]["own_domains"])
    competitors = payload["meta"]["known_competitors"]
    results = []
    by_prompt = {}
    for row in payload["answers"]:
        text = row["answer_text"]
        # Exact word boundary prevents e.g. StarGoTravel from being treated as the target.
        raw_mention = bool(re.search(r"(?<![A-Za-z0-9])stargo(?![A-Za-z0-9])", text, re.I))
        cited = any(any((host == domain or host.endswith("."+domain)) for domain in owned) for host in [(urlparse(u).hostname or "").lower().removeprefix("www.") for u in row.get("citations", [])])
        rivals = [c for c in competitors if re.search(r"(?<![a-z\d])" + re.escape(c) + r"(?![a-z\d])", text, re.I)]
        wrong_claim = bool(re.search(r"stargo.{0,100}(?:ocean carrier|holiday booking|travel company|shipping between|headquartered in rotterdam)", text, re.I))
        lookalike = bool(re.search(r"stargo.{0,90}(?:holiday booking|app with mixed reviews)", text, re.I))
        mentioned = raw_mention and not lookalike and not wrong_claim
        gap = row["priority"]*20 + (0 if mentioned else 22) + (0 if cited else 12) + min(12, len(rivals)*4) + (25 if wrong_claim else 0) + (15 if lookalike else 0)
        item = {**{k:row[k] for k in ("answer_id","prompt_id","prompt","cluster","priority","engine","citations")}, "mentioned": mentioned, "owned_citation": cited, "competitors": rivals, "wrong_claim": wrong_claim, "brand_confusion": lookalike, "gap_score": gap}
        results.append(item)
        by_prompt.setdefault(row["prompt_id"], {"prompt_id":row["prompt_id"], "prompt":row["prompt"], "priority":row["priority"], "engines":[], "score":0})
        by_prompt[row["prompt_id"]]["engines"].append(item)
        by_prompt[row["prompt_id"]]["score"] += gap
    gaps = sorted(by_prompt.values(), key=lambda x:(-x["score"], x["prompt_id"]))
    return {"answers":results,"gaps":gaps,"formula":"Per engine: buyer priority × 20 + missing mention 22 + missing owned citation 12 + competitor mention (4 each, max 12) + wrong claim 25 + brand confusion 15. Prompt score is sum across three engines.","own_domains":sorted(owned)}


def build_brief(source_dir: str) -> dict:
    state = analyze_answers(source_dir)
    top = state["gaps"][0]
    prompt = top["prompt"]
    cluster = top["engines"][0]["cluster"]
    category = "BC-3a" if cluster in {"rate-quoting", "quote-automation"} else "BC-3b" if cluster in {"document-extraction", "air-cargo"} else "BC-3c" if "reconcil" in cluster or "freight-audit" in cluster else "BC-3d" if "trade" in cluster else "BC-1"
    direct = "Stargo applies agentic AI to operational freight and trade workflows. Its agents turn incoming documents, emails and datasets into transactions, while people retain approval control. The relevant capability is described in the approved product context. Buyers should assess fit against their workflow, source formats and human review process, rather than unverified marketing claims."
    # Every sentence in generated content explicitly tagged to approved sources.
    sections = [
        {"heading":"What Stargo does", "body": COMPANY_CLAIMS["BC-1"], "citations":["BC-1"]},
        {"heading":"Relevant workflow", "body": COMPANY_CLAIMS[category], "citations":[category]},
        {"heading":"Who it is designed for", "body": COMPANY_CLAIMS["BC-2"], "citations":["BC-2"]},
        {"heading":"Operator oversight", "body":"People approve AI-generated operational drafts before they become transactions.","citations":["BC-1"]},
    ]
    faq = [
        {"question":"What does Stargo automate?", "answer":COMPANY_CLAIMS["BC-1"], "citations":["BC-1"]},
        {"question":"Who can use it?", "answer":COMPANY_CLAIMS["BC-2"], "citations":["BC-2"]},
        {"question":"Is human review available?", "answer":"Humans approve agents' drafts.","citations":["BC-1"]},
    ]
    return {"prompt_id":top["prompt_id"], "title":prompt.rstrip("?").capitalize() + "?", "direct_answer":direct + " [BC-1] [BC-2]", "sections":sections, "faq":faq, "schema_org":"FAQPage", "generation_mode":"approved-context template (offline; not live LLM)", "source_ids":list(COMPANY_CLAIMS), "warning":"No external model used; all factual claims require BC/PP provenance."}
