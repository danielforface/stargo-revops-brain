from pathlib import Path
import json
from geo import analyze_answers, build_brief


def test_visibility_brand_confusion_and_owned_citations(tmp_path):
    sample={"meta":{"own_domains":["stargo.co"],"known_competitors":["Laneframe","QuoteHarbor"]},"answers":[{"answer_id":"P1-C","prompt_id":"P1","prompt":"freight quote software","cluster":"rate-quoting","priority":3,"engine":"ChatGPT","answer_text":"StarGo is a holiday booking app; Laneframe handles quotes.","citations":["https://laneframe.example"]},{"answer_id":"P1-P","prompt_id":"P1","prompt":"freight quote software","cluster":"rate-quoting","priority":3,"engine":"Perplexity","answer_text":"Stargo works with freight documents.","citations":["https://docs.stargo.co/overview"]}]}
    (tmp_path/"ai_answers.json").write_text(json.dumps(sample))
    result=analyze_answers(str(tmp_path))
    assert result["answers"][0]["brand_confusion"] is True
    assert result["answers"][0]["mentioned"] is False
    # An explicitly owned base domain covers its subdomains.
    assert result["answers"][1]["owned_citation"] is True
    brief=build_brief(str(tmp_path))
    assert 40 <= len(brief["direct_answer"].split()) <= 60
    assert len(brief["sections"]) in range(3,6)
    assert len(brief["faq"]) in range(3,6)
    assert all(s["citations"] for s in brief["sections"])
