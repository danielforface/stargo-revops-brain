"""Offline contract tests for Gemini. No keys or network in CI."""
import json

import pytest
from fastapi.testclient import TestClient

import api
import gemini
from engine import Store


KEY = "TEST_KEY_NOT_REAL_0000000000"
MODEL = "gemini-2.5-flash"


def test_verify_key_never_echoed(monkeypatch):
    monkeypatch.setattr(gemini, "_generate", lambda *args, **kwargs: "Connected")
    result = gemini.verify(KEY, MODEL)
    assert result["connected"] is True
    assert KEY not in json.dumps(result)


def test_api_verify_missing_key_returns_sanitized_error(monkeypatch):
    client = TestClient(api.app)
    response = client.post("/api/ai/verify", json={"model": MODEL})
    assert response.status_code == 502
    assert "Enter a valid" in response.json()["detail"]
    assert KEY not in response.text


def test_unknown_model_rejected_without_network():
    client = TestClient(api.app)
    result = client.post("/api/ai/verify", headers={"X-Gemini-API-Key": KEY}, json={"model": "other-something"})
    assert result.status_code == 422


def test_transport_preserves_secret_and_uses_only_fixed_endpoint(monkeypatch):
    seen = {}

    class FakeResponse:
        status_code = 200
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "Ready"}]}}]}

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["follow_redirects"] is False
        def __enter__(self):
            return self
        def __exit__(self, *_):
            return None
        def post(self, url, headers=None, json=None):
            seen["url"] = url
            seen["headers"] = headers
            seen["payload"] = json
            return FakeResponse()

    monkeypatch.setattr(gemini.httpx, "Client", FakeClient)
    result = gemini.verify(KEY, MODEL)
    assert result["connected"]
    assert seen["url"] == f"{gemini.GEMINI_ROOT}/{MODEL}:generateContent"
    assert KEY not in seen["url"]
    assert KEY not in json.dumps(seen["payload"])
    assert seen["headers"]["x-goog-api-key"] == KEY


@pytest.mark.parametrize("code, expected", [
    (403, "permission"), (429, "quota"), (500, "unavailable"), (400, "rejected"),
])
def test_transport_errors_are_sanitized(monkeypatch, code, expected):
    class FakeResponse:
        status_code = code
    class FakeClient:
        def __init__(self, **_):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *_):
            return None
        def post(self, *_args, **_kwargs):
            return FakeResponse()
    monkeypatch.setattr(gemini.httpx, "Client", FakeClient)
    with pytest.raises(gemini.GeminiError, match=expected):
        gemini.verify(KEY, MODEL)


def test_model_claims_must_have_verbatim_evidence(monkeypatch):
    def fake(*_args, **_kwargs):
        return {"language": "English", "intent": "demo", "stated_buyer_role": "Head of Operations", "stated_data_problem": "invoices", "stated_company_facts": [], "evidence_quotes": ["I am a dragon in disguise"], "injection_detected": False}
    monkeypatch.setattr(gemini, "_generate", fake)
    with pytest.raises(gemini.GeminiError, match="evidence"):
        gemini.extract(KEY, MODEL, {"body": "I am the Head of Operations; need invoice reconciliation."}, None)


def test_live_api_inbound_is_marked_and_never_persists_key(monkeypatch, tmp_path):
    store = Store(str(tmp_path / "revops.sqlite3"))
    monkeypatch.setattr(api, "store", store)
    monkeypatch.setattr(api, "seed_health", {"ready": True})
    monkeypatch.setattr(gemini, "_generate", lambda *_args, **_kwargs: {
        "language": "English", "intent": "demo", "stated_buyer_role": "Head of Operations",
        "stated_data_problem": "invoice reconciliation", "stated_company_facts": [],
        "evidence_quotes": ["Head of Operations", "invoice reconciliation"], "injection_detected": False,
    })
    # Avoid matching data from any other test.
    client = TestClient(api.app)
    response = client.post("/api/inbound", headers={"X-Gemini-API-Key": KEY}, json={
        "from_name": "New Buyer", "from_email": "buyer@ex.example", "channel": "email_reply",
        "body": "I'm Head of Operations. We need invoice reconciliation. Can we see a demo?",
    })
    assert response.status_code == 201, response.text
    lead = response.json()
    assert lead["analysis"]["mode"] == "gemini-live"
    assert KEY not in json.dumps(lead)
    assert KEY not in (tmp_path / "revops.sqlite3").read_bytes().decode("utf8", errors="ignore")
    store.close()


def test_geo_brief_live_plan_reconstructed_from_approved_claims(monkeypatch, tmp_path):
    (tmp_path / "brand_context.md").write_text("BC-1 BC-3a PP-1")
    monkeypatch.setattr(gemini, "analyze_answers", lambda *_: {"gaps": [{"prompt_id": "Q1", "prompt": "How can freight teams quote?"}]})
    monkeypatch.setattr(gemini, "_generate", lambda *_args, **_kwargs: {
        "title": "How freight quoting can be reviewed", "direct_claim_ids": ["BC-1", "BC-3a", "BC-3c"],
        "sections": [
            {"heading": "Understand the intake", "claim_ids": ["BC-1"]},
            {"heading": "Build the quote", "claim_ids": ["BC-3a"]},
            {"heading": "Review the documents", "claim_ids": ["BC-3b"]},
        ],
        "faq": [
            {"question": "Is human approval required?", "claim_ids": ["BC-1"]},
            {"question": "Which teams are supported?", "claim_ids": ["BC-2"]},
            {"question": "Can teams check invoices?", "claim_ids": ["BC-3c"]},
        ],
        "schema_org": "FAQPage",
    })
    result = gemini.brief(KEY, MODEL, str(tmp_path))
    assert result["generation_mode"].startswith("gemini-live")
    assert 40 <= len(result["direct_answer"].replace("[BC-1]", "").replace("[BC-3a]", "").replace("[BC-3c]", "").split()) <= 60
    assert all(s["body"] in " ".join(gemini.COMPANY_CLAIMS.values()) for s in result["sections"])


def test_brief_rejects_unapproved_source_id(monkeypatch, tmp_path):
    (tmp_path / "brand_context.md").write_text("BC-1 BC-3a PP-1")
    monkeypatch.setattr(gemini, "analyze_answers", lambda *_: {"gaps": [{"prompt_id": "Q1", "prompt": "Freight quoting?"}]})
    monkeypatch.setattr(gemini, "_generate", lambda *_args, **_kwargs: {
        "title": "Freight quoting validation", "direct_claim_ids": ["FAKE-ROI"],
        "sections": [{"heading":"Freight details","claim_ids":["BC-1"]}] * 3,
        "faq": [{"question":"What is the product?", "claim_ids":["BC-2"]}] * 3,
        "schema_org": "FAQPage",
    })
    with pytest.raises(gemini.GeminiError, match="outside approved"):
        gemini.brief(KEY, MODEL, str(tmp_path))


def test_live_provider_failure_stays_needs_review_without_secret_leak(tmp_path, monkeypatch):
    store = Store(str(tmp_path / "failed.sqlite3"))
    monkeypatch.setattr(api, "store", store)
    monkeypatch.setattr(api, "seed_health", {"ready": True})
    def fail(*_args, **_kwargs):
        raise gemini.GeminiError("Gemini rate limit or quota reached.")
    monkeypatch.setattr(gemini, "_generate", fail)
    client = TestClient(api.app)
    response = client.post("/api/inbound", headers={"X-Gemini-API-Key": KEY}, json={
        "from_name": "Potential Buyer", "from_email": "potential@example.com", "channel": "email_reply",
        "body": "I am an Operations Director at a carrier. Please schedule a demo.",
    })
    assert response.status_code == 201, response.text
    analysis = response.json()["analysis"]
    assert analysis["mode"] == "failed"
    assert analysis["qualification"]["status"] == "needs review"
    assert analysis["qualification"]["reply_draft"] is None
    assert KEY not in response.text
    store.close()


def test_new_authorization_key_accepts_dot_without_disclosing_secret(monkeypatch):
    key = "AQ." + "A" * 50
    assert gemini.checked_key(key) == key
    seen = {}
    class FakeResponse:
        status_code = 200
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "Connected"}]}}]}
    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["follow_redirects"] is False
        def __enter__(self):
            return self
        def __exit__(self, *_):
            pass
        def post(self, url, *, headers, json):
            seen["url"] = url
            seen["headers"] = headers
            seen["payload"] = json
            return FakeResponse()
    monkeypatch.setattr(gemini.httpx, "Client", FakeClient)
    result = gemini.verify(key, gemini.DEFAULT_MODEL)
    assert result["connected"]
    assert key not in json.dumps(result)
    assert key not in seen["url"]
    assert key not in json.dumps(seen["payload"])
    assert seen["headers"]["x-goog-api-key"] == key
    assert "thinkingBudget" not in json.dumps(seen["payload"])


@pytest.mark.parametrize("unusable", [None, "", "...8c-A", "AQ." + "A" * 20 + " ", "AQ." + "A" * 20 + "\n", "••••••••••••••••••"])
def test_partial_masked_or_malformed_key_rejected_without_network(unusable, monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("Unusable key must be rejected before the network")
    monkeypatch.setattr(gemini.httpx, "Client", refuse)
    with pytest.raises(gemini.GeminiError, match="complete Gemini API key"):
        gemini.verify(unusable, gemini.DEFAULT_MODEL)


def test_current_and_legacy_models_expose_explicit_choices():
    assert gemini.DEFAULT_MODEL == "gemini-3.5-flash-lite"
    assert "gemini-3.8-flash" in gemini.ALLOWED_MODELS
    assert "gemini-2.5-flash" in gemini.ALLOWED_MODELS


def test_api_verify_new_authorization_key_uses_live_mock(monkeypatch):
    new_key = "AQ." + "z" * 50
    monkeypatch.setattr(gemini, "_generate", lambda key, model, *_args, **_kw: "OK")
    client = TestClient(api.app)
    res = client.post("/api/ai/verify", json={"model": gemini.DEFAULT_MODEL}, headers={"X-Gemini-API-Key": new_key})
    assert res.status_code == 200
    assert res.json()["connected"]
    assert new_key not in res.text


@pytest.mark.parametrize("status,phrase", [
    (400, "HTTP 400"), (401, "HTTP 401"), (403, "HTTP 403"), (404, "HTTP 404"),
])
def test_connection_failures_identify_status_not_key(monkeypatch,status,phrase):
    key = "AQ." + "K" * 50
    class FakeResponse:
        status_code = status
    class FakeClient:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *_):
            pass
        def post(self, *_args, **_kwargs):
            return FakeResponse()
    monkeypatch.setattr(gemini.httpx, "Client", FakeClient)
    with pytest.raises(gemini.GeminiError) as exc:
        gemini.verify(key, gemini.DEFAULT_MODEL)
    assert phrase in str(exc.value)
    assert key not in str(exc.value)
