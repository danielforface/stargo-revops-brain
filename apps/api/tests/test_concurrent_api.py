"""Regression: browser startup issues concurrent independent API requests.

The Store holds one SQLite connection, so its public operations must serialize
through a reentrant lock even while qualification calls other Store methods.
"""
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

import api
from engine import Store
from test_engine import base_contact, base_event


def test_concurrent_startup_and_qualification_are_consistent(tmp_path, monkeypatch):
    store = Store(str(tmp_path / "parallel.sqlite3"))
    store.put("contacts", "C-1", base_contact())
    event = base_event()
    store.put("inbound", event["id"], event, "C-1")
    store.put("decisions", "D-1", {
        "id": "D-1", "decision": "accepted", "decided_at": "2026-10-06T10:00:00+03:00",
    }, "C-1")
    store.db.commit()
    monkeypatch.setattr(api, "store", store)
    monkeypatch.setattr(api, "seed_health", {"ready": True})
    client = TestClient(api.app, raise_server_exceptions=True)

    def get(endpoint):
        response = client.get(endpoint)
        assert response.status_code == 200, (endpoint, response.text)
        return endpoint, response.json()

    endpoints = ["/api/leads", "/api/kpi/week", "/api/leads/I-1", "/api/kpi/drilldown?metric=qualified_leads"]
    with ThreadPoolExecutor(max_workers=12) as pool:
        outcomes = list(pool.map(get, endpoints * 25))

    for endpoint, data in outcomes:
        if endpoint == "/api/kpi/week":
            assert data["metrics"]["qualified_leads"]["actual"] == 1
        elif endpoint == "/api/leads":
            assert len(data) == 1
        elif endpoint == "/api/leads/I-1":
            assert data["analysis"]["qualification"]["status"] == "QL"
        else:
            assert len(data["records"]) == 1
    store.close()


def test_new_owner_inbound_is_not_dropped_without_crm():
    from engine import fallback_extract, assess
    event = base_event(
        from_email="buyer@personal.example",
        body=("I own a 40-person customs brokerage in Haifa. "
              "We reconcile supplier invoices manually. "
              "What would document automation cost us, and can we see it working?"),
    )
    extraction = fallback_extract(event, None)
    assert extraction.stated_buyer_role == "Owner (self-reported)"
    result = assess(event, None, extraction, [], event["received_at"])
    assert result.conditions["company_fit"]["met"]
    assert result.conditions["relevant_buyer"]["met"]
    assert result.conditions["company_fit"]["unverified"]
    assert result.status == "QL candidate"
