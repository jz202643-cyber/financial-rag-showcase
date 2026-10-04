from .pdf_loader import load_pdf_pages
from .tables.table_detector import is_table_row
from .financial_fact_builder import build_financial_facts

def infer_fact_unit(
    metric,
    section,
    default_unit="USD millions"
):

    metric_lower = metric.lower()

    section_lower = (
        section.lower()
        if section
        else ""
    )

    # Earnings per share
    if section_lower == "earnings per share":
        return "USD per share"

    # Weighted-average shares
    if (
        "weighted-average shares"
        in section_lower
    ):
        return "shares millions"

    return default_unit

def extract_duration_table_facts(
    page_text,
    unit="USD millions"
):

    lines = [
        line.strip()
        for line in page_text.split("\n")
    ]

    duration_line = None
    year_line = None

    table_started = False
    current_section = None

    all_facts = []


    for index, line in enumerate(lines):

        if not line:
            continue


        # -----------------------------------------
        # 1. Find duration header
        # -----------------------------------------

        if (
            "months ended" in line.lower()
            and duration_line is None
        ):

            duration_line = line

            for next_line in lines[index + 1:]:

                if next_line:
                    year_line = next_line
                    break

            table_started = True

            continue


        if not table_started:
            continue


        # -----------------------------------------
        # 2. Stop at table separator
        # -----------------------------------------

        if line.startswith("_"):
            break


        # -----------------------------------------
        # 3. Detect subsection labels
        # -----------------------------------------

        if (
            line.endswith(":")
            and not is_table_row(line)
        ):

            current_section = line.rstrip(":")

            continue


        # -----------------------------------------
        # 4. Ignore non-table rows
        # -----------------------------------------

        if not is_table_row(line):
            continue


        # -----------------------------------------
        # 5. Parse row and build facts
        # -----------------------------------------

        result = build_financial_facts(
            row_line=line,
            duration_line=duration_line,
            year_line=year_line,
            unit=unit
        )


        if result is None:
            continue


        if result["status"] != "OK":

            print(
                "WARNING:",
                result
            )

            continue


        # -----------------------------------------
        # 6. Add context to EVERY fact
        # -----------------------------------------

        for fact in result["facts"]:

            fact["section"] = current_section

            fact["unit"] = infer_fact_unit(
                metric=fact["metric"],
                section=current_section,
                default_unit=unit
            )

            all_facts.append(
                fact
            )


    return all_facts

if __name__ == "__main__":

    PDF_PATH = (
        "data/"
        "Meta-Reports-Second-Quarter-2026-Results-2026.pdf"
    )

    pages = load_pdf_pages(
        PDF_PATH
    )

    # Python index 5 = PDF page 6
    page = pages[5]

    facts = extract_duration_table_facts(
        page["text"]
    )

    print("==============================")
    print("DURATION TABLE FACTS")
    print("==============================")

    print(
        "Number of facts:",
        len(facts)
    )

    for fact in facts:

        print("\nFACT:")
        print(fact)