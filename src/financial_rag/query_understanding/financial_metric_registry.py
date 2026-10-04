# ============================================================
# FINANCIAL METRIC REGISTRY V0.1
# ============================================================

FINANCIAL_METRICS = {

    # ========================================================
    # REVENUE
    # ========================================================

    "revenue": {
        "aliases": [
            "revenue",
            "revenues",
            "total revenue",
            "total revenues",
        ],

        "value_type": "currency",

        "typical_statement": (
            "income_statement"
        ),
    },


    # ========================================================
    # NET INCOME
    # ========================================================

    "net_income": {
        "aliases": [
            "net income",
            "net earnings",
        ],

        "value_type": "currency",

        "typical_statement": (
            "income_statement"
        ),
    },


    # ========================================================
    # OPERATING INCOME
    # ========================================================

    "operating_income": {
        "aliases": [
            "operating income",
            "income from operations",
            "operating profit",
        ],

        "value_type": "currency",

        "typical_statement": (
            "income_statement"
        ),
    },


    # ========================================================
    # TOTAL COSTS AND EXPENSES
    # ========================================================

    "total_costs_and_expenses": {
        "aliases": [
            "total costs and expenses",
            "costs and expenses",
            "total expenses",
        ],

        "value_type": "currency",

        "typical_statement": (
            "income_statement"
        ),
    },


    # ========================================================
    # OPERATING MARGIN
    # ========================================================

    "operating_margin": {
        "aliases": [
            "operating margin",
        ],

        "value_type": "percentage",

        "typical_statement": (
            "income_statement"
        ),
    },


    # ========================================================
    # CAPITAL EXPENDITURES
    # ========================================================

    "capital_expenditures": {
        "aliases": [
            "capital expenditures",
            "capital expenditure",
            "capex",
        ],

        "value_type": "currency",

        "typical_statement": (
            "cash_flow_or_disclosure"
        ),
    },


    # ========================================================
    # OPERATING CASH FLOW
    # ========================================================

    "operating_cash_flow": {
        "aliases": [
            "cash flow from operating activities",
            "operating cash flow",
            "cash from operations",
            "cfo",
        ],

        "value_type": "currency",

        "typical_statement": (
            "cash_flow_statement"
        ),
    },


    # ========================================================
    # FREE CASH FLOW
    # ========================================================

    "free_cash_flow": {
        "aliases": [
            "free cash flow",
            "fcf",
        ],

        "value_type": "currency",

        "typical_statement": (
            "cash_flow_or_disclosure"
        ),
    },


    # ========================================================
    # CASH AND MARKETABLE SECURITIES
    # ========================================================

    "cash_and_marketable_securities": {
        "aliases": [
            "cash, cash equivalents, and marketable securities",
            "cash equivalents and marketable securities",
            "cash and marketable securities",
        ],

        "value_type": "currency",

        "typical_statement": (
            "balance_sheet_or_disclosure"
        ),
    },


    # ========================================================
    # LONG-TERM DEBT
    # ========================================================

    "long_term_debt": {
        "aliases": [
            "long-term debt",
            "long term debt",
        ],

        "value_type": "currency",

        "typical_statement": (
            "balance_sheet"
        ),
    },


    # ========================================================
    # TOTAL ASSETS
    # ========================================================

    "total_assets": {
        "aliases": [
            "total assets",
        ],

        "value_type": "currency",

        "typical_statement": (
            "balance_sheet"
        ),
    },


    # ========================================================
    # TAX RATE
    # ========================================================

    "tax_rate": {
        "aliases": [
            "tax rate",
            "effective tax rate",
        ],

        "value_type": "percentage",

        "typical_statement": (
            "income_statement_or_guidance"
        ),
    },
}


# ============================================================
# NORMALIZATION
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
# ALIAS -> CANONICAL CONCEPT
# ============================================================

def canonicalize_metric(metric):
    """
    Convert a financial metric expression into the
    canonical concept used internally by the system.

    Example:

        Income from operations
                ↓
        operating_income
    """

    text = normalize_text(
        metric
    )


    if not text:
        return None


    for concept_id, definition in (
        FINANCIAL_METRICS.items()
    ):

        aliases = definition[
            "aliases"
        ]


        for alias in aliases:

            if text == normalize_text(
                alias
            ):

                return concept_id


    return None


# ============================================================
# FIND METRIC INSIDE A QUESTION
# ============================================================

def extract_metric_concept(question):
    """
    Detect a registered financial metric inside
    a natural-language question.

    Longer aliases are checked first so that:

        "total revenue"

    is preferred over:

        "revenue"
    """

    q = normalize_text(
        question
    )


    candidates = []


    for concept_id, definition in (
        FINANCIAL_METRICS.items()
    ):

        for alias in definition[
            "aliases"
        ]:

            candidates.append(
                (
                    alias,
                    concept_id
                )
            )


    candidates.sort(
        key=lambda item: len(
            item[0]
        ),
        reverse=True
    )


    for alias, concept_id in candidates:

        if normalize_text(
            alias
        ) in q:

            return concept_id


    return None


# ============================================================
# DEVELOPMENT TEST
# ============================================================

if __name__ == "__main__":

    test_metrics = [
        "Income from operations",
        "Operating income",
        "Operating margin",
        "Capital expenditures",
        "Cash flow from operating activities",
        "Free cash flow",
        "Long-term debt",
        "Total assets",
        "Tax rate",
    ]


    print(
        "======================================"
    )

    print(
        "CANONICALIZATION TEST"
    )

    print(
        "======================================"
    )


    for metric in test_metrics:

        print(
            metric,
            "->",
            canonicalize_metric(
                metric
            )
        )


    print(
        "\n======================================"
    )

    print(
        "QUESTION EXTRACTION TEST"
    )

    print(
        "======================================"
    )


    test_questions = [
        (
            "What were Meta's total costs "
            "and expenses in Q2 2026?"
        ),

        (
            "What was Meta's operating "
            "margin in Q2 2026?"
        ),

        (
            "What was Meta's cash flow from "
            "operating activities in Q2 2026?"
        ),

        (
            "What was Meta's long-term debt "
            "as of June 30, 2026?"
        ),

        (
            "What tax rate does Meta expect "
            "for the remaining quarters of 2026?"
        ),
    ]


    for question in test_questions:

        print(
            question
        )

        print(
            "->",
            extract_metric_concept(
                question
            )
        )

        print()