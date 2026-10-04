import os
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    OpenAI,
    APIConnectionError,
    APIStatusError,
)


# ============================================================
# CUSTOM ERRORS
# ============================================================

class LLMClientError(Exception):
    """
    Base exception for controlled LLM client failures.
    """

    pass


class LLMServiceUnavailableError(
    LLMClientError
):
    """
    Raised when the upstream LLM service is temporarily
    unavailable, such as HTTP 5xx or connection failures.
    """

    pass


# ============================================================
# LOAD PROJECT ENVIRONMENT
# ============================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[3]

ENV_PATH = (
    PROJECT_ROOT
    / ".env"
)

load_dotenv(
    dotenv_path=ENV_PATH
)


# ============================================================
# CONFIGURATION
# ============================================================

def get_llm_config():

    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

    base_url = os.getenv(
        "LLM_BASE_URL"
    )

    model_name = os.getenv(
        "LLM_MODEL"
    )


    if not api_key:

        raise LLMClientError(
            "LLM API key not found. "
            "Check the project .env file."
        )


    if not base_url:

        raise LLMClientError(
            "LLM_BASE_URL not found. "
            "Check the project .env file."
        )


    if not model_name:

        raise LLMClientError(
            "LLM_MODEL not found. "
            "Check the project .env file."
        )


    return {
        "api_key": api_key,
        "base_url": base_url,
        "model_name": model_name,
    }


# ============================================================
# LLM CALL
# ============================================================

def call_llm(
    messages,
    max_tokens=200
):

    config = get_llm_config()


    client = OpenAI(
        api_key=config[
            "api_key"
        ],
        base_url=config[
            "base_url"
        ],
    )


    try:

        response = (
            client.chat.completions.create(
                model=config[
                    "model_name"
                ],
                messages=messages,
                max_tokens=max_tokens,
            )
        )


    except APIConnectionError as error:

        raise LLMServiceUnavailableError(
            "Could not connect to the LLM service."
        ) from error


    except APIStatusError as error:

        status_code = error.status_code


        if (
            status_code is not None
            and status_code >= 500
        ):

            raise LLMServiceUnavailableError(
                f"LLM service returned "
                f"HTTP {status_code}."
            ) from error


        raise LLMClientError(
            f"LLM request failed with "
            f"HTTP {status_code}."
        ) from error


    return (
        response
        .choices[0]
        .message
        .content
    )


# ============================================================
# DEVELOPMENT TEST
# ============================================================

if __name__ == "__main__":

    config = get_llm_config()


    print(
        "API key found:",
        bool(
            config["api_key"]
        )
    )

    print(
        "Base URL found:",
        bool(
            config["base_url"]
        )
    )

    print(
        "Model found:",
        bool(
            config["model_name"]
        )
    )


    test_messages = [
        {
            "role": "user",
            "content": (
                "Reply with exactly: "
                "API connection works."
            )
        }
    ]


    try:

        answer = call_llm(
            test_messages,
            max_tokens=20
        )

        print(
            "\nLLM response:"
        )

        print(
            answer
        )


    except LLMServiceUnavailableError as error:

        print(
            "\nLLM STATUS:"
        )

        print(
            "SERVICE_UNAVAILABLE"
        )

        print(
            "Reason:",
            str(error)
        )


    except LLMClientError as error:

        print(
            "\nLLM STATUS:"
        )

        print(
            "REQUEST_FAILED"
        )

        print(
            "Reason:",
            str(error)
        )