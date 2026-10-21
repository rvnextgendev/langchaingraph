from unittest.mock import Mock, patch

import pytest

from order_assistant.rag_workflow import NO_EVIDENCE, build_rag_workflow
from order_assistant.retrieval import retrieve_policy
from order_assistant.service import answer_request


def test_returns_retrieval_finds_relevant_passage():
    passages = retrieve_policy("Can I return unused items?")
    assert passages
    assert "30 days" in passages[0].text
    assert "returns.md" in passages[0].source


def test_unknown_question_skips_model():
    factory = Mock()
    result = build_rag_workflow(factory).invoke({"question": "quantum astrophysics"})
    assert result["reply"] == NO_EVIDENCE
    factory.assert_not_called()


def test_cited_answer_includes_actual_sources_and_evidence():
    model = Mock()
    model.invoke.return_value.text = "Returns may be requested within 30 days of delivery. [1]"
    result = build_rag_workflow(lambda: model).invoke({"question": "return unused items"})
    assert "[1]" in result["reply"]
    assert "returns.md" in result["reply"]
    assert "30 days" in model.invoke.call_args.args[0][1][1]


@pytest.mark.parametrize("text", ["", "Unsupported answer", "Wrong citation [99]"])
def test_invalid_citations_replace_answer_with_evidence(text):
    model = Mock()
    model.invoke.return_value.text = text
    reply = build_rag_workflow(lambda: model).invoke({"question": "return unused items"})["reply"]
    assert reply.startswith("A cited answer could not be generated")
    assert "returns.md" in reply


def test_provider_failure_propagates():
    model = Mock()
    model.invoke.side_effect = TimeoutError()
    with pytest.raises(TimeoutError):
        build_rag_workflow(lambda: model).invoke({"question": "return unused items"})


def test_modified_document_updates_cached_chunks(tmp_path):
    document = tmp_path / "policy.md"
    document.write_text("Returns allowed for 10 days.", encoding="utf-8")
    assert "10 days" in retrieve_policy("returns", tmp_path)[0].text
    document.write_text("Returns allowed for 20 days.", encoding="utf-8")
    assert "20 days" in retrieve_policy("returns", tmp_path)[0].text


def test_empty_corpus_returns_no_matches(tmp_path):
    assert retrieve_policy("returns", tmp_path) == ()


def test_service_rag_and_blank_validation():
    assert answer_request("rag", "quantum astrophysics") == NO_EVIDENCE
    with pytest.raises(ValueError):
        answer_request("rag", " ")
    with patch("order_assistant.llm.build_model") as model:
        model.return_value.invoke.return_value.text = "Allow 3 to 5 business days. [1]"
        with patch("order_assistant.llm.Settings.from_env"):
            assert "shipping.md" in answer_request("rag", "standard shipping")
