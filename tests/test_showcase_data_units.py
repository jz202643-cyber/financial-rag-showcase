"""Validate corrected units in the frozen showcase JSON fact store."""
import json
from pathlib import Path


def test_prebuilt_fact_store_units():
    facts_path = Path(__file__).resolve().parents[1] / "data" / "meta_q2_2026_financial_facts.json"
    facts = json.loads(facts_path.read_text())
    by_id = {fact.get("fact_id"): fact for fact in facts}
    assert len(facts) == 168
    expected = {
        "meta_q2_2026_fact_0009": "USD millions",
        "meta_q2_2026_fact_0010": "USD millions",
        "meta_q2_2026_fact_0015": "USD per share",
        "meta_q2_2026_fact_0016": "USD per share",
    }
    for fact_id, unit in expected.items():
        assert by_id[fact_id]["unit"] == unit
    # No raw monetary or EPS figure in this dataset should be
    # classified as a percentage solely due to an adjacent cell.
    for fact in facts:
        if fact.get("unit") == "percent":
            assert "%" in str(fact.get("raw_value")), fact.get("fact_id")
