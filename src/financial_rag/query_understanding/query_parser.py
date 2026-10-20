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
    Detect unresolved qualifiers attached to any recognized
    financial metric.

    Supports both:

        cloud operating margin
            -> qualifier = cloud

    and:

        operating margin for cloud
            -> qualifier = cloud

    Recognized company references, periods, and segments are
    removed before deciding whether an unresolved qualifier
    remains.
    """

    if not metric:
        return None


    q = question.lower()


    # --------------------------------------------------------
    # Identify the metric concept and its registered aliases
    # --------------------------------------------------------

    concept_id = extract_metric_id(
        question
    )


    if concept_id is None:
        return None


    definition = FINANCIAL_METRICS.get(
        concept_id,
        {}
    )


    aliases = definition.get(
        "aliases",
        []
    )


    if not aliases:
        return None


    # --------------------------------------------------------
    # Find the metric phrase actually used in the question.
    #
    # Longest aliases are checked first so:
    #
    #     total revenue
    #
    # is preferred over:
    #
    #     revenue
    # --------------------------------------------------------

    matched_start = None
    matched_end = None


    for alias in sorted(
        aliases,
        key=len,
        reverse=True
    ):

        pattern = (
            r"(?<!\w)"
            + re.escape(alias.lower())
            + r"(?!\w)"
        )


        match = re.search(
            pattern,
            q
        )


        if match:

            matched_start = match.start()
            matched_end = match.end()

            break


    if (
        matched_start is None
        or matched_end is None
    ):
        return None


    prefix = q[:matched_start]
    suffix = q[matched_end:]


    # --------------------------------------------------------
    # Shared cleanup for possible qualifier regions
    # --------------------------------------------------------

    def clean_candidate_region(region):

        if not region:
            return []


        # ----------------------------------------------------
        # Remove recognized segments
        # ----------------------------------------------------

        if segment == "Family of Apps":

            region = region.replace(
                "family of apps",
                " "
            )

            region = re.sub(
                r"\bfoa\b",
                " ",
                region
            )


        if segment == "Reality Labs":

            region = region.replace(
                "reality labs",
                " "
            )


        # ----------------------------------------------------
        # Remove company references
        # ----------------------------------------------------

        region = re.sub(
            r"\bmeta platforms(?:'s)?\b",
            " ",
            region
        )

        region = re.sub(
            r"\bmeta(?:'s)?\b",
            " ",
            region
        )


        # ----------------------------------------------------
        # Remove common period expressions
        # ----------------------------------------------------

        region = re.sub(
            r"\bq[1-4]\s*20\d{2}\b",
            " ",
            region
        )

        region = re.sub(
            r"\bq[1-4]\b",
            " ",
            region
        )

        region = re.sub(
            r"\bfy\s*20\d{2}\b",
            " ",
            region
        )

        region = re.sub(
            r"\b20\d{2}\b",
            " ",
            region
        )


        # ----------------------------------------------------
        # Remove punctuation
        # ----------------------------------------------------

        region = re.sub(
            r"[^a-z0-9\s]",
            " ",
            region
        )


        tokens = region.split()


        ignored_words = {
            # Question scaffolding
            "what",
            "was",
            "were",
            "is",
            "are",
            "did",
            "does",
            "do",
            "has",
            "have",
            "had",
            "how",
            "much",
            "many",
            "the",
            "a",
            "an",
            "its",

            # Relation words
            "of",
            "for",
            "in",
            "during",
            "from",
            "within",
            "at",
            "on",
            "to",
            "by",
            "as",

            # Common reporting language
            "report",
            "reported",
            "reporting",

            # Safe company-total qualifiers
            "total",
            "overall",
            "consolidated",
            "company",
            "wide",

            # Common temporal language
            "quarter",
            "quarters",
            "year",
            "years",
            "month",
            "months",
            "ended",
            # Benign question wording that can precede a metric.
            # These words do not specify a reporting segment.
            "large",
            "combined",
            "balance",
            "state",
            "liquidity",
            "hold",
            "ending",
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        }


        return [

            token

            for token in tokens

            if (
                token not in ignored_words
                and not token.isdigit()
            )
        ]


    # --------------------------------------------------------
    # 1. Qualifiers before the metric
    #
    # Example:
    #
    #     Meta's cloud operating margin
    #            ^^^^^
    # --------------------------------------------------------

    prefix_tokens = (
        clean_candidate_region(
            prefix
        )
    )


    # --------------------------------------------------------
    # 2. Qualifiers after the metric
    #
    # Only inspect suffixes introduced by relation words.
    # This deliberately avoids treating arbitrary trailing
    # language as a qualifier.
    #
    # Examples:
    #
    #     operating margin for cloud
    #     revenue in Reality Labs
    # --------------------------------------------------------

    suffix_tokens = []

    stripped_suffix = suffix.lstrip()


    if re.match(
        r"^(for|of|from|within|in)\b",
        stripped_suffix
    ):
        # Stop before a comparative clause. It describes the
        # requested operation, not a financial metric segment.
        scoped_suffix = re.split(
            r"\b(?:compared(?:\s+(?:to|with))?|versus|vs\.?|relative\s+to)\b",
            stripped_suffix,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        # A reporting period is context, not a qualifier. If
        # it occurs after a genuine segment, retain the segment
        # phrase but exclude the following temporal expression.
        scoped_suffix = re.split(
            r"\b(?:in|during|as\s+of|at|on|for)\s+"
            r"(?:(?:the\s+)?(?:first|second|third|fourth)\s+quarter"
            r"|q[1-4]\b|fy\s*20\d{2}\b|20\d{2}\b"
            r"|(?:the\s+)?(?:three|six|nine|twelve)\s+months?\b"
            r"|(?:the\s+)?quarter\s+ended\b)",
            scoped_suffix,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        suffix_tokens = clean_candidate_region(scoped_suffix)


    remaining_tokens = (
        prefix_tokens
        + suffix_tokens
    )


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