from financial_rag.ingestion.financial_fact_builder import (
    build_layout_financial_facts,
)


def test_mixed_financial_row_units():

    rows = [
        {
            "metric": "Revenue",
            "cells": [
                "60,801",
                "47,516",
                "28%",
            ],
        },
        {
            "metric": "Operating margin",
            "cells": [
                "31%",
                "43%",
                None,
            ],
        },
        {
            "metric": "Income from operations",
            "cells": [
                "18,775",
                "20,441",
                "-8%",
            ],
        },
    ]


    columns = [
        {
            "label": "Q2 2026",
            "duration": "three",
            "end_date": "June 30",
            "year": 2026,
        },
        {
            "label": "Q2 2025",
            "duration": "three",
            "end_date": "June 30",
            "year": 2025,
        },
        {
            "label": "Q2 YoY Change",
            "duration": "three",
            "end_date": "June 30",
            "year": 2026,
        },
    ]


    facts = build_layout_financial_facts(
        rows,
        columns,
    )


    lookup = {
        (
            fact["metric"],
            fact["raw_value"],
        ):
        fact["unit"]

        for fact in facts
    }


    assert (
        lookup[
            ("Revenue", "60,801")
        ]
        ==
        "USD millions"
    )

    assert (
        lookup[
            ("Revenue", "47,516")
        ]
        ==
        "USD millions"
    )

    assert (
        lookup[
            ("Revenue", "28%")
        ]
        ==
        "percent"
    )

    assert (
        lookup[
            ("Operating margin", "31%")
        ]
        ==
        "percent"
    )

    assert (
        lookup[
            (
                "Income from operations",
                "18,775",
            )
        ]
        ==
        "USD millions"
    )

    assert (
        lookup[
            (
                "Income from operations",
                "-8%",
            )
        ]
        ==
        "percent"
    )


def test_metric_semantics_without_percent_symbol():
    column = {"label": "Q2 2026", "duration": "three", "end_date": "June 30", "year": 2026}
    rows = [{"metric": "Operating margin", "cells": ["31"]}]
    result = build_layout_financial_facts(rows, [column])
    assert result[0]["unit"] == "percent"


def test_per_share_units_and_yoy_percent():
    cols = [
        {"label": "Q2 2026", "duration": "three", "end_date": "June 30", "year": 2026},
        {"label": "YoY", "duration": "three", "end_date": "June 30", "year": 2026},
    ]
    result = build_layout_financial_facts([
        {"metric": "Diluted earnings per share (EPS)", "cells": ["6.18", "-13%"]},
    ], cols)
    assert [fact["unit"] for fact in result] == ["USD per share", "percent"]


def test_corporate_tax_amount_is_not_a_percent():
    cols = [{"label": "Q2 2026", "duration": "three", "end_date": "June 30", "year": 2026}]
    result = build_layout_financial_facts([
        {"metric": "Corporate income taxes", "cells": ["2,908"]}
    ], cols)
    assert result[0]["unit"] == "USD millions"
