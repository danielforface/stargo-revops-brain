import json
from fastapi.testclient import TestClient
import api
from engine import Store


def fake_seed(store):
    store.put("contacts", "C-1", {"record_id":"C-1", "first_name":"A", "last_name":"B", "email":"a@forwarder.example", "linkedin_url":"", "company_name":"Forwarder", "vertical":"freight-forwarder", "country":"UK", "employees":"55", "job_title":"Operations Director", "is_customer":"false", "owner":"Leo"})
    store.db.commit()


def test_api_inbound_decision_kpi_replay_and_restart(tmp_path, monkeypatch):
    store=Store(str(tmp_path/"db.sqlite3"))
    fake_seed(store)
    monkeypatch.setattr(api, "store", store)
    monkeypatch.setattr(api, "seed_health", {"ready":True})
    monkeypatch.setattr(api, "PROVIDER", "rules-only")
    client=TestClient(api.app)
    inbound={"from_name":"A B","from_email":"a@forwarder.example","channel":"email_reply","source":"warm-network","received_at":"2026-10-03T10:00:00+03:00","body":"We manually reconcile freight invoices and rate contracts. Could we see a demo next week?"}
    response=client.post('/api/inbound',json=inbound)
    assert response.status_code==201, response.text
    lead=response.json()
    assert lead['analysis']['qualification']['status']=='QL candidate'
    lid=lead['inbound']['id']
    accepted=client.post(f'/api/leads/{lid}/decisions',json={'decision':'accepted','decided_at':'2026-10-06T10:00:00+03:00','actor':'Reviewer'})
    assert accepted.status_code==200
    assert accepted.json()['analysis']['qualification']['status']=='QL'
    assert client.get('/api/kpi/week').json()['metrics']['qualified_leads']['actual']==1
    assert client.get('/api/kpi/drilldown?metric=qualified_leads').json()['records'][0]['inbound_id']==lid
    assert client.get('/api/kpi/drilldown?metric=wrong').status_code==404
    store.close()
    reopened=Store(str(tmp_path/"db.sqlite3"))
    monkeypatch.setattr(api,'store',reopened)
    assert client.get('/api/kpi/week').json()['metrics']['qualified_leads']['actual']==1
    reopened.close()


def test_inbound_bad_identity_rejected(tmp_path,monkeypatch):
    store=Store(str(tmp_path/"db.sqlite3"))
    monkeypatch.setattr(api, "store", store)
    monkeypatch.setattr(api, "seed_health", {"ready":True})
    client=TestClient(api.app)
    response=client.post('/api/inbound',json={'from_name':'Buyer','channel':'email_reply','body':'Hi, can we talk?'})
    assert response.status_code==422
    assert not store.items('inbound')
    store.close()
