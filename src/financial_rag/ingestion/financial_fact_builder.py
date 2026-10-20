import re
from .tables.table_row_parser import parse_table_row
from .tables.table_header_parser import parse_duration_header



def build_financial_facts(
    row_line,
    duration_line,
    year_line,
    unit="USD millions"
):

    # -----------------------------------------
    # 1. Parse financial row
    # -----------------------------------------

    parsed_row = parse_table_row(
        row_line
    )

    if parsed_row is None:
        return None


    # -----------------------------------------
    # 2. Parse headers
    # -----------------------------------------

    columns = parse_duration_header(
        duration_line,
        year_line
    )

    if columns is None:
        return None


    values = parsed_row["values"]


    # -----------------------------------------
    # 3. Safety check
    # -----------------------------------------

    if len(values) != len(columns):

        return {
            "status": "COLUMN_VALUE_MISMATCH",
            "metric": parsed_row["metric"],
            "number_of_values": len(values),
            "number_of_columns": len(columns)
        }


    # -----------------------------------------
    # 4. Build facts
    # -----------------------------------------

    facts = []


    for column, value in zip(
        columns,
        values
    ):

        facts.append(
            {
                "metric": parsed_row["metric"],
                "period": column["label"],
                "duration": column["duration"],
                "end_date": column["end_date"],
                "year": column["year"],
                "value": value,
                "unit": unit
            }
        )


    return {
        "status": "OK",
        "metric": parsed_row["metric"],
        "facts": facts
    }




def build_layout_financial_facts(
    reconstructed_rows,
    semantic_columns,
    default_unit="USD millions"
):
    """
    Convert reconstructed layout-aware table rows
    into individual structured financial facts.

    Unit inference is performed PER CELL.

    This is important because one financial row may
    contain both monetary values and auxiliary
    percentage-change columns.

    Example:

        Revenue | 60,801 | 47,516 | 28%

    Here:
        60,801 -> USD millions
        47,516 -> USD millions
        28%    -> percent
    """

    facts = []


    for row in reconstructed_rows:

        metric = row["metric"]
        cells = row["cells"]


        # ----------------------------------------------------
        # Safety check
        # ----------------------------------------------------

        if len(cells) != len(semantic_columns):

            print(
                "WARNING:",
                {
                    "status": "COLUMN_VALUE_MISMATCH",
                    "metric": metric,
                    "number_of_cells": len(cells),
                    "number_of_columns": len(
                        semantic_columns
                    ),
                }
            )

            continue


        # ----------------------------------------------------
        # Metric-level percentage semantics
        # ----------------------------------------------------

        metric_lower = metric.lower()


        # Match complete semantic words rather than substrings;
        # e.g. "rate" must not match the end of "corporate".
        metric_is_percentage = bool(re.search(
            r"\b(?:margin|rate|percentage|growth)\b",
            metric_lower,
        ))
        metric_is_per_share = bool(re.search(
            r"\b(?:eps|per share)\b",
            metric_lower,
        ))


        # ----------------------------------------------------
        # Build one fact per cell
        # ----------------------------------------------------

        for cell, column in zip(
            cells,
            semantic_columns
        ):

            if cell is None:
                continue


            # -----------------------------------------------
            # IMPORTANT:
            # infer the unit for THIS CELL,
            # not for the entire row.
            # -----------------------------------------------

            cell_is_percentage = (
                "%" in str(cell)
            )


            if metric_is_percentage or cell_is_percentage:
                unit = "percent"
            elif metric_is_per_share:
                # Income statement values are usually USD millions,
                # except for explicitly per-share figures.
                currency = default_unit.split()[0]
                unit = f"{currency} per share"
            else:
                unit = default_unit


            facts.append(
                {
                    "metric": metric,

                    "period": column[
                        "label"
                    ],

                    "duration": column[
                        "duration"
                    ],

                    "end_date": column[
                        "end_date"
                    ],

                    "year": column[
                        "year"
                    ],

                    "raw_value": cell,

                    "unit": unit,
                }
            )


    return facts


if __name__ == "__main__":


    duration_line = (
        "Three Months Ended June 30, "
        "Six Months Ended June 30,"
    )


    year_line = (
        "2026  2025  2026  2025"
    )


    revenue_line = (
        "Revenue $       60,801  "
        "$       47,516  "
        "$      117,111  "
        "$       89,830"
    )


    result = build_financial_facts(
        revenue_line,
        duration_line,
        year_line
    )


    print(
        "=============================="
    )

    print(
        "FINANCIAL FACT BUILDER TEST"
    )

    print(
        "=============================="
    )


    print(
        result
    )