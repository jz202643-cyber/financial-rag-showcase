from pathlib import Path
from pypdf import PdfReader
import pdfplumber

def load_pdf_words(pdf_path):
    """
    Load PDF words together with their page coordinates.

    This preserves layout information that plain-text
    extraction may lose.

    Each word contains:
        text
        x0
        x1
        top
        bottom
    """

    pages = []

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            raw_words = page.extract_words()

            words = []

            for word in raw_words:

                words.append(
                    {
                        "text": word["text"],
                        "x0": word["x0"],
                        "x1": word["x1"],
                        "top": word["top"],
                        "bottom": word["bottom"],
                    }
                )

            pages.append(
                {
                    "page": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "words": words,
                    "source": str(pdf_path),
                }
            )

    return pages
def load_pdf_pages(pdf_path):

    reader = PdfReader(pdf_path)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text() or ""

        page_data = {
            "page": page_number,
            "text": text.strip(),
            "source": Path(pdf_path).name
        }

        pages.append(page_data)

    return pages


if __name__ == "__main__":

    pdf_path = Path(
        "data/Meta-Reports-Second-Quarter-2026-Results-2026.pdf"
    )

    pages = load_pdf_pages(pdf_path)

    print("Number of pages:", len(pages))

    print("\n==============================")
    print("PAGE 1")
    print("==============================")

    print(pages[0]["text"][:2000])
def group_words_into_rows(words, y_tolerance=3):
    """
    Group PDF words into visual rows using their vertical position.
    """

    if not words:
        return []

    sorted_words = sorted(
        words,
        key=lambda word: (
            word["top"],
            word["x0"]
        )
    )

    rows = []

    current_row = []
    current_top = None

    for word in sorted_words:

        if current_top is None:
            current_row = [word]
            current_top = word["top"]
            continue

        if abs(word["top"] - current_top) <= y_tolerance:
            current_row.append(word)

        else:
            current_row = sorted(
                current_row,
                key=lambda item: item["x0"]
            )

            rows.append(current_row)

            current_row = [word]
            current_top = word["top"]

    if current_row:

        current_row = sorted(
            current_row,
            key=lambda item: item["x0"]
        )

        rows.append(current_row)

    return rows