import re

from .table_detector import is_table_row


def parse_financial_number(raw_value):
    """
    Convert a raw financial-table value into
    a Python numeric value.

    Supported examples:

        60,801      -> 60801
        $60,801     -> 60801
        (685)       -> -685
        31%         -> 31
        (8)%        -> -8
        6.23        -> 6.23
        —           -> None
        -           -> None

    Percentage values are NOT divided by 100.

    Example:
        raw_value = "31%"
        value = 31
        unit = "percent"

    This keeps numeric value and unit separate.
    """

    # ========================================================
    # 1. HANDLE MISSING VALUES
    # ========================================================

    if raw_value is None:
        return None


    text = str(
        raw_value
    ).strip()


    if not text:
        return None


    # Financial tables frequently use a dash
    # to represent missing / not applicable.

    if text in {
        "—",
        "–",
        "-",
    }:
        return None


    # ========================================================
    # 2. REMOVE PERCENT SYMBOL
    # ========================================================

    # Keep percentage magnitude as displayed.
    #
    # "31%" -> 31
    #
    # The fact's unit field will separately contain
    # "percent".

    if text.endswith(
        "%"
    ):

        text = text[
            :-1
        ].strip()


    # ========================================================
    # 3. DETECT ACCOUNTING NEGATIVE FORMAT
    # ========================================================

    # Example:
    #
    # (685)  -> -685
    # (8)    -> -8

    is_parentheses_negative = (
        text.startswith(
            "("
        )
        and text.endswith(
            ")"
        )
    )


    if is_parentheses_negative:

        text = text[
            1:-1
        ].strip()


    # ========================================================
    # 4. REMOVE FINANCIAL FORMATTING
    # ========================================================

    text = (
        text
        .replace(
            "$",
            ""
        )
        .replace(
            ",",
            ""
        )
        .strip()
    )


    if not text:
        return None


    # ========================================================
    # 5. PARSE NUMBER
    # ========================================================

    try:

        if "." in text:

            value = float(
                text
            )

        else:

            value = int(
                text
            )


    except ValueError:

        # High-trust behaviour:
        #
        # Do not invent a number if the raw cell
        # contains an unsupported format.

        return None


    # ========================================================
    # 6. APPLY ACCOUNTING NEGATIVE SIGN
    # ========================================================

    if is_parentheses_negative:

        value = -value


    return value


def parse_table_row(line):

    if not is_table_row(line):
        return None

    text = line.strip()


    # -----------------------------------------
    # Remove attached footnote markers
    #
    # Example:
    # General and administrative(1)
    #
    # Important:
    # This does NOT remove:
    # net (19)
    #
    # because (19) is separated by a space
    # and can therefore be a financial value.
    # -----------------------------------------

    cleaned_text = re.sub(
        r"(?<=[A-Za-z])\(\d+\)",
        "",
        text
    )


    # -----------------------------------------
    # Financial number pattern
    #
    # Examples:
    # 60,801
    # 6.23
    # (1,139)
    # $15,848
    # -----------------------------------------

    number_pattern = re.compile(
        r"\$?\s*"
        r"(?:"
        r"\(\s*\d[\d,]*(?:\.\d+)?\s*\)"
        r"|"
        r"\d[\d,]*(?:\.\d+)?"
        r")"
    )


    matches = list(
        number_pattern.finditer(
            cleaned_text
        )
    )

    if not matches:
        return None


    # Everything before the first number
    # is treated as the metric name.

    first_number_start = matches[0].start()

    metric = cleaned_text[
        :first_number_start
    ].strip()


    raw_values = [
        match.group().strip()
        for match in matches
    ]


    values = [
        parse_financial_number(raw_value)
        for raw_value in raw_values
    ]


    return {
        "metric": metric,
        "values": values,
        "raw_values": raw_values
    }
def align_row_to_columns(row, columns):
    """
    Align numeric values in a visual PDF row
    to locally inferred table columns.

    Missing cells are preserved as None.

    Supports common financial-table formats:
        60,801
        (685)
        28%
        6.23
        —
        -

    Also handles a percentage sign extracted as
    a separate PDF word:

        31   %

    which should become:

        31%
    """

    if not row or not columns:
        return []


    # ========================================================
    # 1. SORT COLUMN ANCHORS
    # ========================================================

    sorted_columns = sorted(
        columns,
        key=lambda column: column["x"]
    )


    # ========================================================
    # 2. CREATE EMPTY CELLS
    # ========================================================

    cells = [
        None
        for _ in sorted_columns
    ]


    # ========================================================
    # 3. ESTIMATE START OF NUMERIC DATA AREA
    # ========================================================

    if len(sorted_columns) >= 2:

        first_gap = (
            sorted_columns[1]["x"]
            -
            sorted_columns[0]["x"]
        )

        data_start_x = (
            sorted_columns[0]["x"]
            -
            first_gap / 2
        )

    else:

        data_start_x = (
            sorted_columns[0]["x"]
            -
            30
        )


    # ========================================================
    # 4. FINANCIAL NUMERIC PATTERN
    # ========================================================

    numeric_pattern = re.compile(
        r"^\(?"
        r"\$?"
        r"-?"
        r"\d[\d,]*"
        r"(?:\.\d+)?"
        r"%?"
        r"\)?$"
    )


    # ========================================================
    # 5. INSPECT EACH VISUAL WORD
    # ========================================================

    for word in row:

        raw_text = (
            word["text"]
            .strip()
        )


        word_center_x = (
            word["x0"]
            +
            word["x1"]
        ) / 2


        # ----------------------------------------------------
        # Ignore content that clearly belongs to
        # the metric-label area.
        # ----------------------------------------------------

        if word_center_x < data_start_x:
            continue


        # ====================================================
        # 5A. HANDLE STANDALONE "%"
        # ====================================================

        # pdfplumber may extract:
        #
        #   31   %
        #
        # as two independent words.
        #
        # Attach "%" to the nearest populated cell.

        if raw_text == "%":

            nearest_index = min(
                range(
                    len(
                        sorted_columns
                    )
                ),
                key=lambda index: abs(
                    word_center_x
                    -
                    sorted_columns[
                        index
                    ]["x"]
                )
            )


            if (
                cells[
                    nearest_index
                ]
                is not None
            ):

                existing_value = str(
                    cells[
                        nearest_index
                    ]
                )


                if not existing_value.endswith(
                    "%"
                ):

                    cells[
                        nearest_index
                    ] = (
                        existing_value
                        +
                        "%"
                    )


            continue


        # ====================================================
        # 5B. HANDLE DASH / EM DASH
        # ====================================================

        # Financial tables often use:
        #
        #   —
        #
        # to represent no value / zero / not applicable.
        #
        # Preserve it as a raw cell for now.
        # Interpretation happens later.

        if raw_text in {
            "—",
            "-",
        }:

            nearest_index = min(
                range(
                    len(
                        sorted_columns
                    )
                ),
                key=lambda index: abs(
                    word_center_x
                    -
                    sorted_columns[
                        index
                    ]["x"]
                )
            )


            cells[
                nearest_index
            ] = raw_text

            continue


        # ====================================================
        # 5C. IGNORE NON-NUMERIC TOKENS
        # ====================================================

        if not numeric_pattern.fullmatch(
            raw_text
        ):

            continue


        # ====================================================
        # 5D. ALIGN NUMERIC VALUE TO NEAREST COLUMN
        # ====================================================

        nearest_index = min(
            range(
                len(
                    sorted_columns
                )
            ),
            key=lambda index: abs(
                word_center_x
                -
                sorted_columns[
                    index
                ]["x"]
            )
        )


        cells[
            nearest_index
        ] = raw_text


    # ========================================================
    # 6. RETURN ALIGNED CELLS
    # ========================================================

    return cells


    # -----------------------------------------------------
    # 1. Sort column anchors from left to right
    # -----------------------------------------------------

    sorted_columns = sorted(
        columns,
        key=lambda column: column["x"]
    )


    # -----------------------------------------------------
    # 2. Create empty cells
    #
    # Example:
    # [None, None, None, None]
    # -----------------------------------------------------

    cells = [
        None
        for _ in sorted_columns
    ]


    # -----------------------------------------------------
    # 3. Estimate where the table value area begins
    #
    # This prevents years/numbers inside the metric name
    # from being mistaken for cell values.
    # -----------------------------------------------------

    if len(sorted_columns) >= 2:

        first_gap = (
            sorted_columns[1]["x"]
            - sorted_columns[0]["x"]
        )

        data_start_x = (
            sorted_columns[0]["x"]
            - first_gap / 2
        )

    else:

        data_start_x = (
            sorted_columns[0]["x"] - 30
        )


    # -----------------------------------------------------
    # 4. Numeric token pattern
    #
    # Examples:
    # 60,801
    # (685)
    # 28%
    # 6.23
    # -----------------------------------------------------

    numeric_pattern = re.compile(
        r"^\(?"
        r"\$?"
        r"-?"
        r"\d[\d,]*"
        r"(?:\.\d+)?"
        r"%?"
        r"\)?$"
    )


    # -----------------------------------------------------
    # 5. Inspect every word in the visual row
    # -----------------------------------------------------

    for word in row:

        raw_text = word["text"].strip()

        if not numeric_pattern.fullmatch(
            raw_text
        ):
            continue


        word_center_x = (
            word["x0"] + word["x1"]
        ) / 2


        # Ignore numbers that occur inside the metric label.
        if word_center_x < data_start_x:
            continue


        # -------------------------------------------------
        # Find nearest local column anchor
        # -------------------------------------------------

        nearest_index = min(
            range(len(sorted_columns)),
            key=lambda index: abs(
                word_center_x
                - sorted_columns[index]["x"]
            )
        )


        cells[nearest_index] = raw_text


    # -----------------------------------------------------
    # IMPORTANT:
    # This return belongs to the FUNCTION,
    # not to the for-loop.
    # -----------------------------------------------------

    return cells

    if not row or not columns:
        return []

def reconstruct_layout_table(rows, header_info):
    """
    Reconstruct a table from visual PDF rows and
    locally inferred column anchors.

    Returns rows in the form:

    {
        "metric": "...",
        "cells": [...]
    }
    """

    columns = header_info["columns"]

    sorted_columns = sorted(
        columns,
        key=lambda column: column["x"]
    )

    if len(sorted_columns) >= 2:

        first_gap = (
            sorted_columns[1]["x"]
            - sorted_columns[0]["x"]
        )

        data_start_x = (
            sorted_columns[0]["x"]
            - first_gap / 2
        )

    else:

        data_start_x = (
            sorted_columns[0]["x"] - 30
        )


    reconstructed_rows = []

    start_row = (
        header_info["row_number"] + 1
    )


    for row in rows[start_row:]:

        cells = align_row_to_columns(
            row,
            sorted_columns
        )

        # Ignore rows with no values in any data column
        if not any(
            cell is not None
            for cell in cells
        ):
            continue


        metric_words = []

        for word in row:

            word_center_x = (
                word["x0"] + word["x1"]
            ) / 2

            if word_center_x < data_start_x:

                metric_words.append(
                    word["text"]
                )


        metric = " ".join(
            metric_words
        ).strip()


        if not metric:
            continue


        reconstructed_rows.append(
            {
                "metric": metric,
                "cells": cells,
            }
        )


    return reconstructed_rows
    # -----------------------------------------------------
    # 1. Sort columns from left to right
    # -----------------------------------------------------

    sorted_columns = sorted(
        columns,
        key=lambda column: column["x"]
    )


    # -----------------------------------------------------
    # 2. Create empty cells
    #
    # Example:
    # [None, None, None, None]
    # -----------------------------------------------------

    cells = [
        None
        for _ in sorted_columns
    ]


    # -----------------------------------------------------
    # 3. Estimate where the numeric data region begins
    #
    # We use half of the first column gap.
    # This prevents years/numbers inside the metric label
    # from being treated as table values.
    # -----------------------------------------------------

    if len(sorted_columns) >= 2:

        first_gap = (
            sorted_columns[1]["x"]
            - sorted_columns[0]["x"]
        )

        data_start_x = (
            sorted_columns[0]["x"]
            - first_gap / 2
        )

    else:

        data_start_x = (
            sorted_columns[0]["x"] - 30
        )


    # -----------------------------------------------------
    # 4. Detect numeric-looking cell tokens
    #
    # Examples:
    # 60,801
    # (685)
    # 28%
    # 6.23
    # -----------------------------------------------------

    numeric_pattern = re.compile(
        r"^\(?"
        r"\$?"
        r"-?"
        r"\d[\d,]*"
        r"(?:\.\d+)?"
        r"%?"
        r"\)?$"
    )


    for word in row:

        raw_text = word["text"].strip()

        if not numeric_pattern.fullmatch(
            raw_text
        ):
            continue


        word_center_x = (
            word["x0"] + word["x1"]
        ) / 2


        # Ignore numbers occurring inside the metric label.
        if word_center_x < data_start_x:
            continue


        # -------------------------------------------------
        # 5. Find nearest column anchor
        # -------------------------------------------------

        nearest_index = min(
            range(len(sorted_columns)),
            key=lambda index: abs(
                word_center_x
                - sorted_columns[index]["x"]
            )
        )


        # -------------------------------------------------
        # 6. Put the raw value in that column
        # -------------------------------------------------

        cells[nearest_index] = raw_text


    return cells

if __name__ == "__main__":

    test_lines = [
        (
            "Revenue $       60,801  "
            "$       47,516  "
            "$      117,111  "
            "$       89,830"
        ),

        (
            "General and administrative(1) "
            "5,609  2,663  8,222  4,943"
        ),

        (
            "Interest and other income "
            "(expense), net (19)  93  "
            "(1,139)  919"
        ),

        (
            "Net income $       15,848  "
            "$       18,337  "
            "$       42,621  "
            "$       34,981"
        ),

        (
            "Cash and cash equivalents "
            "$ 15,462  $ 35,873"
        )
    ]


    print("==============================")
    print("TABLE ROW PARSER TEST")
    print("==============================")


    for line in test_lines:

        result = parse_table_row(line)

        print("\nINPUT:")
        print(line)

        print("PARSED:")
        print(result)