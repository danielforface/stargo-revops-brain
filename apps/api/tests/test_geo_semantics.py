"""Safe, topic-matched BC/PP citations for generated GEO content."""
from pathlib import Path

import gemini
import pytest


KEY='TEST_KEY_NOT_REAL_0000000000'
MODEL='gemini-2.5-flash'


def make_brief(tmp_path, monkeypatch, sections=None):
    (tmp_path/'brand_context.md').write_text('BC-1 BC-3a PP-1')
    monkeypatch.setattr(gemini,'analyze_answers',lambda *_:{'gaps':[{'prompt_id':'Q1','prompt':'alternatives to Laneframe for freight pricing'}]})
    plan={
        'title':'Freight pricing alternatives for logistics teams',
        'direct_claim_ids':['BC-1','BC-3a','PP-1'],
        'sections':sections or [
          {'heading':'Automating Rate Quotes','claim_ids':['BC-3a','PP-1']},
          {'heading':'Document Extraction','claim_ids':['BC-3b','PP-2']},
          {'heading':'Invoice and Contract Reconciliation','claim_ids':['BC-3c','PP-3']},
        ],
        'faq':[
          {'question':'How are freight quotes prepared?','claim_ids':['BC-3a']},
          {'question':'Which logistics teams can use it?','claim_ids':['BC-2']},
          {'question':'What is the review process?','claim_ids':['BC-1']},
        ],
        'schema_org':'FAQPage',
    }
    monkeypatch.setattr(gemini,'_generate',lambda *args,**kwargs: plan)
    return gemini.brief(KEY,MODEL,str(tmp_path))


def test_irrelevant_airwaybill_pilot_removed_from_invoice_section(tmp_path,monkeypatch):
    result=make_brief(tmp_path,monkeypatch)
    invoice=next(s for s in result['sections'] if 'Invoice' in s['heading'])
    assert invoice['citations']==['BC-3c']
    assert 'PP-3' not in invoice['body']
    assert any('PP-3' in note for note in result['quality_notes'])
    assert len(result['sections'])==3


def test_reject_generated_unsupported_numbers_in_heading(tmp_path,monkeypatch):
    sections=[{'heading':'Guarantee 99% cost savings','claim_ids':['BC-1']},
              {'heading':'Relevant freight rates','claim_ids':['BC-3a']},
              {'heading':'Approved document workflows','claim_ids':['BC-3b']}]
    with pytest.raises(gemini.GeminiError,match='unsupported numerical'):
        make_brief(tmp_path,monkeypatch,sections)


def test_reject_when_section_cites_only_unrelated_claims(tmp_path,monkeypatch):
    sections=[{'heading':'Carrier invoice reconciliation','claim_ids':['PP-3']},
              {'heading':'Relevant freight rates','claim_ids':['BC-3a']},
              {'heading':'Approved document workflows','claim_ids':['BC-3b']}]
    with pytest.raises(gemini.GeminiError,match='only claims unrelated'):
        make_brief(tmp_path,monkeypatch,sections)


def test_faq_only_unrelated_claims_are_rejected(tmp_path, monkeypatch):
    """Question-answer citations must support that question's subject too."""
    (tmp_path / 'brand_context.md').write_text('BC-1 BC-3a PP-1')
    monkeypatch.setattr(gemini,'analyze_answers',lambda *_:{'gaps':[{'prompt_id':'Q1','prompt':'best freight pricing software'}]})
    monkeypatch.setattr(gemini,'_generate',lambda *_args,**_kwargs:{
        'title':'Freight pricing software assessment',
        'direct_claim_ids':['BC-1','BC-3a','PP-1'],
        'sections':[{'heading':'Rate quoting','claim_ids':['BC-3a']}]*3,
        'faq':[{'question':'How are carrier invoices reconciled?','claim_ids':['PP-3']},
               {'question':'Which teams are supported?','claim_ids':['BC-2']},
               {'question':'How are quotes prepared?','claim_ids':['BC-3a']}],
        'schema_org':'FAQPage',
    })
    with pytest.raises(gemini.GeminiError,match='only claims unrelated'):
        gemini.brief(KEY,MODEL,str(tmp_path))


def test_direct_answer_must_use_topic_appropriate_source_ids(tmp_path,monkeypatch):
    (tmp_path / 'brand_context.md').write_text('BC-1 BC-3a PP-1')
    monkeypatch.setattr(gemini,'analyze_answers',lambda *_:{'gaps':[{'prompt_id':'Q1','prompt':'freight rate quoting alternatives'}]})
    monkeypatch.setattr(gemini,'_generate',lambda *_args,**_kwargs:{
        'title':'Freight quoting alternatives for operators',
        'direct_claim_ids':['PP-3','BC-3b'],
        'sections':[{'heading':'Rate quoting','claim_ids':['BC-3a']}]*3,
        'faq':[{'question':'How are quotes prepared?','claim_ids':['BC-3a']}]*3,
        'schema_org':'FAQPage',
    })
    with pytest.raises(gemini.GeminiError,match='only claims unrelated'):
        gemini.brief(KEY,MODEL,str(tmp_path))


def test_mixed_invoice_and_unverified_trade_compliance_heading_is_rewritten(tmp_path, monkeypatch):
    result = make_brief(tmp_path, monkeypatch, sections=[
        {'heading':'Invoice Reconciliation and Trade Compliance', 'claim_ids':['BC-3c']},
        {'heading':'Document Extraction', 'claim_ids':['BC-3b']},
        {'heading':'Rate Quoting Workflow', 'claim_ids':['BC-3a']},
    ])
    assert result['sections'][0]['heading'] == 'Invoice and Contract Reconciliation'
    assert result['sections'][0]['citations'] == ['BC-3c']
    assert not any('compliance' in s['heading'].lower() for s in result['sections'])
    assert any('unsupported section-heading' in n for n in result['quality_notes'])


def test_general_logistics_scope_does_not_attach_unrelated_airwaybill_pilot(tmp_path, monkeypatch):
    result = make_brief(tmp_path, monkeypatch, sections=[
        {'heading':'Operational Scope Across Logistics Segments', 'claim_ids':['BC-1','BC-2','PP-3']},
        {'heading':'Document Extraction', 'claim_ids':['BC-3b']},
        {'heading':'Rate Quoting Workflow', 'claim_ids':['BC-3a']},
    ])
    assert result['sections'][0]['citations'] == ['BC-1','BC-2']
    assert 'PP-3' not in result['sections'][0]['body']
    assert any('PP-3' in n for n in result['quality_notes'])


def test_multi_topic_heading_cannot_imply_both_invoice_and_airwaybill_if_only_invoice_evidence(tmp_path, monkeypatch):
    result = make_brief(tmp_path, monkeypatch, sections=[
        {'heading':'Invoice Reconciliation and Air Waybill Digitization', 'claim_ids':['BC-3c']},
        {'heading':'Document Extraction', 'claim_ids':['BC-3b']},
        {'heading':'Rate Quoting Workflow', 'claim_ids':['BC-3a']},
    ])
    assert result['sections'][0]['heading'] == 'Invoice and Contract Reconciliation'
    assert result['sections'][0]['citations'] == ['BC-3c']


def test_trade_compliance_not_claimed_from_trade_document_checking_alone():
    # The approved claim is about checking trade documents for finance teams.
    # It does not say the service guarantees trade/regulatory compliance.
    notes = []
    title = gemini.grounded_heading("Trade Compliance", ["BC-3d"], notes)
    assert title == "Trade Document Checking"
    assert len(notes) == 1


def test_enterprise_integration_not_claimed_from_audience_listing():
    notes = []
    title = gemini.grounded_heading("Enterprise Integration", ["BC-2"], notes)
    assert title == "Supported Logistics Teams"
    assert len(notes) == 1
