import sys
import json

from pathlib import Path
from collections import defaultdict


sys.path.insert(
    0,
    "src"
)


from financial_rag.main import (
    answer_question
)


TEST_FILE = Path(
    "evaluation/benchmark_50_portfolio.json"
)

JSON_OUTPUT = Path(
    "evaluation/benchmark_50_portfolio_results.json"
)

MD_OUTPUT = Path(
    "evaluation/benchmark_50_portfolio_results.md"
)


def pct(correct, total):

    if total == 0:
        return 0.0

    return (
        100.0
        *
        correct
        /
        total
    )


def get_evidence(result):

    evidence = result.get(
        "evidence"
    )

    if isinstance(
        evidence,
        dict
    ):
        return evidence

    answer = result.get(
        "answer"
    )

    if isinstance(
        answer,
        dict
    ):
        return answer

    return None


def safe_abstention(status):

    return status in {
        "INSUFFICIENT",
        "UNSUPPORTED",
        "AMBIGUOUS",
    }


def main():

    cases = json.loads(
        TEST_FILE.read_text(
            encoding="utf-8"
        )
    )


    if len(cases) != 50:

        raise ValueError(
            f"Expected 50 questions, "
            f"found {len(cases)}"
        )


    total = 50


    pipeline_correct = 0
    route_correct = 0
    status_correct = 0
    strict_correct = 0


    numeric_correct = 0
    numeric_total = 0


    unit_correct = 0
    unit_total = 0


    provenance_correct = 0
    provenance_total = 0


    abstention_correct = 0
    abstention_total = 0


    narrative_correct = 0
    narrative_total = 0


    categories = defaultdict(
        lambda: {
            "total": 0,
            "route": 0,
            "status": 0,
            "strict": 0,
        }
    )


    sources = defaultdict(
        lambda: {
            "total": 0,
            "strict": 0,
        }
    )


    records = []


    print("=" * 88)
    print(
        "FINANCIAL RAG — "
        "50 QUESTION PORTFOLIO BENCHMARK"
    )
    print("=" * 88)


    for case in cases:

        category = case[
            "category"
        ]

        source_set = case.get(
            "source_set",
            "unknown"
        )


        categories[
            category
        ]["total"] += 1


        sources[
            source_set
        ]["total"] += 1


        try:

            result = answer_question(
                case["question"]
            )

            pipeline_pass = True

            pipeline_correct += 1

            error = None


        except Exception as exc:

            result = {}

            pipeline_pass = False

            error = repr(
                exc
            )


        actual_route = result.get(
            "route"
        )

        actual_status = result.get(
            "status"
        )


        route_pass = (
            actual_route
            ==
            case[
                "expected_route"
            ]
        )


        status_pass = (
            actual_status
            ==
            case[
                "expected_status"
            ]
        )


        if route_pass:

            route_correct += 1

            categories[
                category
            ]["route"] += 1


        if status_pass:

            status_correct += 1

            categories[
                category
            ]["status"] += 1


        numeric_pass = None
        unit_pass = None
        provenance_pass = None
        abstention_pass = None
        narrative_pass = None


        actual_value = None
        actual_unit = None


        # ====================================================
        # NUMERIC
        # ====================================================

        if "expected_value" in case:

            numeric_total += 1
            unit_total += 1
            provenance_total += 1


            evidence = get_evidence(
                result
            )


            if evidence:

                actual_value = (
                    evidence.get(
                        "value"
                    )
                )

                actual_unit = (
                    evidence.get(
                        "unit"
                    )
                )


            expected_value = case[
                "expected_value"
            ]


            try:

                numeric_pass = (
                    abs(
                        float(
                            actual_value
                        )
                        -
                        float(
                            expected_value
                        )
                    )
                    <
                    1e-6
                )

            except Exception:

                numeric_pass = False


            if numeric_pass:

                numeric_correct += 1


            unit_pass = (
                actual_unit
                ==
                case.get(
                    "expected_unit"
                )
            )


            if unit_pass:

                unit_correct += 1


            provenance_pass = (
                evidence is not None
                and bool(
                    evidence.get(
                        "source"
                    )
                )
                and evidence.get(
                    "page"
                )
                is not None
            )


            if provenance_pass:

                provenance_correct += 1


        # ====================================================
        # NARRATIVE CONTENT
        # ====================================================

        if "expected_contains" in case:

            narrative_total += 1


            answer = str(
                result.get(
                    "answer",
                    ""
                )
            ).lower()


            narrative_pass = all(

                str(token).lower()
                in answer

                for token
                in case[
                    "expected_contains"
                ]
            )


            if narrative_pass:

                narrative_correct += 1


        # ====================================================
        # SAFE ABSTENTION
        # ====================================================

        if category in {
            "abstention",
            "unsupported",
        }:

            abstention_total += 1


            abstention_pass = (
                safe_abstention(
                    actual_status
                )
            )


            if abstention_pass:

                abstention_correct += 1


        # ====================================================
        # STRICT CASE
        # ====================================================

        requirements = [
            pipeline_pass,
            route_pass,
            status_pass,
        ]


        if numeric_pass is not None:

            requirements.extend(
                [
                    numeric_pass,
                    unit_pass,
                    provenance_pass,
                ]
            )


        if narrative_pass is not None:

            requirements.append(
                narrative_pass
            )


        strict_pass = all(
            requirements
        )


        if strict_pass:

            strict_correct += 1

            categories[
                category
            ]["strict"] += 1

            sources[
                source_set
            ]["strict"] += 1


        records.append(
            {
                "id":
                    case["id"],

                "source_set":
                    source_set,

                "source_question_id":
                    case.get(
                        "source_question_id"
                    ),

                "category":
                    category,

                "question":
                    case["question"],

                "expected_route":
                    case[
                        "expected_route"
                    ],

                "actual_route":
                    actual_route,

                "route_pass":
                    route_pass,

                "expected_status":
                    case[
                        "expected_status"
                    ],

                "actual_status":
                    actual_status,

                "status_pass":
                    status_pass,

                "expected_value":
                    case.get(
                        "expected_value"
                    ),

                "actual_value":
                    actual_value,

                "numeric_pass":
                    numeric_pass,

                "expected_unit":
                    case.get(
                        "expected_unit"
                    ),

                "actual_unit":
                    actual_unit,

                "unit_pass":
                    unit_pass,

                "provenance_pass":
                    provenance_pass,

                "safe_abstention_pass":
                    abstention_pass,

                "narrative_content_pass":
                    narrative_pass,

                "strict_pass":
                    strict_pass,

                "error":
                    error,
            }
        )


        marks = [

            "R✓"
            if route_pass
            else "R✗",

            "S✓"
            if status_pass
            else "S✗",
        ]


        if numeric_pass is not None:

            marks.append(
                "N✓"
                if numeric_pass
                else "N✗"
            )


        if abstention_pass is not None:

            marks.append(
                "A✓"
                if abstention_pass
                else "A✗"
            )


        if narrative_pass is not None:

            marks.append(
                "T✓"
                if narrative_pass
                else "T✗"
            )


        print(
            f"{case['id']:<7}"
            f"{category:<23}"
            f"{' '.join(marks):<17}"
            f"{str(actual_route):<12}"
            f"{actual_status}"
        )


    metrics = [

        (
            "Pipeline Completion",
            pipeline_correct,
            total,
        ),

        (
            "Route Accuracy",
            route_correct,
            total,
        ),

        (
            "Status / Behaviour",
            status_correct,
            total,
        ),

        (
            "Strict Case Accuracy",
            strict_correct,
            total,
        ),

        (
            "Structured Numeric",
            numeric_correct,
            numeric_total,
        ),

        (
            "Unit Accuracy",
            unit_correct,
            unit_total,
        ),

        (
            "Evidence Provenance",
            provenance_correct,
            provenance_total,
        ),

        (
            "Safe Abstention",
            abstention_correct,
            abstention_total,
        ),
    ]


    if narrative_total:

        metrics.append(
            (
                "Narrative Content",
                narrative_correct,
                narrative_total,
            )
        )


    print()
    print("=" * 88)
    print(
        "PORTFOLIO BENCHMARK SUMMARY"
    )
    print("=" * 88)


    for (
        label,
        correct,
        denominator
    ) in metrics:

        print(
            f"{label:<27}"
            f"{correct}/{denominator} "
            f"({pct(correct, denominator):.1f}%)"
        )


    print()
    print("CATEGORY BREAKDOWN")
    print("-" * 88)


    for (
        category,
        stats
    ) in categories.items():

        n = stats[
            "total"
        ]

        print(
            f"{category:<24}"
            f"Strict "
            f"{stats['strict']}/{n} "
            f"| Route "
            f"{stats['route']}/{n} "
            f"| Status "
            f"{stats['status']}/{n}"
        )


    print()
    print("SOURCE BREAKDOWN")
    print("-" * 88)


    for (
        source,
        stats
    ) in sources.items():

        print(
            f"{source:<24}"
            f"Strict "
            f"{stats['strict']}/"
            f"{stats['total']} "
            f"({pct(stats['strict'], stats['total']):.1f}%)"
        )


    output = {

        "benchmark_type":
            "50-case curated portfolio benchmark",

        "methodology":
            {
                "development_40_cases":
                    25,

                "original_50_cases":
                    25,

                "held_out":
                    False,

                "note":
                    (
                        "This benchmark combines 25 cases "
                        "from the development benchmark with "
                        "25 cases from the previous 50-case "
                        "evaluation. It is intended as a "
                        "representative portfolio benchmark, "
                        "not a held-out generalisation test."
                    ),
            },

        "summary":
            {
                label: {
                    "correct":
                        correct,

                    "total":
                        denominator,

                    "percentage":
                        pct(
                            correct,
                            denominator
                        ),
                }

                for (
                    label,
                    correct,
                    denominator
                )
                in metrics
            },

        "cases":
            records,
    }


    JSON_OUTPUT.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


    md = [

        "# Financial RAG — 50-Case Portfolio Benchmark\n\n",

        "This benchmark contains 50 representative "
        "financial QA cases: 25 drawn from the development "
        "benchmark and 25 drawn from the broader evaluation set.\n\n",

        "It is a **curated portfolio benchmark**, not a held-out "
        "generalisation test.\n\n",

        "## Results\n\n",

        "| Metric | Result |\n",

        "|---|---:|\n",
    ]


    for (
        label,
        correct,
        denominator
    ) in metrics:

        md.append(
            f"| {label} | "
            f"{correct}/{denominator} "
            f"({pct(correct, denominator):.1f}%) |\n"
        )


    md.extend(
        [
            "\n## Test Cases\n\n",

            "| ID | Source | Category | Question | Strict Result |\n",

            "|---|---|---|---|---|\n",
        ]
    )


    for record in records:

        question = (
            record[
                "question"
            ]
            .replace(
                "|",
                "\\|"
            )
        )


        result = (
            "PASS"
            if record[
                "strict_pass"
            ]
            else "FAIL"
        )


        md.append(
            f"| {record['id']} "
            f"| {record['source_set']} "
            f"| {record['category']} "
            f"| {question} "
            f"| {result} |\n"
        )


    MD_OUTPUT.write_text(
        "".join(
            md
        ),
        encoding="utf-8"
    )


    print()
    print("Saved:")
    print(JSON_OUTPUT)
    print(MD_OUTPUT)


if __name__ == "__main__":
    main()
