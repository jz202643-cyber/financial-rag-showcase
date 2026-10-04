import re


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    """
    Normalize PDF-extracted text for deterministic
    explicit financial fact extraction.
    """

    if text is None:
        return ""

    text = str(text)

    # Normalize common dash variants.
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    # Collapse whitespace produced by PDF extraction.
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# VALUE NORMALIZATION
# ============================================================

def convert_to_usd_millions(
    value,
    scale
):
    """
    Convert financial values into USD millions.

    Examples:

        31.08 billion
            -> 31080

        784 million
            -> 784
    """

    numeric_value = float(
        value
    )

    scale = scale.lower()


    if scale == "billion":

        numeric_value = (
            numeric_value
            * 1000
        )


    elif scale == "million":

        numeric_value = (
            numeric_value
        )


    else:

        return None


    # Preserve integer representation
    # when possible.
    if numeric_value.is_integer():

        return int(
            numeric_value
        )


    return numeric_value


# ============================================================
# DURATION HELPERS
# ============================================================

def infer_duration(period):
    """
    Infer the duration label used by the current
    structured financial fact schema.
    """

    if period is None:
        return None


    text = period.lower()


    if "three months ended" in text:
        return "three"


    if "six months ended" in text:
        return "six"


    if "nine months ended" in text:
        return "nine"


    if "twelve months ended" in text:
        return "twelve"


    return None


# ============================================================
# CAPITAL EXPENDITURE EXTRACTION
# ============================================================

def extract_capex_actual_fact(
    text,
    reporting_period,
    end_date,
    year
):
    """
    Extract an explicitly disclosed ACTUAL
    capital expenditure fact.

    Example source text:

        Capital expenditures - Capital expenditures,
        including principal payments on finance leases,
        were $31.08 billion.

    Important:

    This extractor only accepts actual-result language
    such as "was" or "were".

    Guidance language such as:
        expect
        anticipate
        guidance
        outlook

    is intentionally excluded.
    """

    normalized_text = normalize_text(
        text
    )


    # --------------------------------------------------------
    # Find a local Capital Expenditures disclosure.
    #
    # Limit the search window so that unrelated numbers
    # elsewhere on the page are not captured.
    # --------------------------------------------------------

    capex_pattern = re.compile(
        r"""
        capital\s+expenditures?
        .{0,220}?
        \b(?:was|were)\b
        \s*
        \$\s*
        (?P<value>\d+(?:\.\d+)?)
        \s*
        (?P<scale>billion|million)
        """,
        re.IGNORECASE
        | re.VERBOSE
    )


    match = capex_pattern.search(
        normalized_text
    )


    if not match:

        return None


    # --------------------------------------------------------
    # Additional safety check:
    #
    # Inspect the local disclosure and reject it if it
    # contains forward-looking guidance language.
    # --------------------------------------------------------

    start = max(
        0,
        match.start() - 80
    )

    end = min(
        len(normalized_text),
        match.end() + 80
    )


    local_context = (
        normalized_text[
            start:end
        ].lower()
    )


    guidance_markers = [
        "expect",
        "expected",
        "anticipate",
        "anticipated",
        "guidance",
        "outlook",
        "forecast",
    ]


    for marker in guidance_markers:

        if marker in local_context:

            return None


    # --------------------------------------------------------
    # Convert value to the common storage unit.
    # --------------------------------------------------------

    value = convert_to_usd_millions(
        match.group("value"),
        match.group("scale")
    )


    if value is None:

        return None


    # --------------------------------------------------------
    # Build fact using the SAME core schema as the
    # existing duration-table facts.
    # --------------------------------------------------------

    fact = {

        "metric": (
            "Capital expenditures"
        ),

        "period": (
            reporting_period
        ),

        "duration": infer_duration(
            reporting_period
        ),

        "end_date": (
            end_date
        ),

        "year": (
            year
        ),

        "value": (
            value
        ),

        "unit": (
            "USD millions"
        ),

        "section": (
            "financial_highlights"
        ),
    }


    return fact


# ============================================================
# EXPLICIT FACT EXTRACTION ENTRY POINT
# ============================================================

def extract_explicit_actual_facts(
    text,
    reporting_period,
    end_date,
    year
):
    """
    Extract supported explicit actual financial facts
    from narrative / financial-highlight text.

    V0.1 currently supports:

        Capital expenditures

    More metric extractors can later be added here
    without changing the downstream structured
    retrieval interface.
    """

    facts = []


    capex_fact = (
        extract_capex_actual_fact(
            text=text,
            reporting_period=reporting_period,
            end_date=end_date,
            year=year
        )
    )


    if capex_fact is not None:

        facts.append(
            capex_fact
        )


    return facts