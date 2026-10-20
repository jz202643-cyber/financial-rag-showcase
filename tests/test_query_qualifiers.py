from financial_rag.query_understanding.query_parser import parse_query


def test_unknown_prefix_qualifier_is_unresolved():
    r = parse_query(
        "What was Meta's cloud operating margin in Q2 2026?"
    )

    assert r["metric_concept"] == "operating_margin"
    assert r["qualifier"] == "cloud"
    assert r["qualifier_status"] == "unresolved"


def test_unknown_suffix_qualifier_is_unresolved():
    r = parse_query(
        "What was Meta's operating margin for cloud in Q2 2026?"
    )

    assert r["metric_concept"] == "operating_margin"
    assert r["qualifier"] == "cloud"
    assert r["qualifier_status"] == "unresolved"


def test_normal_company_metric_remains_clear():
    r = parse_query(
        "What was Meta's operating margin in Q2 2026?"
    )

    assert r["qualifier"] is None
    assert r["qualifier_status"] == "clear"


def test_recognized_segment_is_not_unresolved_qualifier():
    r = parse_query(
        "What was Reality Labs revenue in Q2 2026?"
    )

    assert r["segment"] == "Reality Labs"
    assert r["qualifier"] is None
    assert r["qualifier_status"] == "clear"


import pytest


@pytest.mark.parametrize("question, expected", [
    ("What was Meta's cloud net income in Q2 2026?", "cloud"),
    ("What was Meta's cloud operating profit in Q2 2026?", "cloud"),
    ("What was Meta's cloud free cash flow in Q2 2026?", "cloud"),
    ("What was Meta's cloud capital expenditure in Q2 2026?", "cloud"),
    ("What were Meta's cloud total assets in 2026?", "cloud"),
    ("What was Meta's cloud tax rate in Q2 2026?", "cloud"),
    ("What was the operating margin for Meta's cloud business in Q2 2026?", "cloud business"),
    ("What was Meta's revenue from ads in Q2 2026?", "ads"),
    ("What was Meta's bank division revenue in Q2 2026?", "bank division"),
])
def test_unresolved_qualifiers_generalize(question, expected):
    result = parse_query(question)
    assert result["qualifier"] == expected
    assert result["qualifier_status"] == "unresolved"


@pytest.mark.parametrize("question, segment", [
    ("What was revenue for Reality Labs in Q2 2026?", "Reality Labs"),
    ("What was revenue for Family of Apps in Q2 2026?", "Family of Apps"),
    ("What was Reality Labs revenue in Q2 2026?", "Reality Labs"),
    ("What was Family of Apps revenue in Q2 2026?", "Family of Apps"),
])
def test_recognized_segment_both_positions(question, segment):
    result = parse_query(question)
    assert result["segment"] == segment
    assert result["qualifier"] is None
    assert result["qualifier_status"] == "clear"


@pytest.mark.parametrize("question", [
    "What was Meta's revenue in Q2 2026 compared to Q2 2025?",
    "What was Meta's operating margin in Q2 2026 compared with Q2 2025?",
    "What was Meta's revenue for the second quarter of 2026 compared with 2025?",
    "What was Meta's total revenue in Q2 2026?",
    "What was Meta's effective tax rate in Q2 2026?",
])
def test_comparison_and_reporting_clauses_not_qualifiers(question):
    result = parse_query(question)
    assert result["qualifier"] is None
    assert result["qualifier_status"] == "clear"
