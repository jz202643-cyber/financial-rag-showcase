import json

from ..query_understanding.financial_metric_registry import (
    canonicalize_metric,
)


# ============================================================
# LOAD STRUCTURED FACTS
# ============================================================

def load_financial_facts(
    json_path
):
    """
    Load structured financial facts from JSON.
    """

    with open(
        json_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):

    if text is None:

        return ""


    return (
        str(text)
        .strip()
        .lower()
    )


# ============================================================
# METRIC NORMALIZATION
# ============================================================

def normalize_metric(metric):
    """
    Normalize metrics through the shared
    Financial Metric Registry.

    Example:

        operating income
                ↓
        operating_income

        income from operations
                ↓
        operating_income

    If a metric is not yet registered,
    deterministic raw-text normalization
    is used as a fallback.
    """

    if metric is None:

        return ""


    concept_id = canonicalize_metric(
        metric
    )


    if concept_id:

        return concept_id


    return normalize_text(
        metric
    )


# ============================================================
# PERIOD NORMALIZATION
# ============================================================

def normalize_period(period):
    """
    Normalize current quarterly period expressions.

    V0 assumes calendar-year reporting.

    This will later become fiscal-calendar-aware.
    """

    text = normalize_text(
        period
    )


    period_aliases = {

        "q1 2026": (
            "three months ended march 31, 2026"
        ),

        "q2 2026": (
            "three months ended june 30, 2026"
        ),

        "q3 2026": (
            "three months ended september 30, 2026"
        ),

        "q4 2026": (
            "three months ended december 31, 2026"
        ),
    }


    return period_aliases.get(
        text,
        text
    )


# ============================================================
# STRUCTURED FACT RETRIEVAL
# ============================================================

def retrieve_financial_facts(
    facts,
    entity=None,
    metric=None,
    period=None
):
    """
    Retrieve structured financial facts using
    deterministic metadata matching.

    Current constraints:

        entity
        metric concept
        period

    Segment-aware retrieval will be added later.
    """

    results = []


    # ========================================================
    # NORMALIZE QUERY
    # ========================================================

    entity_query = normalize_text(
        entity
    )

    metric_query = normalize_metric(
        metric
    )

    period_query = normalize_period(
        period
    )


    # ========================================================
    # SEARCH FACT STORE
    # ========================================================

    for fact in facts:


        fact_company = normalize_text(
            fact.get(
                "company"
            )
        )


        fact_metric = normalize_metric(
            fact.get(
                "metric"
            )
        )


        fact_period = normalize_text(
            fact.get(
                "period"
            )
        )


        # ----------------------------------------------------
        # ENTITY CONSTRAINT
        # ----------------------------------------------------

        if entity_query:

            if (
                entity_query
                not in fact_company
            ):

                continue


        # ----------------------------------------------------
        # METRIC CONSTRAINT
        # ----------------------------------------------------

        if metric_query:

            if (
                metric_query
                != fact_metric
            ):

                continue


        # ----------------------------------------------------
        # PERIOD CONSTRAINT
        # ----------------------------------------------------

        if period_query:

            if (
                period_query
                != fact_period
            ):

                continue


        # ----------------------------------------------------
        # MATCH
        # ----------------------------------------------------

        results.append(
            fact
        )


    return results


# ============================================================
# DEVELOPMENT TEST
# ============================================================

if __name__ == "__main__":

    facts = load_financial_facts(
        "data/meta_q2_2026_financial_facts.json"
    )


    print(
        "FACTS LOADED:",
        len(
            facts
        )
    )


    test_metrics = [
        "Revenue",
        "Operating income",
        "Income from operations",
        "Total costs and expenses",
        "Operating margin",
        "Capital expenditures",
    ]


    for metric in test_metrics:

        results = retrieve_financial_facts(
            facts=facts,
            entity="Meta Platforms",
            metric=metric,
            period="Q2 2026"
        )


        print(
            "\n======================================"
        )

        print(
            "METRIC:",
            metric
        )

        print(
            "NORMALIZED:",
            normalize_metric(
                metric
            )
        )

        print(
            "MATCHES:",
            len(
                results
            )
        )


        for result in results[:3]:

            print(
                result
            )