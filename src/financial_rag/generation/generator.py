from .llm_client import (
    call_llm,
    LLMClientError,
    LLMServiceUnavailableError,
)


# ============================================================
# EVIDENCE FORMATTER
# ============================================================

def format_selected_evidence(
    selected_evidence
):
    """
    Convert selected narrative evidence into a compact,
    provenance-aware text block for the LLM.

    selected_evidence items are expected to contain:

        {
            "rank": ...,
            "candidate": {
                "text": ...,
                "page": ...,
                "source": ...,
                "chunk_id": ...
            },
            ...
        }
    """

    evidence_blocks = []


    for index, item in enumerate(
        selected_evidence,
        start=1
    ):

        candidate = item[
            "candidate"
        ]


        page = candidate.get(
            "page",
            "unknown"
        )

        source = candidate.get(
            "source",
            "unknown"
        )

        chunk_id = candidate.get(
            "chunk_id",
            "unknown"
        )

        text = candidate.get(
            "text",
            ""
        )


        block = (
            f"[Evidence {index}]\n"
            f"Page: {page}\n"
            f"Chunk ID: {chunk_id}\n"
            f"Source: {source}\n"
            f"Text:\n{text}"
        )


        evidence_blocks.append(
            block
        )


    return "\n\n".join(
        evidence_blocks
    )


# ============================================================
# GROUNDED NARRATIVE GENERATION
# ============================================================

def generate_narrative_answer(
    question,
    answerability_status,
    selected_evidence
):
    """
    Generate a narrative answer only when the upstream
    Evidence Composition layer has determined that the
    evidence is ANSWERABLE.

    The LLM does NOT decide whether evidence is sufficient.
    That decision has already been made upstream.
    """


    # --------------------------------------------------------
    # 1. Reject before calling the LLM
    # --------------------------------------------------------

    if (
        answerability_status
        != "ANSWERABLE"
    ):

        return {
            "status": answerability_status,
            "llm_called": False,
            "answer": (
                "I cannot answer this question reliably "
                "from the available evidence."
            ),
        }


    # --------------------------------------------------------
    # 2. Safety check
    # --------------------------------------------------------

    if not selected_evidence:

        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "llm_called": False,
            "answer": (
                "I cannot answer this question reliably "
                "because no validated evidence was selected."
            ),
        }


    # --------------------------------------------------------
    # 3. Format validated evidence
    # --------------------------------------------------------

    evidence_text = format_selected_evidence(
        selected_evidence
    )


    # --------------------------------------------------------
    # 4. Grounded generation prompt
    # --------------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial research assistant. "
                "Answer using ONLY the supplied evidence. "

                "Do not use outside knowledge. "
                "Do not invent financial facts, causes, "
                "numbers, dates, or explanations. "

                "You may make simple comparative or arithmetic "
                "inferences when they follow directly from the "
                "supplied evidence. "

                "When making such an inference, make clear that "
                "it is an inference from the reported figures, "
                "rather than an explicit statement by the company. "

                "If the supplied evidence cannot support a claim, "
                "do not make that claim. "

                "Cite the supporting evidence using labels such as "
                "[Evidence 1] or [Evidence 2]."
            )
        },

        {
            "role": "user",
            "content": (
                f"Question:\n"
                f"{question}\n\n"

                f"Validated evidence:\n"
                f"{evidence_text}\n\n"

                "Answer the question directly and concisely. "
                "Use only the validated evidence above."
            )
        }
    ]


    # --------------------------------------------------------
    # 5. Call LLM
    # --------------------------------------------------------

from .llm_client import (
    call_llm,
    LLMClientError,
    LLMServiceUnavailableError,
)


# ============================================================
# EVIDENCE FORMATTER
# ============================================================

def format_selected_evidence(
    selected_evidence
):
    """
    Convert selected narrative evidence into a compact,
    provenance-aware text block for the LLM.
    """

    evidence_blocks = []


    for index, item in enumerate(
        selected_evidence,
        start=1
    ):

        candidate = item[
            "candidate"
        ]


        page = candidate.get(
            "page",
            "unknown"
        )

        source = candidate.get(
            "source",
            "unknown"
        )

        chunk_id = candidate.get(
            "chunk_id",
            "unknown"
        )

        text = candidate.get(
            "text",
            ""
        )


        block = (
            f"[Evidence {index}]\n"
            f"Page: {page}\n"
            f"Chunk ID: {chunk_id}\n"
            f"Source: {source}\n"
            f"Text:\n{text}"
        )


        evidence_blocks.append(
            block
        )


    return "\n\n".join(
        evidence_blocks
    )


# ============================================================
# GROUNDED NARRATIVE GENERATION
# ============================================================

def generate_narrative_answer(
    question,
    answerability_status,
    selected_evidence
):
    """
    Generate an answer only when the upstream
    Evidence Composition layer says the question
    is ANSWERABLE.

    The LLM is responsible only for generating
    the final grounded response.

    It does NOT decide whether the evidence is valid
    or sufficient.
    """


    # ========================================================
    # 1. ANSWERABILITY CHECK
    # ========================================================

    if (
        answerability_status
        != "ANSWERABLE"
    ):

        return {
            "status": answerability_status,
            "llm_called": False,
            "answer": (
                "I cannot answer this question reliably "
                "from the available evidence."
            ),
            "evidence_count": len(
                selected_evidence
            ),
        }


    # ========================================================
    # 2. EMPTY EVIDENCE SAFETY CHECK
    # ========================================================

    if not selected_evidence:

        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "llm_called": False,
            "answer": (
                "I cannot answer this question reliably "
                "because no validated evidence was selected."
            ),
            "evidence_count": 0,
        }


    # ========================================================
    # 3. FORMAT VALIDATED EVIDENCE
    # ========================================================

    evidence_text = format_selected_evidence(
        selected_evidence
    )


    # ========================================================
    # 4. BUILD GROUNDED PROMPT
    # ========================================================

    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial research assistant. "
                "Answer using ONLY the supplied evidence. "

                "Do not use outside knowledge. "
                "Do not invent financial facts, causes, "
                "numbers, dates, or explanations. "

                "You may make simple comparative or arithmetic "
                "inferences when they follow directly from the "
                "supplied evidence. "

                "When making such an inference, clearly state "
                "that it is an inference from the reported figures "
                "rather than an explicit statement by the company. "

                "If the supplied evidence cannot support a claim, "
                "do not make that claim. "

                "Cite supporting evidence using labels such as "
                "[Evidence 1] or [Evidence 2]."
            )
        },

        {
            "role": "user",
            "content": (
                f"Question:\n"
                f"{question}\n\n"

                f"Validated evidence:\n"
                f"{evidence_text}\n\n"

                "Answer the question directly and concisely. "
                "Use only the validated evidence above."
            )
        }
    ]


    # ========================================================
    # 5. CALL LLM
    # ========================================================

    try:

        answer = call_llm(
            messages,
            max_tokens=220
        )


    # --------------------------------------------------------
    # Upstream provider unavailable
    # e.g. HTTP 503 / connection failure
    # --------------------------------------------------------

    except LLMServiceUnavailableError as error:

        return {
            "status": "LLM_SERVICE_UNAVAILABLE",
            "llm_called": True,
            "answer": None,
            "error": str(
                error
            ),
            "evidence_count": len(
                selected_evidence
            ),
        }


    # --------------------------------------------------------
    # Other controlled LLM request errors
    # --------------------------------------------------------

    except LLMClientError as error:

        return {
            "status": "LLM_REQUEST_FAILED",
            "llm_called": True,
            "answer": None,
            "error": str(
                error
            ),
            "evidence_count": len(
                selected_evidence
            ),
        }


    # ========================================================
    # 6. SUCCESSFUL GROUNDED ANSWER
    # ========================================================

    return {
        "status": "SUPPORTED",
        "llm_called": True,
        "answer": answer,
        "evidence_count": len(
            selected_evidence
        ),
    }


# ============================================================
# DEVELOPMENT TEST
# ============================================================

if __name__ == "__main__":

    print(
        "generator.py loaded successfully."
    )