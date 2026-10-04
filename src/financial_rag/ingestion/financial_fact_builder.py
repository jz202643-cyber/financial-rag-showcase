from .tables.table_row_parser import parse_table_row
from .tables.table_header_parser import parse_duration_header


def build_financial_facts(
    row_line,
    duration_line,
    year_line,
    unit="USD millions"
):

    # -----------------------------------------
    # 1. Parse the financial row
    # -----------------------------------------

    parsed_row = parse_table_row(
        row_line
    )

    if parsed_row is None:
        return None


    # -----------------------------------------
    # 2. Parse the table headers
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
    #
    # Number of values must equal
    # number of table columns.
    # -----------------------------------------

    if len(values) != len(columns):

        return {
            "status": "COLUMN_VALUE_MISMATCH",
            "metric": parsed_row["metric"],
            "number_of_values": len(values),
            "number_of_columns": len(columns)
        }


    # -----------------------------------------
    # 4. Connect each value to its column
    # -----------------------------------------

    facts = []


    for column, value in zip(
        columns,
        values
    ):

        fact = {
            "metric": parsed_row["metric"],
            "period": column["label"],
            "duration": column["duration"],
            "end_date": column["end_date"],
            "year": column["year"],
            "value": value,
            "unit": unit
        }

        facts.append(
            fact
        )


    # -----------------------------------------
    # 5. Return structured row
    # -----------------------------------------

    return {
        "status": "OK",
        "metric": parsed_row["metric"],
        "facts": facts
    }


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


    print("==============================")
    print("FINANCIAL FACT BUILDER TEST")
    print("==============================")


    print(
        "Metric:",
        result["metric"]
    )


    for fact in result["facts"]:

        print("\nFACT:")

        print(fact)
def build_layout_financial_facts(
    reconstructed_rows,
    semantic_columns,
    default_unit="USD millions"
):
    """
    Convert a reconstructed layout-aware table
    into individual financial facts.

    Missing cells (None) are skipped.
    """

    facts = []

    for row in reconstructed_rows:

        metric = row["metric"]
        cells = row["cells"]

        # Safety check:
        # number of cells must match number of columns
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


def build_layout_financial_facts(
    reconstructed_rows,
    semantic_columns,
    default_unit="USD millions"
):
    """
    Convert a reconstructed layout-aware table
    into individual financial facts.

    Missing cells (None) are skipped.

    Percentage units are inferred from either:
        1. the metric label itself
        2. percentage symbols inside the table cells

    Example:
        Operating margin | 31% | 43%

    The metric label does not contain "%",
    therefore cell values must also be inspected.
    """

    facts = []

    for row in reconstructed_rows:

        metric = row["metric"]
        cells = row["cells"]


        # ====================================================
        # 1. SAFETY CHECK
        # ====================================================

        # Number of reconstructed cells must match
        # the number of semantic columns.

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


        # ====================================================
        # 2. INFER UNIT
        # ====================================================

        # A percentage metric may not contain "%"
        # in its label.
        #
        # Example:
        #
        # Operating margin
        # 31%
        # 43%
        #
        # Therefore inspect the actual cells as well.

        has_percentage_cell = any(
            (
                cell is not None
                and "%" in str(cell)
            )
            for cell in cells
        )


        if (
            "%" in metric
            or has_percentage_cell
        ):

            unit = "percent"

        else:

            unit = default_unit


        # ====================================================
        # 3. BUILD ONE FACT PER CELL
        # ====================================================

        for cell, column in zip(
            cells,
            semantic_columns
        ):

            # -----------------------------------------------
            # Preserve missing cells.
            #
            # Example:
            #
            # [100, None, 120, None]
            #
            # None should NOT become a financial fact.
            # -----------------------------------------------

            if cell is None:
                continue


            # -----------------------------------------------
            # Create structured financial fact.
            # -----------------------------------------------

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