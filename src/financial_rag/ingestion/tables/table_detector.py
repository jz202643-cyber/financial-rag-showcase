import re


# ============================================================
# 1. TABLE ROW DETECTION
# ============================================================

def is_table_row(line):
    """
    Determine whether a line looks like a financial table row.
    """

    text = line.strip()

    if not text:
        return False


    # Exclude obvious footnotes
    if re.match(
        r"^\(\d+\)\s+[A-Za-z]",
        text
    ):
        return False


    # Exclude duration headers
    duration_markers = [
        "three months ended",
        "six months ended",
        "nine months ended",
        "twelve months ended",
        "year ended",
        "years ended",
    ]

    text_lower = text.lower()

    if any(
        marker in text_lower
        for marker in duration_markers
    ):
        return False


    # Exclude pure year / numeric header rows
    # Example:
    # 2026  2025  2026  2025
    if re.fullmatch(
        r"[\d\s,]+",
        text
    ):
        return False


    # Financial rows normally begin with a metric name
    if not re.match(
        r"^[A-Za-z]",
        text
    ):
        return False


    # Detect financial-looking numbers
    number_pattern = (
        r"\(?"
        r"\$?"
        r"\s*"
        r"\d[\d,]*"
        r"(?:\.\d+)?"
        r"\)?"
    )

    numbers = re.findall(
        number_pattern,
        text
    )


    # Require at least two numeric values
    if len(numbers) < 2:
        return False


    return True


# ============================================================
# 2. DURATION HEADER DETECTION
# ============================================================

def is_duration_header(line):
    """
    Detect a duration-style table header.

    Example:
    Three Months Ended June 30, Six Months Ended June 30,
    """

    text = line.strip().lower()

    if not text:
        return False

    duration_markers = [
        "three months ended",
        "six months ended",
        "nine months ended",
        "twelve months ended",
    ]

    return any(
        marker in text
        for marker in duration_markers
    )


# ============================================================
# 3. FIND DURATION HEADERS
# ============================================================

def find_duration_headers(text):
    """
    Find all duration headers inside a statement block.
    """

    lines = text.split("\n")

    headers = []

    for line_number, line in enumerate(
        lines,
        start=1
    ):

        if is_duration_header(line):

            headers.append(
                {
                    "line_number": line_number,
                    "text": line.strip(),
                }
            )

    return headers


# ============================================================
# 4. BUILD DURATION TABLE BLOCKS
# ============================================================

def build_duration_table_blocks(text):
    """
    Split a statement block into coarse table blocks.

    Every duration header starts a new candidate table block.

    A block ends immediately before the next duration header,
    or at the end of the statement.
    """

    lines = text.split("\n")

    headers = find_duration_headers(text)

    # No duration headers -> no duration table blocks
    if not headers:
        return []


    table_blocks = []


    for index, header in enumerate(headers):

        # Header line numbers start at 1,
        # but Python list indexes start at 0.
        start_index = (
            header["line_number"] - 1
        )


        # If another header exists,
        # current block ends immediately before it.
        if index + 1 < len(headers):

            next_header = headers[index + 1]

            end_index = (
                next_header["line_number"] - 1
            )

        else:

            # Last table continues to end of statement
            end_index = len(lines)


        block_lines = lines[
            start_index:end_index
        ]


        table_blocks.append(
            {
                "table_number": index + 1,

                "start_line": start_index + 1,

                "end_line": end_index,

                "header": header["text"],

                "lines": block_lines,

                "text": "\n".join(block_lines),
            }
        )


    return table_blocks


# ============================================================
# 5. DEVELOPMENT TEST
# ============================================================

if __name__ == "__main__":

    print("==============================")
    print("TABLE DETECTOR TEST")
    print("==============================")


    sample_statement = """
Segment Information
Three Months Ended June 30, Six Months Ended June 30,
2026 2025 2026 2025
Advertising 58,137 46,300 112,000 87,000
Other revenue 2,233 1,216 4,000 2,000

Some text between tables

Three Months Ended June 30, Six Months Ended June 30,
2026 2025 2026 2025
Family of Apps 60,370 47,000 116,000 89,000
Reality Labs 431 370 800 700
"""


    headers = find_duration_headers(
        sample_statement
    )


    print(
        "Headers found:",
        len(headers)
    )

    for header in headers:

        print(
            header
        )


    print("\n==============================")
    print("TABLE BLOCKS")
    print("==============================")


    table_blocks = build_duration_table_blocks(
        sample_statement
    )


    print(
        "Table blocks:",
        len(table_blocks)
    )


    for block in table_blocks:

        print(
            f"\nTable {block['table_number']}"
        )

        print(
            f"Lines "
            f"{block['start_line']} "
            f"to "
            f"{block['end_line']}"
        )

        print(
            "Header:",
            block["header"]
        )

        print(
            block["text"]
        )