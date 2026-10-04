from pathlib import Path

from .query_understanding.query_parser import (
    parse_query,
    route_query,
)

from .retrieval.retriever import (
    retrieve_evidence,
)

from .retrieval.structured_retriever import (
    load_financial_facts,
    retrieve_financial_facts,
)

from .generation.evidence_gate import (
    evaluate_candidate_set,
)

from .generation.evidence_composer import (
    compose_evidence_set,
)

from .generation.generator import (
    generate_narrative_answer,
)

from .domain_rules import (
    apply_domain_rules,
    fallback_structured_fact,
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

FACTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "meta_q2_2026_financial_facts.json"
)


# ============================================================
# MAIN PIPELINE
# ============================================================

def answer_question(question):

    # --------------------------------------------------------
    # 1. Query understanding
    # --------------------------------------------------------

    parsed_query = parse_query(
        question
    )


    # --------------------------------------------------------
    # 2. Original router
    # --------------------------------------------------------

    route = route_query(
        parsed_query
    )


    # --------------------------------------------------------
    # 3. Finance-domain normalisation layer
    # --------------------------------------------------------

    parsed_query, route = (
        apply_domain_rules(
            question,
            parsed_query,
            route,
        )
    )


    # ========================================================
    # UNSUPPORTED
    # ========================================================

    if route == "unsupported":

        return {
            "status": "UNSUPPORTED",
            "route": "unsupported",
            "query": parsed_query,
        }


    # ========================================================
    # STRUCTURED PATH
    # ========================================================

    if route == "structured":


        # ----------------------------------------------------
        # Qualifier safety gate
        # ----------------------------------------------------

        if (
            parsed_query.get(
                "qualifier_status"
            )
            == "unresolved"
        ):

            return {
                "status": "INSUFFICIENT",
                "route": "structured",
                "query": parsed_query,
                "reason": (
                    "Unresolved metric qualifier."
                ),
                "matches": [],
            }


        facts = load_financial_facts(
            FACTS_PATH
        )


        # ----------------------------------------------------
        # Original exact retrieval
        # ----------------------------------------------------

        try:

            matches = (
                retrieve_financial_facts(
                    facts=facts,
                    entity=parsed_query.get(
                        "entity"
                    ),
                    metric=parsed_query.get(
                        "metric"
                    ),
                    period=parsed_query.get(
                        "period"
                    ),
                )
            )

        except Exception:

            matches = []


        # ----------------------------------------------------
        # Tolerant structured fallback
        # ----------------------------------------------------

        if len(matches) != 1:

            fallback_fact = (
                fallback_structured_fact(
                    facts,
                    question,
                    parsed_query,
                )
            )


            if fallback_fact is not None:

                return {
                    "status": "SUPPORTED",
                    "route": "structured",
                    "query": parsed_query,
                    "evidence": fallback_fact,
                    "retrieval_mode":
                        "structured_fallback",
                }


        # ----------------------------------------------------
        # Exact result
        # ----------------------------------------------------

        if len(matches) == 1:

            return {
                "status": "SUPPORTED",
                "route": "structured",
                "query": parsed_query,
                "evidence": matches[0],
                "retrieval_mode":
                    "structured_exact",
            }


        if len(matches) > 1:

            return {
                "status": "AMBIGUOUS",
                "route": "structured",
                "query": parsed_query,
                "matches": matches,
            }


        return {
            "status": "INSUFFICIENT",
            "route": "structured",
            "query": parsed_query,
            "matches": [],
        }


    # ========================================================
    # NARRATIVE PATH
    # ========================================================

    if route == "narrative":

        retrieval_result = (
            retrieve_evidence(
                question
            )
        )

        candidates = (
            retrieval_result[
                "candidates"
            ]
        )


        gate_result = (
            evaluate_candidate_set(
                parsed_query,
                candidates,
            )
        )


        valid_candidates = (
            gate_result[
                "valid_candidates"
            ]
        )


        composition_result = (
            compose_evidence_set(
                parsed_query,
                valid_candidates,
            )
        )


        answerability_status = (
            composition_result[
                "status"
            ]
        )


        selected_evidence = (
            composition_result[
                "selected_evidence"
            ]
        )


        generation_result = (
            generate_narrative_answer(
                question=question,
                answerability_status=(
                    answerability_status
                ),
                selected_evidence=(
                    selected_evidence
                ),
            )
        )


        return {
            "status":
                generation_result[
                    "status"
                ],

            "route":
                "narrative",

            "query":
                parsed_query,

            "candidates":
                candidates,

            "validated_candidates":
                gate_result[
                    "validated_candidates"
                ],

            "valid_candidates":
                valid_candidates,

            "answerability_status":
                answerability_status,

            "num_valid_candidates":
                composition_result[
                    "num_valid_candidates"
                ],

            "num_selected":
                composition_result[
                    "num_selected"
                ],

            "selected_evidence":
                selected_evidence,

            "llm_called":
                generation_result[
                    "llm_called"
                ],

            "answer":
                generation_result[
                    "answer"
                ],

            "generation_error":
                generation_result.get(
                    "error"
                ),
        }


    return {
        "status": "UNSUPPORTED",
        "route": "unsupported",
        "query": parsed_query,
    }
