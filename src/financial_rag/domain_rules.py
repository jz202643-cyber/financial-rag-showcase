import re


# ============================================================
# METRIC NORMALISATION
# ============================================================

def metric_from_question(question):
    q = question.lower()

    patterns = [
        (
            [
                "cash, cash equivalents, and marketable securities",
                "cash and marketable securities",
            ],
            "Cash, cash equivalents, and marketable securities",
        ),

        (
            [
                "net cash provided by operating activities",
                "cash flow from operating activities",
                "operating cash flow",
            ],
            "Operating cash flow",
        ),

        (
            [
                "free cash flow",
            ],
            "Free cash flow",
        ),

        (
            [
                "total costs and expenses",
                "costs and expenses",
            ],
            "Costs and expenses",
        ),

        (
            [
                "income from operations",
                "operating income",
                "operating profit",
            ],
            "Income from operations",
        ),

        (
            [
                "operating margin",
                "margin did meta earn from operations",
                "margin from operations",
            ],
            "Operating margin",
        ),

        (
            [
                "capital expenditures",
                "capital expenditure",
                "capex",
            ],
            "Capital expenditures",
        ),

        (
            [
                "long-term debt",
                "long term debt",
            ],
            "Long-term debt",
        ),

        (
            [
                "total assets",
            ],
            "Total assets",
        ),

        (
            [
                "net income",
            ],
            "Net income",
        ),

        (
            [
                "revenue",
            ],
            "Revenue",
        ),
    ]

    for aliases, canonical in patterns:
        for alias in aliases:
            if alias in q:
                return canonical

    return None


# ============================================================
# ROUTING OVERRIDE
# ============================================================

def apply_domain_rules(
    question,
    parsed_query,
    current_route,
):
    """
    Small deterministic routing and normalisation layer for finance-domain queries.

    It does not replace the original parser.
    It only normalises common finance aliases and catches
    obvious unsupported / narrative query classes.
    """

    q = question.lower().strip()

    parsed_query = dict(parsed_query)


    # --------------------------------------------------------
    # 1. Unsupported / external-information questions
    # --------------------------------------------------------

    unsupported_patterns = [
        "stock price target",
        "current share price",
        "share price today",
        "stock price today",
        "dividend yield today",
        "should i buy",
        "should i sell",
        "should i invest",
        "how old is",
        "employees work in europe",
        "employees in europe",
    ]

    if any(
        pattern in q
        for pattern in unsupported_patterns
    ):
        return parsed_query, "unsupported"


    # --------------------------------------------------------
    # 2. Metric canonicalisation
    # --------------------------------------------------------

    metric = metric_from_question(
        question
    )

    if metric is not None:
        parsed_query["metric"] = metric


    # --------------------------------------------------------
    # 3. Unknown metric qualifier safety
    #
    # Prevent:
    # cloud operating margin
    # AWS revenue
    # banking revenue
    #
    # from collapsing into total-company metrics.
    # --------------------------------------------------------

    unsupported_qualifiers = [
        "cloud",
        "aws",
        "banking",
    ]

    if (
        metric is not None
        and any(
            qualifier in q
            for qualifier in unsupported_qualifiers
        )
    ):
        parsed_query[
            "qualifier_status"
        ] = "unresolved"


    # --------------------------------------------------------
    # 4. Narrative / guidance / explanation queries
    # --------------------------------------------------------

    narrative_signals = [
        "why ",
        "guidance",
        "outlook",
        "driving",
        "driver",
        "describe",
        "relationship between",
        "what did meta say",
        "what did meta expect",
        "expect for",
        "expected for",
        "anticipate",
    ]

    if any(
        signal in q
        for signal in narrative_signals
    ):
        return parsed_query, "narrative"


    # --------------------------------------------------------
    # 5. Known structured metric
    # --------------------------------------------------------

    if metric is not None:
        return parsed_query, "structured"


    return parsed_query, current_route


# ============================================================
# STRUCTURED FALLBACK RETRIEVAL
# ============================================================

def _normalise_metric(metric):
    if not metric:
        return ""

    m = metric.lower()
    m = re.sub(r"[^a-z0-9]+", " ", m)
    m = " ".join(m.split())

    aliases = {
        "total revenue": "revenue",

        "total costs and expenses":
            "costs and expenses",

        "operating profit":
            "income from operations",

        "operating income":
            "income from operations",

        "net cash provided by operating activities":
            "operating cash flow",

        "cash flow from operating activities":
            "operating cash flow",

        "cash cash equivalents and marketable securities":
            "cash cash equivalents and marketable securities",

        "capital expenditure":
            "capital expenditures",
    }

    return aliases.get(m, m)


def _extract_year(question):
    match = re.search(
        r"\b(20\d{2})\b",
        question,
    )

    if match:
        return int(
            match.group(1)
        )

    return None


def fallback_structured_fact(
    facts,
    question,
    parsed_query,
):
    """
    More tolerant fact lookup used only when exact
    entity + metric + period retrieval fails.

    Still requires:
        - canonical metric match
        - requested year match
        - quarterly compatibility when Q2 is requested
    """

    if (
        parsed_query.get(
            "qualifier_status"
        )
        == "unresolved"
    ):
        return None


    query_metric = (
        metric_from_question(
            question
        )
        or parsed_query.get(
            "metric"
        )
    )

    if not query_metric:
        return None


    target_metric = (
        _normalise_metric(
            query_metric
        )
    )

    target_year = (
        _extract_year(
            question
        )
    )

    q = question.lower()

    wants_q2 = (
        "q2" in q
        or "second quarter" in q
    )


    candidates = []


    for fact in facts:

        fact_metric = (
            _normalise_metric(
                fact.get(
                    "metric"
                )
            )
        )

        if fact_metric != target_metric:
            continue


        fact_year = fact.get(
            "year"
        )

        try:
            if fact_year is not None:
                fact_year = int(
                    fact_year
                )
        except Exception:
            pass


        if (
            target_year is not None
            and fact_year != target_year
        ):
            continue


        if wants_q2:

            duration = str(
                fact.get(
                    "duration",
                    ""
                )
            ).lower()

            period = str(
                fact.get(
                    "period",
                    ""
                )
            ).lower()


            stock_metrics = {
                "cash cash equivalents and marketable securities",
                "long term debt",
                "total assets",
            }


            if (
                target_metric
                not in stock_metrics
                and duration
                not in {
                    "three",
                    "three months",
                }
                and "three months" not in period
                and "q2" not in period
            ):
                continue


        candidates.append(
            fact
        )


    if not candidates:
        return None


    def rank(fact):

        page = fact.get(
            "page"
        )

        try:
            page = int(page)
        except Exception:
            page = 999


        curated = (
            0
            if fact.get(
                "verified_fact"
            )
            else 1
        )


        return (
            curated,
            page,
        )


    candidates.sort(
        key=rank
    )

    return candidates[0]
