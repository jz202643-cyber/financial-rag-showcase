import re

from .evidence_gate import (
    get_metric_context_lines,
)


# ============================================================
# CONSTANTS
# ============================================================

COMPARISON_MARKERS = [
    "%",
    "change",
    "margin",
    "cost",
    "costs",
    "expense",
    "expenses",
    "revenue",
    "increase",
    "increased",
    "decrease",
    "decreased",
    "higher",
    "lower",
    "versus",
    " vs ",
]


# ============================================================
# QUANTITATIVE COMPARISON SIGNAL
# ============================================================

def has_quantitative_comparison_signal(
    parsed_query,
    candidate
):
    """
    Check whether a valid candidate contains enough
    quantitative/comparative information to help answer
    an explanation question.

    This is a soft answerability signal.

    Example:
        Costs and expenses: 42,026 vs 27,075 (+55%)
        Income from operations: 18,775 vs 20,441 (-8%)

    Such evidence may support an explanation even when
    the source does not explicitly contain words like
    "because" or "due to".
    """

    context_lines = get_metric_context_lines(
        parsed_query,
        candidate
    )


    if not context_lines:
        return False


    context_text = " ".join(
        context_lines
    ).lower()


    # --------------------------------------------------------
    # Detect financial numbers
    # --------------------------------------------------------

    numbers = re.findall(
        r"-?\(?\$?\d[\d,]*(?:\.\d+)?\)?",
        context_text
    )


    has_multiple_numbers = (
        len(numbers) >= 2
    )


    # --------------------------------------------------------
    # Detect comparative / financial context
    # --------------------------------------------------------

    has_comparison_marker = any(
        marker in context_text
        for marker in COMPARISON_MARKERS
    )


    return (
        has_multiple_numbers
        and has_comparison_marker
    )


# ============================================================
# EVIDENCE SET COMPOSITION
# ============================================================

def compose_evidence_set(
    parsed_query,
    valid_candidates
):
    """
    Compose already-valid candidates into a smaller
    evidence set.

    V1 selection rule:

        number of selected evidence
        =
        max(1, number of valid candidates - 1)

    Example:

        1 valid candidate  -> select 1
        2 valid candidates -> select 1
        3 valid candidates -> select 2
        4 valid candidates -> select 3
        5 valid candidates -> select 4

    The candidates are assumed to remain ordered by
    retrieval / reranker rank.

    This function DOES NOT generate an answer.
    It only determines whether the selected evidence
    appears sufficient for later answer generation.
    """


    # --------------------------------------------------------
    # No valid evidence
    # --------------------------------------------------------

    if not valid_candidates:

        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "num_valid_candidates": 0,
            "num_selected": 0,
            "selected_evidence": [],
        }


    # --------------------------------------------------------
    # Determine how many valid candidates to select
    # --------------------------------------------------------

    num_valid = len(
        valid_candidates
    )


    num_to_select = max(
        1,
        num_valid - 1
    )


    selected = valid_candidates[
        :num_to_select
    ]


    # --------------------------------------------------------
    # Non-explanation questions
    #
    # For V1, already-valid evidence is considered enough.
    # --------------------------------------------------------

    if (
        parsed_query.get(
            "question_type"
        )
        != "explanation"
    ):

        return {
            "status": "ANSWERABLE",
            "num_valid_candidates": num_valid,
            "num_selected": num_to_select,
            "selected_evidence": selected,
        }


    # --------------------------------------------------------
    # Explanation questions
    #
    # Need additional evidence that supports explanation.
    # --------------------------------------------------------

    answerability_found = False


    for item in selected:

        candidate = item[
            "candidate"
        ]

        validation = item[
            "validation"
        ]


        # ----------------------------------------------------
        # Signal 1:
        # Explicit explanation language
        #
        # e.g. because / due to / driven by
        # ----------------------------------------------------

        direct_explanation = validation.get(
            "explanation_signal",
            False
        )


        # ----------------------------------------------------
        # Signal 2:
        # Quantitative comparative evidence
        #
        # e.g.
        # revenue +28%
        # expenses +55%
        # operating income -8%
        # ----------------------------------------------------

        quantitative_comparison = (
            has_quantitative_comparison_signal(
                parsed_query,
                candidate
            )
        )


        # ----------------------------------------------------
        # Store composition diagnostics
        # ----------------------------------------------------

        item[
            "composition"
        ] = {
            "direct_explanation": (
                direct_explanation
            ),

            "quantitative_comparison": (
                quantitative_comparison
            ),
        }


        # ----------------------------------------------------
        # Candidate contributes to answerability if
        # either signal is present.
        # ----------------------------------------------------

        if (
            direct_explanation
            or quantitative_comparison
        ):

            answerability_found = True


    # --------------------------------------------------------
    # Final answerability decision
    # --------------------------------------------------------

    if answerability_found:

        status = "ANSWERABLE"

    else:

        status = "PARTIAL_EVIDENCE"


    return {
        "status": status,
        "num_valid_candidates": num_valid,
        "num_selected": num_to_select,
        "selected_evidence": selected,
    }