"""Decision-time business evidence must survive a later LLM failure or reinterpretation.

Only synthetic test values are committed; employer-provided pack is private.
"""
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import api
from fastapi.testclient import TestClient
from engine import Store, fallback_extract
from test_engine import base_contact, base_event, synthetic_store
from export_kpi import render


def accept(store, inbound_id='I-1', when='2026-10-06T11:00:00+03:00'):
    return store.decide(inbound_id, 'accepted', when, 'Synthetic Reviewer')


def test_acceptance_freezes_evidence_when_model_later_fails(tmp_path):
    store=synthetic_store(tmp_path)
    store.analyze('I-1')
    assert accept(store)['analysis']['qualification']['status']=='QL'
    report=store.kpi()
    assert report['metrics']['qualified_leads']['actual']==1
    frozen=report['metrics']['qualified_leads']['records'][0]['snapshot']
    assert all(v['met'] for v in frozen.values())
    failure=store.analyze('I-1', lambda *_: {'intent':'fabricated', 'language':'en'})
    assert failure['mode']=='failed'
    assert store.lead('I-1')['analysis']['qualification']['status']=='needs review'
    assert store.kpi()['metrics']['qualified_leads']['actual']==1
    assert store.db.execute('SELECT count(*) FROM analysis_history').fetchone()[0]==2
    assert store.db.execute('SELECT count(*) FROM decision_evidence').fetchone()[0]==1
    store.close()
    reopened=Store(str(tmp_path/'data.sqlite3'))
    assert reopened.kpi()['metrics']['qualified_leads']['actual']==1
    reopened.close()


def test_rejection_supersedes_earlier_acceptance_not_frozen_evidence(tmp_path):
    store=synthetic_store(tmp_path)
    store.analyze('I-1')
    accept(store)
    store.decide('I-1','rejected','2026-10-08T13:00:00+03:00','Synthetic Reviewer')
    assert store.kpi()['metrics']['qualified_leads']['actual']==0
    assert store.db.execute('SELECT count(*) FROM decision_evidence').fetchone()[0]==1
    store.close()


def test_history_snapshot_blocks_future_inbound_from_qualifying_past_acceptance(tmp_path):
    store=synthetic_store(tmp_path)
    first=base_event(body='Hello, this is a friendly introduction.')
    store.db.execute('UPDATE inbound SET payload=? WHERE id=?',(json.dumps(first),'I-1'))
    store.analyze('I-1')
    accept(store)
    second=base_event(id='I-2',received_at='2026-10-07T15:00:00+03:00')
    store.put('inbound','I-2',second,'C-1')
    store.analyze('I-2')
    assert store.kpi()['metrics']['qualified_leads']['actual']==0
    store.close()


def test_inbound_after_old_decision_is_rejected_with_clear_reason(tmp_path,monkeypatch):
    store=synthetic_store(tmp_path)
    monkeypatch.setattr(api,'store',store)
    monkeypatch.setattr(api,'seed_health',{'ready':True})
    res=TestClient(api.app).post('/api/leads/I-1/decisions',json={
        'decision':'accepted','actor':'Example Reviewer','decided_at':'2026-10-01T09:00:00+03:00'})
    assert res.status_code==422
    assert 'predates the first inbound' in res.json()['detail']
    assert len(store.items('decisions'))==0
    store.close()


def test_authoritative_kpi_pack_is_persisted_and_updated_on_decision(tmp_path):
    store=synthetic_store(tmp_path)
    store.analyze('I-1')
    before=json.loads(store.db.execute("SELECT payload FROM meta WHERE name='latest_kpi_pack'").fetchone()[0]) if store.db.execute("SELECT 1 FROM meta WHERE name='latest_kpi_pack'").fetchone() else None
    assert before is None
    accept(store)
    persisted=json.loads(store.db.execute("SELECT payload FROM meta WHERE name='latest_kpi_pack'").fetchone()[0])
    assert persisted['metrics']['qualified_leads']['actual']==1
    store.decide('I-1','rejected','2026-10-07T11:00:00+03:00','Synthetic Reviewer')
    updated=json.loads(store.db.execute("SELECT payload FROM meta WHERE name='latest_kpi_pack'").fetchone()[0])
    assert updated['metrics']['qualified_leads']['actual']==0
    store.close()


def test_dynamic_cro_note_never_claims_six_when_report_is_one(tmp_path):
    store=synthetic_store(tmp_path)
    store.analyze('I-1')
    accept(store)
    report=store.kpi()
    visibility={'gaps':[{'prompt':'how to reconcile invoices','score':280}]}
    text=render(report,visibility)
    note=text.split('## Note to CRO\n\n')[1].strip()
    assert '1 against 25' in note
    assert '6 acquisition QLs' not in note
    assert 'how to reconcile invoices' in note
    assert len(note.split())<=150
    store.close()


def test_kpi_export_endpoint_uses_same_live_pack_as_api(tmp_path,monkeypatch):
    store=synthetic_store(tmp_path)
    store.analyze('I-1')
    accept(store)
    monkeypatch.setattr(api,'store',store)
    monkeypatch.setattr(api,'seed_health',{'ready':True})
    monkeypatch.setattr(api,'analyze_answers', lambda *_: {'gaps':[{'prompt':'quoting software','score':200}]})
    client=TestClient(api.app)
    data=client.get('/api/kpi/week').json()
    markdown=client.get('/api/kpi/pack').json()['markdown']
    assert data['metrics']['qualified_leads']['actual']==1
    assert '| Qualified Leads | 1 | 25 | -24 |' in markdown
    assert '1 against 25' in markdown
    store.close()


def test_parallel_kpi_query_does_not_wait_for_remote_llm(tmp_path):
    store=synthetic_store(tmp_path)
    started=threading.Event()
    finish=threading.Event()
    def blocked_model(inbound,crm):
        started.set()
        if not finish.wait(2):
            raise RuntimeError('simulated model stalled')
        return fallback_extract(inbound,crm)
    with ThreadPoolExecutor(max_workers=2) as pool:
        worker=pool.submit(store.analyze,'I-1',blocked_model)
        assert started.wait(1)
        api=pool.submit(store.kpi)
        try:
            result=api.result(timeout=0.8)
            assert result['metrics']['qualified_leads']['actual']==0
        finally:
            finish.set()
        assert worker.result(timeout=2)['mode']=='rules-only'
    store.close()


def test_current_ql_does_not_imply_prior_reporting_week(tmp_path):
    store=synthetic_store(tmp_path)
    store.analyze('I-1')
    lead=accept(store,when='2026-10-11T12:00:00+03:00')
    assert lead['analysis']['qualification']['status']=='QL'
    assert store.kpi()['metrics']['qualified_leads']['actual']==0
    store.close()
