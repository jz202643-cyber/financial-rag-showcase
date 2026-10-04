import re


# ============================================================
# CONSTANTS
# ============================================================

METRIC_PATTERNS = {
    "capital expenditures": [
        "capital expenditures",
        "capital expenditure",
        "capex",
    ],

    "net income": [
        "net income",
    ],

    "operating income": [
        "operating income",
        "income from operations",
    ],

    "revenue": [
        "revenue",
    ],

    "free cash flow": [
        "free cash flow",
    ],
}


GUIDANCE_MARKERS = [
    "we expect",
    "expect to",
    "continue to expect",
    "we anticipate",
    "anticipate",
    "we forecast",
    "forecast",
    "we estimate",
    "guidance",
    "outlook",
    "prior outlook",
    "expected to",
    "anticipated to",
]


EXPLANATION_MARKERS = [
    "because",
    "due to",
    "driven by",
    "primarily",
    "reflecting",
    "as a result",
    "included",
    "includes",
    "increase in",
    "decrease in",
    "higher",
    "lower",
]


QUARTER_MARKERS = {
    1: [
        "q1",
        "first quarter",
        "march 31",
    ],

    2: [
        "q2",
        "second quarter",
        "june 30",
    ],

    3: [
        "q3",
        "third quarter",
        "september 30",
    ],

    4: [
        "q4",
        "fourth quarter",
        "december 31",
    ],
}


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize_text(text):

    if text is None:
        return ""

    return str(text).strip().lower()


def get_metric_patterns(metric):

    if metric is None:
        return []

    metric = normalize_text(metric)

    return METRIC_PATTERNS.get(
        metric,
        [metric]
    )


def get_metric_context_lines(
    parsed_query,
    candidate
):
    """
    Return lines near the queried metric.

    This is safer than classifying the entire chunk,
    because one chunk may contain both actual results
    and guidance.
    """

    text = candidate.get(
        "text",
        ""
    )

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    metric = parsed_query.get(
        "metric"
    )

    patterns = get_metric_patterns(
        metric
    )


    # If no metric was extracted,
    # use the whole candidate as context.
    if not patterns:
        return lines


    matching_indexes = []

    for index, line in enumerate(lines):

        line_lower = line.lower()

        if any(
            pattern in line_lower
            for pattern in patterns
        ):
            matching_indexes.append(
                index
            )


    if not matching_indexes:
        return []


    # Include one line before and after the metric line.
    context_indexes = set()

    for index in matching_indexes:

        for nearby_index in [
            index - 1,
            index,
            index + 1,
        ]:

            if (
                0
                <= nearby_index
                < len(lines)
            ):
                context_indexes.add(
                    nearby_index
                )


    return [
        lines[index]
        for index in sorted(
            context_indexes
        )
    ]


# ============================================================
# CANDIDATE ENTITY CHECK
# ============================================================

def check_candidate_entity(
    parsed_query,
    candidate
):

    requested_entity = normalize_text(
        parsed_query.get(
            "entity"
        )
    )

    if not requested_entity:
        return True


    candidate_company = normalize_text(
        candidate.get(
            "company"
        )
    )

    candidate_text = normalize_text(
        candidate.get(
            "text"
        )
    )


    if candidate_company:

        if (
            requested_entity
            in candidate_company
            or candidate_company
            in requested_entity
        ):
            return True


    return (
        requested_entity
        in candidate_text
    )


# ============================================================
# CANDIDATE METRIC CHECK
# ============================================================

def check_candidate_metric(
    parsed_query,
    candidate
):

    metric = parsed_query.get(
        "metric"
    )

    if metric is None:
        return True


    text = normalize_text(
        candidate.get(
            "text"
        )
    )

    patterns = get_metric_patterns(
        metric
    )


    return any(
        pattern in text
        for pattern in patterns
    )


# ============================================================
# CANDIDATE PERIOD CHECK
# ============================================================

def check_candidate_period(
    parsed_query,
    candidate
):
    """
    V1 period validation uses the candidate text itself.

    We intentionally do not trust candidate["period"] yet,
    because older chunks were created with hard-coded
    Q2 2026 metadata.
    """

    requested_period = normalize_text(
        parsed_query.get(
            "period"
        )
    )

    if not requested_period:
        return True


    text = normalize_text(
        candidate.get(
            "text"
        )
    )


    # --------------------------------------------------------
    # Quarter form:
    # Q2 2026
    # --------------------------------------------------------

    quarter_match = re.fullmatch(
        r"q([1-4])\s*(20\d{2})",
        requested_period
    )

    if quarter_match:

        quarter = int(
            quarter_match.group(1)
        )

        year = quarter_match.group(2)


        if year not in text:
            return False


        markers = QUARTER_MARKERS[
            quarter
        ]


        return any(
            marker in text
            for marker in markers
        )


    # --------------------------------------------------------
    # Fiscal year form:
    # FY2026 / FY 2026
    # --------------------------------------------------------

    fiscal_match = re.fullmatch(
        r"fy\s*(20\d{2})",
        requested_period
    )

    if fiscal_match:

        year = fiscal_match.group(1)

        return year in text


    # --------------------------------------------------------
    # Bare year
    # --------------------------------------------------------

    year_match = re.fullmatch(
        r"(20\d{2})",
        requested_period
    )

    if year_match:

        return (
            year_match.group(1)
            in text
        )


    # --------------------------------------------------------
    # Fallback:
    # Require all detected years in the requested
    # period to occur in the evidence.
    # --------------------------------------------------------

    years = re.findall(
        r"\b20\d{2}\b",
        requested_period
    )

    if years:

        return all(
            year in text
            for year in years
        )


    return True


# ============================================================
# FACT TYPE
# ============================================================

def detect_candidate_fact_type(text):
    """
    Compatibility diagnostic.

    This only gives a coarse whole-chunk classification.
    Actual validation uses metric-local context below.
    """

    text = normalize_text(
        text
    )

    if any(
        marker in text
        for marker in GUIDANCE_MARKERS
    ):
        return "guidance"

    return "actual"


def check_candidate_fact_type(
    parsed_query,
    candidate
):
    """
    Determine fact type only around the queried metric.

    A chunk may contain both actual results and guidance,
    so whole-chunk classification would be unsafe.
    """

    requested_type = normalize_text(
        parsed_query.get(
            "fact_type"
        )
    )

    if not requested_type:
        return True


    context_lines = get_metric_context_lines(
        parsed_query,
        candidate
    )


    if not context_lines:
        return False


    detected_types = set()


    for line in context_lines:

        line_lower = line.lower()

        is_guidance = any(
            marker in line_lower
            for marker in GUIDANCE_MARKERS
        )


        if is_guidance:
            detected_types.add(
                "guidance"
            )

        else:
            detected_types.add(
                "actual"
            )


    return (
        requested_type
        in detected_types
    )


# ============================================================
# PROVENANCE
# ============================================================

def check_candidate_provenance(
    candidate
):

    source = candidate.get(
        "source"
    )

    page = candidate.get(
        "page"
    )

    chunk_id = candidate.get(
        "chunk_id"
    )


    return (
        bool(source)
        and page is not None
        and bool(chunk_id)
    )


# ============================================================
# EXPLANATION SIGNAL
# ============================================================

def check_explanation_signal(
    parsed_query,
    candidate
):
    """
    Soft signal only.

    It does NOT prove that the candidate fully answers
    a why/how question.
    """

    question_type = parsed_query.get(
        "question_type"
    )


    if question_type != "explanation":
        return True


    context_lines = get_metric_context_lines(
        parsed_query,
        candidate
    )


    if not context_lines:
        return False


    context_text = normalize_text(
        " ".join(
            context_lines
        )
    )


    return any(
        marker in context_text
        for marker in EXPLANATION_MARKERS
    )


# ============================================================
# NARRATIVE CANDIDATE VALIDATION
# ============================================================

def validate_narrative_candidate(
    parsed_query,
    candidate,
    require_provenance=True
):

    entity_match = (
        check_candidate_entity(
            parsed_query,
            candidate
        )
    )

    metric_match = (
        check_candidate_metric(
            parsed_query,
            candidate
        )
    )

    period_match = (
        check_candidate_period(
            parsed_query,
            candidate
        )
    )

    fact_type_match = (
        check_candidate_fact_type(
            parsed_query,
            candidate
        )
    )


    if require_provenance:

        provenance_match = (
            check_candidate_provenance(
                candidate
            )
        )

    else:

        provenance_match = True


    explanation_signal = (
        check_explanation_signal(
            parsed_query,
            candidate
        )
    )


    valid = (
        entity_match
        and metric_match
        and period_match
        and fact_type_match
        and provenance_match
    )


    rejection_reasons = []


    if not entity_match:
        rejection_reasons.append(
            "entity_mismatch"
        )

    if not metric_match:
        rejection_reasons.append(
            "metric_mismatch"
        )

    if not period_match:
        rejection_reasons.append(
            "period_mismatch"
        )

    if not fact_type_match:
        rejection_reasons.append(
            "fact_type_mismatch"
        )

    if not provenance_match:
        rejection_reasons.append(
            "missing_provenance"
        )


    return {
        "valid": valid,

        "entity_match": entity_match,
        "metric_match": metric_match,
        "period_match": period_match,
        "fact_type_match": fact_type_match,
        "provenance_match": provenance_match,

        "explanation_signal": (
            explanation_signal
        ),

        "detected_fact_type": (
            detect_candidate_fact_type(
                candidate.get(
                    "text",
                    ""
                )
            )
        ),

        "rejection_reasons": (
            rejection_reasons
        ),
    }


# ============================================================
# EVIDENCE SET EVALUATION
# ============================================================

def evaluate_candidate_set(
    parsed_query,
    candidates
):
    """
    Validate an entire Top-K candidate set.
    """

    validated = []


    for rank, candidate in enumerate(
        candidates,
        start=1
    ):

        validation = (
            validate_narrative_candidate(
                parsed_query,
                candidate,
                require_provenance=True
            )
        )


        validated.append(
            {
                "rank": rank,
                "candidate": candidate,
                "validation": validation,
            }
        )


    valid_candidates = [
        item
        for item in validated
        if item["validation"]["valid"]
    ]


    if not valid_candidates:

        status = (
            "INSUFFICIENT_EVIDENCE"
        )


    elif (
        parsed_query.get(
            "question_type"
        )
        == "explanation"
    ):

        explanatory_candidates = [
            item
            for item in valid_candidates
            if item["validation"][
                "explanation_signal"
            ]
        ]


        if explanatory_candidates:

            status = (
                "EVIDENCE_FOUND"
            )

        else:

            status = (
                "PARTIAL_EVIDENCE"
            )


    else:

        status = (
            "EVIDENCE_FOUND"
        )


    return {
        "status": status,
        "validated_candidates": validated,
        "valid_candidates": valid_candidates,
    }


# ============================================================
# BACKWARD-COMPATIBILITY WRAPPER
#
# validation_demo.py still imports validate_candidate().
# ============================================================

def validate_candidate(
    parsed_query,
    candidate
):

    return validate_narrative_candidate(
        parsed_query,
        candidate,
        require_provenance=False
    )


# ============================================================
# LEGACY STRING-BASED GATE
#
# generator.py still imports evaluate_evidence().
# We keep this temporarily until generator.py is connected
# to the new parsed-query Evidence Gate.
# ============================================================

def check_entity(
    question,
    evidence
):

    question = normalize_text(
        question
    )

    evidence = normalize_text(
        evidence
    )


    if "meta" in question:

        return (
            "meta" in evidence
        )


    return True


def check_period(
    question,
    evidence
):

    question = normalize_text(
        question
    )

    evidence = normalize_text(
        evidence
    )


    years = re.findall(
        r"\b20\d{2}\b",
        question
    )


    if years:

        if not all(
            year in evidence
            for year in years
        ):
            return False


    for quarter, markers in (
        QUARTER_MARKERS.items()
    ):

        if (
            f"q{quarter}"
            in question
        ):

            return any(
                marker in evidence
                for marker in markers
            )


    return True


def check_metric(
    question,
    evidence
):

    question = normalize_text(
        question
    )

    evidence = normalize_text(
        evidence
    )


    for metric, patterns in (
        METRIC_PATTERNS.items()
    ):

        if any(
            pattern in question
            for pattern in patterns
        ):

            return any(
                pattern in evidence
                for pattern in patterns
            )


    return True


def check_attribution(
    question,
    evidence
):

    question = normalize_text(
        question
    )

    evidence = normalize_text(
        evidence
    )


    if (
        "meta platforms shareholders"
        in question
    ):

        if (
            "noncontrolling interests"
            in evidence
        ):
            return False


        return (
            "meta platforms shareholders"
            in evidence
        )


    return True


def evaluate_evidence(
    question,
    evidence
):

    results = {
        "entity_match": (
            check_entity(
                question,
                evidence
            )
        ),

        "period_match": (
            check_period(
                question,
                evidence
            )
        ),

        "metric_match": (
            check_metric(
                question,
                evidence
            )
        ),

        "attribution_match": (
            check_attribution(
                question,
                evidence
            )
        ),
    }


    if all(
        results.values()
    ):

        status = "SUPPORTED"

    else:

        status = (
            "INSUFFICIENT_EVIDENCE"
        )


    results["status"] = status

    return results