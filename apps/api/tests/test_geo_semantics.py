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
