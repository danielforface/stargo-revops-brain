"""Deterministic RevOps domain services. Untrusted text cannot override business rules."""
from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

TZ = ZoneInfo("Asia/Jerusalem")
WEEK_START = datetime(2026, 10, 4, tzinfo=TZ)
WEEK_END = datetime(2026, 10, 9, tzinfo=TZ)
TARGETS = {"qualified_leads": 25, "meetings_booked": 15, "meetings_held": 12, "opportunities_created": 5}
STATUSES = {"QL candidate", "QL", "excluded", "disqualified", "nurture", "suppressed", "needs review"}
FREE_DOMAINS = {"gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com", "aol.com", "proton.me", "protonmail.com"}
SUFFIXES = {"co.uk", "com.sg", "co.il", "org.uk", "com.au", "co.nz"}
VERTICALS = {"freight-forwarder", "carrier", "3pl", "trucking", "air-cargo", "ground-handling", "customs-broker", "shipper", "trade-finance"}
REGION_MAP = {"NL": "Benelux", "BE": "Benelux", "LU": "Benelux", "NETHERLANDS": "Benelux", "BELGIUM": "Benelux", "LUXEMBOURG": "Benelux", "SE": "Nordics", "NO": "Nordics", "DK": "Nordics", "FI": "Nordics", "IS": "Nordics", "UK": "UK", "GB": "UK", "UNITED KINGDOM": "UK", "DE": "DACH", "GERMANY": "DACH", "AT": "DACH", "CH": "DACH", "SG": "Singapore", "SINGAPORE": "Singapore", "US": "United States", "USA": "United States", "UNITED STATES": "United States", "IL": "Israel", "ISRAEL": "Israel"}
ROUTE = {"Benelux": "Dana", "Nordics": "Dana", "UK": "Leo", "DACH": "Leo", "Singapore": "Mei", "APAC": "Mei", "United States": "Sam", "Israel": "Noa"}
INTENTS = Literal["demo", "pricing", "pilot", "not interested", "unsubscribe", "auto-reply", "partnership", "investor", "job seeker", "other"]


def stamp(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone offset")
    return parsed.astimezone(TZ)


def in_week(value: str | datetime) -> bool:
    return WEEK_START <= stamp(value) < WEEK_END


def email_norm(value: str | None) -> str | None:
    if not value:
        return None
    result = value.strip().lower()
    if len(result) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[a-z]{2,}", result):
        return None
    return result


def linkedin_norm(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value.strip() if "://" in value else "https://" + value.strip())
    if parsed.hostname not in {"linkedin.com", "www.linkedin.com"}:
        return None
    segments = [x.lower() for x in parsed.path.strip("/").split("/") if x]
    if len(segments) < 2 or segments[0] != "in" or not re.fullmatch(r"[a-z0-9_-]+", segments[1]):
        return None
    return "linkedin.com/in/" + segments[1]


def domain_norm(value: str | None) -> str | None:
    if not value:
        return None
    host = value.strip().lower().removeprefix("www.")
    host = urlparse(host if "://" in host else "https://" + host).hostname or ""
    bits = host.split(".")
    if len(bits) < 2:
        return None
    size = 3 if ".".join(bits[-2:]) in SUFFIXES else 2
    return ".".join(bits[-size:])


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Inbound(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: str = Field(default_factory=lambda: "IN-" + uuid.uuid4().hex[:12])
    channel: str = Field(min_length=2, max_length=50)
    source: str | None = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    from_name: str = Field(min_length=2, max_length=160)
    from_email: str | None = None
    linkedin_url: str | None = None
    subject: str | None = None
    body: str = Field(min_length=2, max_length=20000)

    @field_validator("received_at")
    @classmethod
    def tz_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("received_at must include an explicit timezone")
        return value

    @field_validator("from_email")
    @classmethod
    def valid_email(cls, value: str | None) -> str | None:
        if value and not email_norm(value):
            raise ValueError("invalid email address")
        return email_norm(value)

    @field_validator("linkedin_url")
    @classmethod
    def valid_linkedin(cls, value: str | None) -> str | None:
        if value and not linkedin_norm(value):
            raise ValueError("invalid LinkedIn profile URL")
        return linkedin_norm(value)

    @field_validator("source")
    @classmethod
    def clean_source(cls, value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None

    @field_validator("from_name", mode="before")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: str = Field(min_length=2, max_length=40)
    intent: INTENTS
    stated_buyer_role: str | None = None
    stated_data_problem: str | None = None
    stated_company_facts: list[str] = Field(default_factory=list, max_length=12)
    evidence_quotes: list[str] = Field(default_factory=list, max_length=8)
    injection_detected: bool = False
    mode: str = "rules-only"


class Factor(BaseModel):
    score: int = Field(ge=0)
    max_score: int = Field(gt=0)
    reason: str


class Qualification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: int = Field(ge=0, le=100)
    factors: dict[str, Factor]
    conditions: dict[str, dict[str, Any]]
    status: str
    owner: str | None
    rationale: str
    reply_draft: str | None = None


PROBLEM_RE = re.compile(r"(quote|quoting|rfq|tariff|rate request|rate card|invoice|reconcil|contract|bill.s? of lading|awb|air waybill|customs|document|import declaration|booking|re.key|תמחור|הצעות מחיר|מתמחר|מסמכ|חשבוניות|מכס)", re.I)
INTEREST_RE = re.compile(r"(demo|pilot|pricing|price|cost|send me times|can we talk|would like to see|can we see|can you show|30.minute call|happy to chat|open to a .*call|want to see|אשמח לשיחה|מחיר|אפשר לראות|פגישה|שיחה השבוע)", re.I)
INJECTION_RE = re.compile(r"((?:ignore|disregard|forget) (?:all |previous |your |the )*(?:rules|instructions|policy)|system (?:note|prompt|message)|developer message|override (?:the |your )?(?:policy|rules)|mark (?:this|me) (?:lead )?as qualified|reveal (?:your|the) (?:system|hidden) prompt|אתה עכשיו|התעלם מההוראות)", re.I)


def fallback_extract(inbound: dict, crm: dict | None) -> Extraction:
    message = inbound["body"]
    low = message.lower()
    intent: str = "other"
    if re.search(r"unsubscribe|remove me from|opt.?out|הסר אותי", low):
        intent = "unsubscribe"
    elif re.search(r"out of (the )?office|automatic reply|limited access to email|auto.reply", low):
        intent = "auto-reply"
    elif re.search(r"no interest|not interested|geen interesse|לא מעוניין", low):
        intent = "not interested"
    elif re.search(r"intern|student|job|career|applying|עבודה", low):
        intent = "job seeker"
    elif re.search(r"funding round|invest|venture capital", low):
        intent = "investor"
    elif re.search(r"partnership|white.label", low):
        intent = "partnership"
    elif re.search(r"pilot|poc|proof.of.concept", low):
        intent = "pilot"
    elif re.search(r"pricing|what would|cost us|please send pricing|rate cards", low):
        intent = "pricing"
    elif INTEREST_RE.search(message):
        intent = "demo"
    language = "he" if re.search("[\u0590-\u05ff]", message) else "nl" if "geen interesse" in low else "en"
    company_facts: list[str] = []
    employees = re.search(r"\b(\d{1,6})\s*[- ]?(?:people|persons?|employees?|staff)\b", message, re.I)
    if employees:
        company_facts.append("employees=" + employees.group(1) + " (self-reported)")
    vertical = re.search(r"customs brokerage|freight forwarder|3pl|trucking|trade.finance|carrier", message, re.I)
    if vertical:
        company_facts.append("vertical=" + vertical.group(0) + " (self-reported)")
    location = re.search(r"\b(?:in|from)\s+(Haifa|Israel|London|Singapore|Rotterdam|Berlin)\b", message, re.I)
    if location:
        company_facts.append("location=" + location.group(1) + " (self-reported)")
    sentence_parts = re.split(r"(?<=[.!?])\s+", message)
    evidence = [part[:260] for part in sentence_parts if PROBLEM_RE.search(part) or INTEREST_RE.search(part)][:5]
    if not evidence and message:
        evidence = [message[:220]]
    # Unseen messages may state a buyer role; do not treat it as verified CRM data.
    role = (crm or {}).get("job_title")
    if not role:
        role_match = re.search(
            r"\b(?:head of (?:pricing|operations|procurement|finance|digital)|"
            r"(?:pricing|operations|procurement|commercial|finance|digital) (?:manager|director)|"
            r"(?:chief (?:operating|financial) officer)|COO|CFO|"
            r"(?:owner|founder) of (?:the |our )?(?:company|business)|I own (?:the |our )?(?:company|business))\b",
            message, re.I)
        if role_match:
            role = role_match.group(0)
        elif re.search(r"(?:מנהלת?|ראש) (?:מחלקת )?(?:תפעול|רכש|כספים|תמחור)", message):
            role = "Operations Manager (self-reported, Hebrew)"
    return Extraction(language=language, intent=intent, stated_buyer_role=role,
        stated_data_problem=(PROBLEM_RE.search(message).group(0) if PROBLEM_RE.search(message) else None),
        stated_company_facts=company_facts, evidence_quotes=evidence,
        injection_detected=bool(INJECTION_RE.search(message)))


def vertical_norm(raw: str | None) -> str:
    v = (raw or "").strip().lower().replace("_", "-").replace(" ", "-")
    return {"freight-forwarder": "freight-forwarder", "freight-forwarding": "freight-forwarder", "air-cargo": "air-cargo", "customs-brokerage": "customs-broker", "customs-broker": "customs-broker", "trade-finance": "trade-finance", "3pl": "3pl"}.get(v, v)


def buyer_role(title: str | None, employee_count: int | None) -> bool:
    if not title:
        return False
    t = title.lower()
    if not re.search(r"pricing|operations|procurement|commercial|finance|digital|transportation|customs|managing director|\bcoo\b|\bcfo\b|vp operations|owner|founder", t):
        return False
    return bool(re.search(r"head|director|manager|chief|\bvp\b|\bcoo\b|\bcfo\b", t)) or (bool(re.search(r"owner|founder", t)) and employee_count is not None and employee_count < 200)


def derive_company(crm: dict | None, ext: Extraction) -> dict:
    company = dict(crm or {})
    # Self-reported values are separate from verified CRM facts and never inferred from a free email.
    facts = ext.stated_company_facts
    for item in facts:
        if item.startswith("employees=") and not company.get("employees"):
            company["employees"] = item.split("=", 1)[1].split(" ", 1)[0]
            company["_employees_unverified"] = True
        if item.startswith("vertical=") and not company.get("vertical"):
            company["vertical"] = item.split("=", 1)[1].split(" (", 1)[0]
            company["_vertical_unverified"] = True
        if item.startswith("location=") and not company.get("country"):
            company["country"] = item.split("=", 1)[1].split(" (", 1)[0]
            company["_region_unverified"] = True
    return company


def assess(inbound: dict, crm: dict | None, extraction: Extraction, decisions: list[dict], first_inbound: str | None = None) -> Qualification:
    c = derive_company(crm, extraction)
    employees = int(c["employees"]) if str(c.get("employees") or "").isdigit() else None
    vertical = vertical_norm(c.get("vertical"))
    region = REGION_MAP.get(str(c.get("country", "")).upper())
    # Fallback geography for self-reported statements only; not based on email locality.
    if not region:
        region = {"haifa":"Israel", "london":"UK", "berlin":"DACH", "rotterdam":"Benelux"}.get(str(c.get("country", "")).lower())
    fit = vertical in VERTICALS and employees is not None and employees >= 20 and region is not None
    buyer = buyer_role(extraction.stated_buyer_role or c.get("job_title"), employees)
    problem = bool(extraction.stated_data_problem)
    interest = extraction.intent in {"demo", "pricing", "pilot"} and bool(INTEREST_RE.search(inbound["body"]))
    accepted = any(d["decision"] == "accepted" for d in decisions)
    conditions = {
        "company_fit": {"met": fit, "known": bool(vertical and employees is not None and region), "evidence": f"vertical={vertical or 'unknown'}; employees={employees if employees is not None else 'unknown'}; region={region or 'unknown'}", "unverified": bool(c.get("_employees_unverified") or c.get("_vertical_unverified") or c.get("_region_unverified"))},
        "relevant_buyer": {"met": buyer, "known": bool(extraction.stated_buyer_role or c.get("job_title")), "evidence": extraction.stated_buyer_role or c.get("job_title") or "unknown"},
        "specific_data_problem": {"met": problem, "known": bool(extraction.stated_data_problem), "evidence": extraction.stated_data_problem or "not evidenced"},
        "expressed_interest": {"met": interest, "known": bool(INTEREST_RE.search(inbound["body"]) or extraction.intent in {"not interested", "unsubscribe"}), "evidence": extraction.intent},
        "sales_acceptance": {"met": accepted, "known": True, "evidence": [d["id"] for d in decisions if d["decision"] == "accepted"]},
    }
    weights = {"company_fit": 25, "relevant_buyer": 20, "specific_data_problem": 20, "expressed_interest": 25, "evidence_quality": 10}
    factors = {name: Factor(score=(maximum if conditions[name]["met"] else 0), max_score=maximum, reason=conditions[name]["evidence"] if isinstance(conditions[name]["evidence"], str) else "decision") for name, maximum in weights.items() if name != "evidence_quality"}
    factors["evidence_quality"] = Factor(score=min(10, len(extraction.evidence_quotes) * 5), max_score=10, reason="Grounded excerpts available")
    score = sum(f.score for f in factors.values())
    current_decision = sorted(decisions, key=lambda d: (stamp(d["decided_at"]), d["id"]))[-1] if decisions else None
    owner = ROUTE.get(region, "Triage queue")
    # Suppression outranks ordinary account ownership, even for existing customers.
    if extraction.intent == "unsubscribe":
        status, owner = "suppressed", None
    elif extraction.injection_detected:
        status = "needs review"
    elif c.get("is_customer") in ("true", "True", True) or (c.get("open_deal_id") and c.get("open_deal_created") and first_inbound and stamp(c["open_deal_created"] + "T00:00:00+03:00") < stamp(first_inbound) and (not decisions or stamp(c["open_deal_created"] + "T00:00:00+03:00") < min(stamp(d["decided_at"]) for d in decisions))):
        owner = c.get("owner") or owner
        status = "excluded"
    elif extraction.intent == "investor":
        status, owner = "excluded", "Founders"
    elif extraction.intent in {"job seeker", "partnership", "auto-reply"} or vertical in {"investor", "software-vendor"}:
        status, owner = "excluded", None
    elif extraction.intent == "not interested":
        status, owner = "nurture", owner
    elif current_decision and current_decision["decision"] == "rejected":
        status, owner = "disqualified", None
    elif all(conditions[k]["met"] for k in conditions):
        status = "QL"
    elif all(conditions[k]["met"] for k in ("company_fit", "relevant_buyer", "specific_data_problem", "expressed_interest")):
        status = "QL candidate"
    elif extraction.intent in {"demo", "pilot", "pricing"}:
        status = "needs review" if not (fit and buyer) else "nurture"
    else:
        status = "nurture"
    draft = None
    if status not in {"suppressed", "excluded", "disqualified", "needs review"} and extraction.intent in {"demo", "pilot", "pricing"}:
        draft = "Thank you for reaching out. We can arrange a conversation with the relevant team. Please share a convenient time. (Draft only — human approval required.)"
    return Qualification(score=score, factors=factors, conditions=conditions, status=status, owner=owner, rationale=f"{extraction.intent}; {sum(bool(x['met']) for x in conditions.values())}/5 QL gates evidenced; owner={owner or 'none'}", reply_draft=draft)


class Store:
    """One SQLite source of truth; seed rows upsert, human actions append-only."""

    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS contacts (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS inbound (id TEXT PRIMARY KEY, contact_id TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, contact_id TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS pipeline (id TEXT PRIMARY KEY, contact_id TEXT, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS analysis (inbound_id TEXT PRIMARY KEY, extraction TEXT, qualification TEXT, error TEXT, mode TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS rejected_seed (id TEXT PRIMARY KEY, reason TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_inbound_contact ON inbound(contact_id);
        CREATE INDEX IF NOT EXISTS idx_decisions_contact ON decisions(contact_id);
        """)
        self.db.commit()

    def close(self):
        self.db.close()

    def put(self, table: str, record_id: str, payload: dict, contact_id: str | None = None) -> None:
        if table == "contacts":
            self.db.execute("INSERT OR IGNORE INTO contacts VALUES (?,?)", (record_id, json.dumps(payload)))
        elif table in {"inbound", "decisions", "pipeline"}:
            self.db.execute(f"INSERT OR IGNORE INTO {table} VALUES (?,?,?)", (record_id, contact_id, json.dumps(payload, default=str)))
        elif table == "meta":
            self.db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (record_id, json.dumps(payload)))
        else:
            raise ValueError("invalid table")

    def items(self, table: str) -> list[dict]:
        if table not in {"contacts", "inbound", "decisions", "pipeline"}:
            raise ValueError("invalid table")
        rows = self.db.execute(f"SELECT * FROM {table}").fetchall()
        return [dict(json.loads(row["payload"]), **({"_contact_id": row["contact_id"]} if "contact_id" in row.keys() else {})) for row in rows]

    def contact_for(self, email: str | None, linkedin: str | None) -> tuple[str, dict | None]:
        e, li = email_norm(email), linkedin_norm(linkedin)
        for c in self.items("contacts"):
            if (e and email_norm(c.get("email")) == e) or (li and linkedin_norm(c.get("linkedin_url")) == li):
                return c["record_id"], c
        # Stable identity for new people; never use company or person's name.
        cid = "EXT-" + uuid.uuid5(uuid.NAMESPACE_URL, e or li or str(uuid.uuid4())).hex[:16]
        return cid, None

    def seed(self, source_dir: str) -> dict:
        path = Path(source_dir)
        with (path / "crm_export.csv").open(newline="", encoding="utf-8-sig") as fh:
            for c in csv.DictReader(fh):
                c["email"] = email_norm(c.get("email")) or ""
                c["linkedin_url"] = linkedin_norm(c.get("linkedin_url")) or ""
                c["company_domain"] = domain_norm(c.get("company_domain")) or ""
                self.put("contacts", c["record_id"], c)
        data = json.loads((path / "gtm_events.json").read_text(encoding="utf8"))
        self.put("meta", "feed_status", data.get("feed_status", {}))
        for event in data["inbound"]:
            try:
                normalized = Inbound.model_validate(event).model_dump(mode="json")
                cid, _ = self.contact_for(event.get("from_email"), event.get("linkedin_url"))
                self.put("inbound", event["id"], normalized, cid)
            except (ValidationError, ValueError) as ex:
                # Store metadata only, never rejected raw messages in logs/audit.
                self.db.execute("INSERT OR IGNORE INTO rejected_seed VALUES (?,?)", (event.get("id", "unknown"), type(ex).__name__))
        for d in data["sales_decisions"]:
            cid, _ = self.contact_for(d.get("contact_email"), None)
            self.put("decisions", d["id"], d, cid)
        for p in data["pipeline_events"]:
            cid, _ = self.contact_for(p.get("contact_email"), None)
            self.put("pipeline", p["id"], p, cid)
        self.db.commit()
        return {"contacts": len(self.items("contacts")), "inbound": len(self.items("inbound")), "decisions": len(self.items("decisions")), "pipeline": len(self.items("pipeline")), "rejected": self.db.execute("SELECT count(*) FROM rejected_seed").fetchone()[0]}

    def ingest(self, inbound: Inbound) -> str:
        cid, c = self.contact_for(inbound.from_email, inbound.linkedin_url)
        if not c:
            # No assumption of company from a mail domain; attributes start unknown.
            self.put("contacts", cid, {"record_id": cid, "first_name": inbound.from_name, "last_name": "", "email": inbound.from_email or "", "linkedin_url": inbound.linkedin_url or "", "company_name": "", "vertical": "", "country": "", "employees": "", "is_customer": "false"})
        self.put("inbound", inbound.id, inbound.model_dump(mode="json"), cid)
        self.db.commit()
        return inbound.id

    def analyze(self, inbound_id: str, extractor=None) -> dict:
        row = self.db.execute("SELECT * FROM inbound WHERE id=?", (inbound_id,)).fetchone()
        if not row:
            raise KeyError(inbound_id)
        inbound = json.loads(row["payload"])
        cid = row["contact_id"]
        crm = next((c for c in self.items("contacts") if c["record_id"] == cid), None)
        messages = [m for m in self.items("inbound") if m["_contact_id"] == cid]
        earliest = min((m["received_at"] for m in messages), key=stamp)
        decisions = [d for d in self.items("decisions") if d["_contact_id"] == cid]
        try:
            extracted = extractor(inbound, crm) if extractor else fallback_extract(inbound, crm)
            extracted = Extraction.model_validate(extracted)
            # Evidence cannot be model-invented; validate each excerpt is in the original message.
            if any(quote not in inbound["body"] for quote in extracted.evidence_quotes):
                raise ValueError("ungrounded evidence quote")
            if INJECTION_RE.search(inbound["body"]):
                extracted.injection_detected = True
            outcome = assess(inbound, crm, extracted, decisions, earliest)
            result = {"extraction": extracted.model_dump(), "qualification": outcome.model_dump(), "error": None, "mode": extracted.mode}
        except (Exception) as ex:
            # Do not log raw message, email, exception string, prompts or keys.
            result = {"extraction": None, "qualification": {"score": 0, "factors": {}, "conditions": {}, "status": "needs review", "owner": (crm or {}).get("owner") or "Triage queue", "rationale": "Analysis unavailable; human review required", "reply_draft": None}, "error": type(ex).__name__, "mode": "failed"}
        self.db.execute("INSERT OR REPLACE INTO analysis VALUES (?,?,?,?,?)", (inbound_id, json.dumps(result["extraction"]) if result["extraction"] is not None else None, json.dumps(result["qualification"]), result["error"], result["mode"]))
        self.db.commit()
        return result

    def lead(self, inbound_id: str) -> dict:
        row = self.db.execute("SELECT * FROM inbound WHERE id=?", (inbound_id,)).fetchone()
        if not row:
            raise KeyError(inbound_id)
        inbound = json.loads(row["payload"])
        cid = row["contact_id"]
        crm = next((c for c in self.items("contacts") if c["record_id"] == cid), {})
        analysis = self.db.execute("SELECT * FROM analysis WHERE inbound_id=?", (inbound_id,)).fetchone()
        if not analysis:
            self.analyze(inbound_id)
            analysis = self.db.execute("SELECT * FROM analysis WHERE inbound_id=?", (inbound_id,)).fetchone()
        decisions = [d for d in self.items("decisions") if d["_contact_id"] == cid]
        outcome = json.loads(analysis["qualification"])
        if analysis["extraction"]:
            ex = Extraction.model_validate_json(analysis["extraction"])
            messages = [m for m in self.items("inbound") if m["_contact_id"] == cid]
            outcome = assess(inbound, crm, ex, decisions, min((m["received_at"] for m in messages), key=stamp)).model_dump()
        # Suppression applies to the identity across all channels, not just its unsubscribe event.
        if any(fallback_extract(m, crm).intent == "unsubscribe" for m in (x for x in self.items("inbound") if x["_contact_id"] == cid)):
            outcome["status"], outcome["owner"], outcome["reply_draft"] = "suppressed", None, None
        return {"inbound": inbound, "contact_id": cid, "contact": crm, "analysis": {"extraction": json.loads(analysis["extraction"]) if analysis["extraction"] else None, "qualification": outcome, "error": analysis["error"], "mode": analysis["mode"]}, "decisions": sorted(decisions, key=lambda x: x["decided_at"])}

    def leads(self) -> list[dict]:
        # The queue represents people, not messages; duplicate-channel touches are visible in detail.
        grouped: dict[str, list[dict]] = defaultdict(list)
        for m in self.items("inbound"):
            grouped[m["_contact_id"]].append(m)
        result = []
        for _, msgs in grouped.items():
            assessed = [self.lead(m["id"]) for m in msgs]
            # Keep an unsafe message visible if any event requires review. Otherwise prioritize
            # a qualified/strong-evidence message, with earliest touch as tie-breaker.
            chosen = sorted(assessed, key=lambda x: (x["analysis"]["qualification"]["status"] != "needs review", x["analysis"]["qualification"]["status"] != "QL", -x["analysis"]["qualification"]["score"], stamp(x["inbound"]["received_at"])))[0]
            chosen["touch_count"] = len(msgs)
            chosen["touches"] = [{"id":m["id"], "received_at":m["received_at"], "channel":m["channel"]} for m in sorted(msgs,key=lambda x:stamp(x["received_at"]))]
            result.append(chosen)
        return sorted(result, key=lambda x: (x["analysis"]["qualification"]["status"] != "needs review", -x["analysis"]["qualification"]["score"], stamp(x["inbound"]["received_at"])))

    def decide(self, inbound_id: str, decision: Literal["accepted", "rejected"], decided_at: str, actor: str, note: str = "") -> dict:
        lead = self.lead(inbound_id)
        cid = lead["contact_id"]
        if lead["analysis"]["qualification"]["status"] == "suppressed" and decision == "accepted":
            raise ValueError("suppressed contact cannot be accepted")
        decided = stamp(decided_at)
        entry = {"id": "SD-" + uuid.uuid4().hex[:14], "contact_email": lead["inbound"].get("from_email"), "decision": decision, "decided_by": actor, "decided_at": decided.isoformat(), "recorded_at": iso_now(), "note": note, "inbound_id": inbound_id, "analysis_mode": lead["analysis"]["mode"]}
        self.put("decisions", entry["id"], entry, cid)
        self.db.commit()
        return self.lead(inbound_id)

    def kpi(self) -> dict:
        inbound = self.items("inbound")
        decisions = self.items("decisions")
        pipeline = self.items("pipeline")
        contacts = {c["record_id"]: c for c in self.items("contacts")}
        by_contact: dict[str, list[dict]] = defaultdict(list)
        for m in inbound:
            by_contact[m["_contact_id"]].append(m)
        first_inbound = {cid: min(items, key=lambda m: stamp(m["received_at"])) for cid, items in by_contact.items()}
        by_dec: dict[str, list[dict]] = defaultdict(list)
        for d in decisions:
            by_dec[d["_contact_id"]].append(d)
        entries = {key: [] for key in TARGETS}
        expansion = {key: [] for key in TARGETS}
        by_source: dict[str, list[str]] = defaultdict(list)
        for cid, ds in by_dec.items():
            if cid not in first_inbound:
                continue
            acceptances = sorted((d for d in ds if d["decision"] == "accepted"), key=lambda d: stamp(d["decided_at"]))
            if not acceptances:
                continue
            first = acceptances[0]
            if not in_week(first["decided_at"]):
                continue
            # A rejection before week end supersedes a prior acceptance; never count duplicate acceptances.
            latest_week_decision = max((d for d in ds if stamp(d["decided_at"]) < WEEK_END), key=lambda d: stamp(d["decided_at"]), default=None)
            if not latest_week_decision or latest_week_decision["decision"] != "accepted":
                continue
            contact = contacts.get(cid, {})
            initial = first_inbound[cid]
            # Only evidence received on/before acceptance may qualify that decision.
            # Future messages cannot retroactively validate an earlier QL.
            gate_4 = any(
                all(
                    self.lead(m["id"])["analysis"]["qualification"].get("conditions", {}).get(k, {}).get("met", False)
                    for k in ("company_fit", "relevant_buyer", "specific_data_problem", "expressed_interest")
                )
                for m in by_contact[cid]
                if stamp(m["received_at"]) <= stamp(first["decided_at"])
            )
            if not gate_4:
                continue
            excluded, why = exclusion_reason(contact, first_inbound[cid]["received_at"], first["decided_at"])
            evidence = {"id": first["id"], "contact_id": cid, "name": initial["from_name"], "decided_at": first["decided_at"], "inbound_id": initial["id"], "source": initial.get("source") or "source not recorded", "rule": why or "five QL conditions met; first accepted decision in week"}
            if excluded:
                if why == "existing customer":
                    expansion["qualified_leads"].append(evidence)
                continue
            entries["qualified_leads"].append(evidence)
            by_source[evidence["source"]].append(cid)
        for p in pipeline:
            if not in_week(p["occurred_at"]):
                continue
            key = {"meeting_booked": "meetings_booked", "meeting_held": "meetings_held", "opportunity_created": "opportunities_created"}.get(p["type"])
            if not key:
                continue
            cid = p["_contact_id"]
            contact = contacts.get(cid, {})
            initial = first_inbound.get(cid)
            accepted_at = min((d["decided_at"] for d in by_dec.get(cid, []) if d["decision"] == "accepted"), key=stamp, default=None)
            excluded, why = exclusion_reason(contact, initial["received_at"] if initial else None, accepted_at)
            evidence = {"id": p["id"], "contact_id": cid, "occurred_at": p["occurred_at"], "type": p["type"], "rule": why or "event timestamp within reporting week"}
            (expansion if why == "existing customer" else entries if not excluded else None)[key].append(evidence) if (not excluded or why == "existing customer") else None
        feed = json.loads(self.db.execute("SELECT payload FROM meta WHERE name='feed_status'").fetchone()[0]) if self.db.execute("SELECT 1 FROM meta WHERE name='feed_status'").fetchone() else {}
        result = {name: {"actual": len(rows), "target": TARGETS[name], "variance": len(rows) - TARGETS[name], "records": rows} for name, rows in entries.items()}
        return {"period": {"start": WEEK_START.isoformat(), "end_exclusive": WEEK_END.isoformat(), "timezone": "Asia/Jerusalem"}, "metrics": result, "by_source": {k: {"actual": len(set(v)), "contact_ids": sorted(set(v))} for k,v in by_source.items()}, "feed_status": feed, "unknown_feeds": sorted(k for k,v in feed.items() if v != "received"), "expansion": {k: {"actual": len(v), "records": v} for k,v in expansion.items()}, "definition": "QL counted once by first accepted decision; source from earliest inbound. Meetings and opportunities by event timestamp. Unknown feeds are not zero."}


def exclusion_reason(c: dict, first_inbound: str | None, accepted_at: str | None) -> tuple[bool, str]:
    if c.get("is_customer") in (True, "true", "True"):
        return True, "existing customer"
    if c.get("open_deal_id") and c.get("open_deal_created") and first_inbound and accepted_at:
        created = stamp(c["open_deal_created"] + "T00:00:00+03:00")
        if created < stamp(first_inbound) and created < stamp(accepted_at):
            return True, "pre-existing open deal"
    return False, ""
