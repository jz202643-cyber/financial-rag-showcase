"""End-to-end structured-path checks, excluding heavy narrative model loading.

Import stubs prevent model downloads/LLM requests; all real structured
routing, domain rules, exact/fallback lookup and fact JSON are exercised.
These are not full narrative-retrieval integration tests.
"""
import sys
import types
import pytest


@pytest.fixture(scope="module")
def answer_question():
    # Heavy model loading lives in the imported retrieval module.
    # Structured path never calls it; stub its import for offline CI.
    retriever = types.ModuleType("financial_rag.retrieval.retriever")
    retriever.retrieve_evidence = lambda *_: {"candidates": []}
    generator = types.ModuleType("financial_rag.generation.generator")
    generator.generate_narrative_answer = lambda **_: {"status": "NOT_TESTED"}
    from unittest.mock import patch
    with patch.dict(sys.modules, {
        "financial_rag.retrieval.retriever": retriever,
        "financial_rag.generation.generator": generator,
    }):
        from financial_rag.main import answer_question as function
    return function


@pytest.mark.parametrize("question,value,unit", [
    ("What was Meta's revenue in Q2 2026?", 60801, "USD millions"),
    ("What was Meta's operating margin in Q2 2026?", 31, "percent"),
    ("What was Meta's operating profit in Q2 2026?", 18775, "USD millions"),
])
def test_supported_company_facts(answer_question, question, value, unit):
    result = answer_question(question)
    assert result["route"] == "structured"
    assert result["status"] == "SUPPORTED"
    assert result["evidence"]["value"] == value
    assert result["evidence"]["unit"] == unit


@pytest.mark.parametrize("question", [
    "What was Meta's cloud revenue in Q2 2026?",
    "What was Meta's cloud operating margin in Q2 2026?",
    "What was Meta's operating margin for cloud in Q2 2026?",
    "What was the operating margin for Meta's cloud business in Q2 2026?",
    "What was Meta's cloud operating profit in Q2 2026?",
    "What was Meta's banking revenue in Q2 2026?",
    "What was Meta's retail revenue in Q2 2026?",
])
def test_unknown_qualifier_is_safe(answer_question, question):
    result = answer_question(question)
    assert result["route"] == "structured"
    assert result["status"] == "INSUFFICIENT"
    assert result["reason"] == "Unresolved metric qualifier."


def test_comparison_is_not_answered_by_single_fact(answer_question):
    question = "What was Meta's revenue in Q2 2026 compared with Q2 2025?"
    result = answer_question(question)
    assert result["route"] == "structured"
    assert result["status"] == "INSUFFICIENT"
    assert "comparison" in result["reason"].lower()


@pytest.mark.parametrize("question,value", [
    ("How large were Meta's total costs and expenses in Q2 2026?", 42026),
    ("What was the combined balance of Meta's cash and marketable securities at June 30, 2026?", 90260),
    ("State Meta's long-term debt balance at the end of June 2026.", 83664),
    ("How much liquidity did Meta hold in cash and marketable securities at quarter end?", 90260),
])
def test_benign_finance_wording_not_rejected(answer_question, question, value):
    result = answer_question(question)
    assert result["route"] == "structured"
    assert result["status"] == "SUPPORTED"
    assert result["evidence"]["value"] == value
