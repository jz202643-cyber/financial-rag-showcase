import sys

sys.path.append("src")

from financial_rag.main import answer_question


TEST_CASES = [

    ("STRUCTURED",
     "What was Meta's revenue in Q2 2026?"),

    ("STRUCTURED",
     "What was Meta's operating income in Q2 2026?"),

    ("STRUCTURED",
     "What was Meta's operating margin in Q2 2026?"),

    ("STRUCTURED",
     "What was Meta's capital expenditure in Q2 2026?"),

    ("ABSTENTION",
     "What was Meta's cloud revenue in Q2 2026?"),

    ("ABSTENTION",
     "What is Meta's stock price target?"),

]


def format_answer(answer):

    if not isinstance(answer, dict):
        return str(answer)


    metric = answer.get("metric")

    value = answer.get("value")

    unit = answer.get("unit")


    if unit == "USD millions":
        value = (
            f"${value/1000:.3f} billion"
        )

    elif unit == "percent":
        value = (
            f"{value}%"
        )


    return f"""
{metric}: {value}

Period:
{answer.get('period')}

Evidence:
Source: {answer.get('source')}
Page: {answer.get('page')}
"""


def main():

    for category, question in TEST_CASES:

        print("="*70)

        print(category)

        print()

        print("QUESTION:")
        print(question)


        result = answer_question(question)


        print()

        print("STATUS:")
        print(result.get("status"))

        print()

        print("ROUTE:")
        print(result.get("route"))

        print()

        print("ANSWER:")


        answer = (
            result.get("answer")
            or
            result.get("evidence")
        )


        print(
            format_answer(answer)
        )


if __name__ == "__main__":
    main()