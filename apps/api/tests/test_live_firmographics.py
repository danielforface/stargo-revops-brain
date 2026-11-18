"""Synthetic regressions: model omissions and inventions never rewrite ICP history."""
import json
import pytest
import gemini
from engine import Store, Inbound, assess, fallback_extract

KEY = "AQ." + "S" * 45
MODEL = gemini.DEFAULT_MODEL

def event(body=None):
    return {
        "id": "IN-SYNTHETIC", "from_name": "Synthetic Buyer",
        "from_email": "synthetic.buyer@gmail.com", "channel": "form_fill",
        "received_at": "2026-10-06T10:00:00+03:00",
        "source": "organic/referral",
        "body": body or ("I own a 43-person customs brokerage in Haifa. "
                         "We manually key import declarations from freight invoices. "
                         "Could you show me a demo and send pricing?"),
    }

def model_output(inbound, **changes):
    return {
        "language": "en", "intent": "pricing", "stated_buyer_role": "owner",
        "stated_data_problem": "We manually key import declarations from freight invoices",
        "stated_company_facts": [], "injection_detected": False,
        "evidence_quotes": inbound["body"].split(". ")[:2] +
             ["Could you show me a demo and send pricing?"],
    } | changes

def test_live_model_omits_firmographics_but_source_has_them(monkeypatch):
    msg=event()
    monkeypatch.setattr(gemini, "_generate", lambda *_a,**_k: model_output(msg))
    ext=gemini.extract(KEY, MODEL, msg, None)
    assert "employees=43 (self-reported)" in ext.stated_company_facts
    assert "vertical=customs brokerage (self-reported)" in ext.stated_company_facts
    assert "location=Haifa (self-reported)" in ext.stated_company_facts
    q=assess(msg,None,ext,[],msg["received_at"])
    assert q.status=="QL candidate" and q.owner=="Noa"
    assert q.conditions["company_fit"]["unverified"]
    assert q.score==100

@pytest.mark.parametrize("fake", ["employees=70","vertical=trade-finance"])
def test_model_invented_icp_fact_is_rejected(monkeypatch,fake):
    msg=event()
    monkeypatch.setattr(gemini,"_generate",lambda *_a,**_k:model_output(msg,stated_company_facts=[fake]))
    with pytest.raises(gemini.GeminiError,match="unsupported"):
        gemini.extract(KEY, MODEL, msg, None)

def test_supported_model_facts_are_normalized(monkeypatch):
    msg=event()
    monkeypatch.setattr(gemini,"_generate",lambda *_a,**_k:model_output(
        msg,stated_company_facts=["employees=43","vertical=customs-brokerage"]))
    assert gemini.extract(KEY,MODEL,msg,None).stated_company_facts[0]=="employees=43 (self-reported)"

def test_unverified_model_buyer_role_is_not_assumed(monkeypatch):
    msg=event("We reconcile freight invoices. Can we see a demo?")
    monkeypatch.setattr(gemini,"_generate",lambda *_a,**_k:model_output(
        msg,stated_buyer_role="Chief Financial Officer",stated_data_problem="freight invoices",
        evidence_quotes=["We reconcile freight invoices.","Can we see a demo?"]))
    assert gemini.extract(KEY,MODEL,msg,None).stated_buyer_role is None

def test_model_cannot_invent_interest_from_unrelated_quote():
    msg=event("We process freight invoices every day.")
    ext=fallback_extract(msg,None)
    ext.intent="demo"
    q=assess(msg,None,ext,[],msg["received_at"])
    assert not q.conditions["expressed_interest"]["met"]

def test_model_cannot_invent_problem_from_interest_only():
    msg=event("Hello. Can we see a demo?")
    ext=fallback_extract(msg,None)
    ext.stated_data_problem="carrier invoice reconciliation"
    q=assess(msg,None,ext,[],msg["received_at"])
    assert not q.conditions["specific_data_problem"]["met"]

def test_unsubscribe_outweighs_live_model_guess(monkeypatch):
    msg=event("Unsubscribe me now. Please remove me from this list.")
    monkeypatch.setattr(gemini,"_generate",lambda *_a,**_k:model_output(
        msg,intent="demo",stated_buyer_role=None,stated_data_problem=None,
        evidence_quotes=["Unsubscribe me now."]))
    ext=gemini.extract(KEY,MODEL,msg,None)
    assert ext.intent=="unsubscribe"
    assert assess(msg,None,ext,[],msg["received_at"]).status=="suppressed"

def test_historical_ql_is_unchanged_after_live_model_failure(tmp_path,monkeypatch):
    msg=event()
    store=Store(str(tmp_path/"synthetic.sqlite3"))
    obj=Inbound.model_validate(msg)
    store.ingest(obj)
    monkeypatch.setattr(gemini,"_generate",lambda *_a,**_k:model_output(msg))
    store.analyze(obj.id,lambda m,c:gemini.extract(KEY,MODEL,m,c))
    assert store.lead(obj.id)["analysis"]["qualification"]["status"]=="QL candidate"
    store.decide(obj.id,"accepted","2026-10-07T12:00:00+03:00","Synthetic Reviewer")
    assert store.kpi()["metrics"]["qualified_leads"]["actual"]==1
    store.analyze(obj.id,lambda *_:(_ for _ in ()).throw(ValueError("failure")))
    assert store.lead(obj.id)["analysis"]["qualification"]["status"]=="needs review"
    assert store.kpi()["metrics"]["qualified_leads"]["actual"]==1
    frozen=json.loads(store.db.execute("SELECT evidence_json FROM decision_evidence").fetchone()[0])
    assert frozen["eligible"] and frozen["conditions"]["company_fit"]["unverified"]
    store.close()
    again=Store(str(tmp_path/"synthetic.sqlite3"))
    assert again.kpi()["metrics"]["qualified_leads"]["actual"]==1
    again.close()

def test_hebrew_self_reported_company_is_source_grounded():
    msg=event("אני בעל של עמילות מכס בחיפה עם 43 עובדים. "
              "אנחנו מקלידים חשבוניות ידנית. אפשר לראות הדגמה בפגישה?")
    ext=fallback_extract(msg,None)
    q=assess(msg,None,ext,[],msg["received_at"])
    assert ext.language=="he" and q.status=="QL candidate"
    assert q.conditions["company_fit"]["unverified"] and q.owner=="Noa"

def test_dutch_self_reported_company_is_source_grounded():
    msg=event("Ik ben eigenaar van een expediteur met 43 medewerkers in Rotterdam. "
              "Wij controleren facturen handmatig. Kunnen we een demo plannen?")
    ext=fallback_extract(msg,None)
    q=assess(msg,None,ext,[],msg["received_at"])
    assert q.status=="QL candidate" and q.owner=="Dana"
