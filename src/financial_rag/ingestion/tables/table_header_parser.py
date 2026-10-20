import re

def is_year_header_row(row):
    """
    Determine whether a visual row is primarily a year header.

    Example accepted:
        2026   2025   2026   2025

    Example rejected:
        Foreign exchange effect on 2026 revenue using 2025 rates
    """

    if not row:
        return False

    year_words = []

    for word in row:

        text = word["text"].strip()

        if re.fullmatch(
            r"(19|20)\d{2}",
            text
        ):
            year_words.append(word)

    # Need at least two year columns
    if len(year_words) < 2:
        return False

    # Most of the row must consist of years.
    #
    # This rejects narrative/metric rows containing
    # incidental year references.
    year_ratio = (
        len(year_words) / len(row)
    )

    if year_ratio < 0.6:
        return False

    return True
def find_year_header_rows(rows):
    """
    Find visual rows that look like table year headers.
    """

    results = []

    for row_number, row in enumerate(rows):

        if not is_year_header_row(row):
            continue

        columns = []

        for word in row:

            text = word["text"].strip()

            if not re.fullmatch(
                r"(19|20)\d{2}",
                text
            ):
                continue

            center_x = (
                word["x0"] + word["x1"]
            ) / 2

            columns.append(
                {
                    "year": int(text),
                    "x": center_x,
                }
            )

        results.append(
            {
                "row_number": row_number,
                "columns": columns,
            }
        )

    return results

def parse_duration_header(
    duration_line,
    year_line
):

    duration_text = duration_line.strip()
    year_text = year_line.strip()


    # -----------------------------------------
    # 1. Detect reporting-period groups
    #
    # Examples:
    # Three Months Ended June 30
    # Six Months Ended June 30
    # Nine Months Ended September 30
    # -----------------------------------------

    duration_pattern = re.compile(
        r"(Three|Six|Nine|Twelve)\s+"
        r"Months?\s+Ended\s+"
        r"([A-Za-z]+\s+\d{1,2})",
        re.IGNORECASE
    )


    duration_matches = list(
        duration_pattern.finditer(
            duration_text
        )
    )


    if not duration_matches:
        return None


    duration_groups = []

    for match in duration_matches:

        duration_name = match.group(1).lower()

        end_date = match.group(2)

        duration_groups.append(
            {
                "duration": duration_name,
                "end_date": end_date
            }
        )


    # -----------------------------------------
    # 2. Extract years
    #
    # Example:
    # 2026 2025 2026 2025
    # -----------------------------------------

    years = re.findall(
        r"\b20\d{2}\b",
        year_text
    )


    if not years:
        return None


    # -----------------------------------------
    # 3. Determine how many years belong
    # to each duration group
    # -----------------------------------------

    number_of_groups = len(
        duration_groups
    )

    if len(years) % number_of_groups != 0:
        return None


    years_per_group = (
        len(years)
        // number_of_groups
    )


    # -----------------------------------------
    # 4. Build ordered column headers
    # -----------------------------------------

    columns = []

    year_index = 0


    for group in duration_groups:

        for _ in range(
            years_per_group
        ):

            year = int(
                years[year_index]
            )

            duration = group[
                "duration"
            ]

            end_date = group[
                "end_date"
            ]

            label = (
                f"{duration.title()} Months "
                f"Ended {end_date}, {year}"
            )


            columns.append(
                {
                    "duration": duration,
                    "end_date": end_date,
                    "year": year,
                    "label": label
                }
            )


            year_index += 1


    return columns


if __name__ == "__main__":

    duration_line = (
        "Three Months Ended June 30, "
        "Six Months Ended June 30,"
    )

    year_line = (
        "2026  2025  2026  2025"
    )


    result = parse_duration_header(
        duration_line,
        year_line
    )


    print("==============================")
    print("TABLE HEADER PARSER TEST")
    print("==============================")


    for column_number, column in enumerate(
        result,
        start=1
    ):

        print(
            f"Column {column_number}:",
            column
        )