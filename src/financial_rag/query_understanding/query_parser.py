import re

from .financial_metric_registry import (
    FINANCIAL_METRICS,
    extract_metric_concept,
)


# ============================================================
# ENTITY EXTRACTION
# ============================================================

def extract_entity(question):

    q = question.lower()

    if "meta" in q:
        return "Meta Platforms"

    return None


# ============================================================
# SEGMENT EXTRACTION
# ============================================================

def extract_segment(question):
    """
    Extract recognized business segments.

    V0.2 currently supports:

        Family of Apps
        Reality Labs
    """

    q = question.lower()


    if (
        "family of apps" in q
        or re.search(
            r"\bfoa\b",
            q
        )
    ):

        return "Family of Apps"


    if "reality labs" in q:

        return "Reality Labs"


    return None


# ============================================================
# METRIC EXTRACTION
# ============================================================

def extract_metric(question):
    """
    Extract a financial metric using the shared
    Financial Metric Registry.

    Returns a human-readable canonical metric label.

    Example:

        "income from operations"
                ↓
        concept = operating_income
                ↓
        metric = "operating income"
    """

    concept_id = extract_metric_concept(
        question
    )


    if concept_id is None:

        return None


    definition = FINANCIAL_METRICS.get(
        concept_id
    )


    if not definition:

        return None


    aliases = definition.get(
        "aliases",
        []
    )


    if not aliases:

        return None


    # First alias is used as the human-readable
    # canonical metric label.
    return aliases[0]


# ============================================================
# METRIC CONCEPT EXTRACTION
# ============================================================

def extract_metric_id(question):
    """
    Return the internal canonical financial concept ID.

    Example:

        operating income
                ↓
        operating_income
    """

    return extract_metric_concept(
        question
    )


# ============================================================
# PERIOD EXTRACTION
# ============================================================

def extract_period(question):

    q = question.lower()


    # --------------------------------------------------------
    # Quarter
    #
    # Example:
    # Q2 2026
    # --------------------------------------------------------

    quarter_match = re.search(
        r"\bq([1-4])\s*(20\d{2})\b",
        q
    )


    if quarter_match:

        quarter = quarter_match.group(1)
        year = quarter_match.group(2)

        return (
            f"Q{quarter} {year}"
        )


    # --------------------------------------------------------
    # Fiscal year
    #
    # FY2026
    # FY 2026
    # --------------------------------------------------------

    fy_match = re.search(
        r"\bfy\s*(20\d{2})\b",
        q
    )


    if fy_match:

        year = fy_match.group(1)

        return (
            f"FY{year}"
        )


    # --------------------------------------------------------
    # Bare year
    # --------------------------------------------------------

    year_match = re.search(
        r"\b(20\d{2})\b",
        q
    )


    if year_match:

        return year_match.group(1)


    return None


# ============================================================
# FACT TYPE EXTRACTION
# ============================================================

def extract_fact_type(question):

    q = question.lower()


    guidance_words = [
        "guidance",
        "outlook",
        "forecast",
        "expect",
        "expected",
        "anticipate",
        "anticipated",
        "estimate",
        "estimated",
    ]


    for word in guidance_words:

        if word in q:

            return "guidance"


    return "actual"


# ============================================================
# QUESTION TYPE EXTRACTION
# ============================================================

def extract_question_type(question):

    q = question.lower().strip()


    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    if q.startswith("why"):

        return "explanation"


    if q.startswith("how did"):

        return "explanation"


    # --------------------------------------------------------
    # Exact fact
    # --------------------------------------------------------

    if (
        q.startswith("what")
        or q.startswith("how much")
        or q.startswith("how many")
    ):

        return "exact_fact"


    return "general"


# ============================================================
# QUALIFIER EXTRACTION
# ============================================================

def extract_metric_qualifier(
    question,
    metric,
    segment
):
    """
    Detect unresolved qualifiers attached to revenue.

    Examples:

        Meta revenue
            -> qualifier = None

        Meta total revenue
            -> qualifier = None

        Family of Apps revenue
            -> segment = Family of Apps
            -> qualifier = None

        cloud revenue
            -> qualifier = cloud
    """

    if metric != "revenue":

        return None


    q = question.lower()


    if "revenue" not in q:

        return None


    # Everything before "revenue"
    prefix = q.split(
        "revenue",
        1
    )[0]


    # --------------------------------------------------------
    # Remove recognized segments
    # --------------------------------------------------------

    if segment == "Family of Apps":

        prefix = prefix.replace(
            "family of apps",
            " "
        )

        prefix = re.sub(
            r"\bfoa\b",
            " ",
            prefix
        )


    if segment == "Reality Labs":

        prefix = prefix.replace(
            "reality labs",
            " "
        )


    # --------------------------------------------------------
    # Remove company references
    # --------------------------------------------------------

    prefix = re.sub(
        r"\bmeta platforms(?:'s)?\b",
        " ",
        prefix
    )

    prefix = re.sub(
        r"\bmeta(?:'s)?\b",
        " ",
        prefix
    )


    # --------------------------------------------------------
    # Remove period expressions
    # --------------------------------------------------------

    prefix = re.sub(
        r"\bq[1-4]\b",
        " ",
        prefix
    )

    prefix = re.sub(
        r"\b20\d{2}\b",
        " ",
        prefix
    )


    # --------------------------------------------------------
    # Remove punctuation
    # --------------------------------------------------------

    prefix = re.sub(
        r"[^a-z0-9\s]",
        " ",
        prefix
    )


    tokens = prefix.split()


    ignored_words = {
        "what",
        "was",
        "were",
        "is",
        "are",
        "did",
        "does",
        "how",
        "much",
        "many",
        "the",
        "a",
        "an",
        "of",
        "for",
        "in",
        "during",

        # Safe company-total qualifiers
        "total",
        "overall",
        "consolidated",
        "company",
    }


    remaining_tokens = [

        token

        for token in tokens

        if token not in ignored_words
    ]


    if not remaining_tokens:

        return None


    return " ".join(
        remaining_tokens
    )


# ============================================================
# QUALIFIER STATUS
# ============================================================

def get_qualifier_status(
    qualifier
):

    if qualifier:

        return "unresolved"


    return "clear"


# ============================================================
# QUERY PARSER
# ============================================================

def parse_query(question):

    entity = extract_entity(
        question
    )

    segment = extract_segment(
        question
    )

    metric = extract_metric(
        question
    )

    metric_concept = extract_metric_id(
        question
    )

    period = extract_period(
        question
    )

    fact_type = extract_fact_type(
        question
    )

    question_type = extract_question_type(
        question
    )


    qualifier = extract_metric_qualifier(
        question=question,
        metric=metric,
        segment=segment
    )


    qualifier_status = (
        get_qualifier_status(
            qualifier
        )
    )


    return {

        "entity": entity,

        "segment": segment,

        "metric": metric,

        "metric_concept": (
            metric_concept
        ),

        "qualifier": qualifier,

        "qualifier_status": (
            qualifier_status
        ),

        "period": period,

        "fact_type": fact_type,

        "question_type": (
            question_type
        ),
    }


# ============================================================
# QUERY ROUTER
# ============================================================

def route_query(parsed_query):
    """
    Current routing logic:

        exact actual
            -> structured

        exact guidance
            -> narrative

        explanation
            -> narrative

        general
            -> narrative

        incomplete exact fact
            -> unsupported
    """

    question_type = parsed_query.get(
        "question_type"
    )

    entity = parsed_query.get(
        "entity"
    )

    metric = parsed_query.get(
        "metric"
    )

    period = parsed_query.get(
        "period"
    )

    fact_type = parsed_query.get(
        "fact_type"
    )


    # ========================================================
    # EXACT FACT
    # ========================================================

    if question_type == "exact_fact":


        if not (
            entity
            and metric
            and period
        ):

            return "unsupported"


        if fact_type == "guidance":

            return "narrative"


        if fact_type == "actual":

            return "structured"


        return "unsupported"


    # ========================================================
    # EXPLANATION
    # ========================================================

    if question_type == "explanation":

        return "narrative"


    # ========================================================
    # GENERAL
    # ========================================================

    if question_type == "general":

        return "narrative"


    return "unsupported"


# ============================================================
# DEVELOPMENT TEST
# ============================================================

if __name__ == "__main__":

    test_questions = [

        "What was Meta's revenue in Q2 2026?",

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

        (
            "What was Meta's cloud revenue "
            "in Q2 2026?"
        ),
    ]


    for question in test_questions:

        parsed = parse_query(
            question
        )

        route = route_query(
            parsed
        )


        print(
            "\n======================================"
        )

        print(
            "QUESTION:"
        )

        print(
            question
        )


        print(
            "\nPARSED:"
        )

        print(
            parsed
        )


        print(
            "\nROUTE:"
        )

        print(
            route
        )