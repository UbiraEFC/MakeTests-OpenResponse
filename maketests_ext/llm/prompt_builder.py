import os

PROMPT_VERSION = "somativo_v1"
_TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "prompts",
    PROMPT_VERSION + ".txt",
)


def build_prompt(payload):
    """payload: GradingPayload -> str (prompt versionado, ver prompts/)."""
    with open(_TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    expected_topics_block = ""
    if payload.expected_topics:
        expected_topics_block = "\nTópicos esperados:\n{}\n".format(payload.expected_topics)

    return template.format(
        statement=payload.statement or "",
        rubric=payload.rubric or "",
        expected_topics_block=expected_topics_block,
        normalized_text=payload.normalized_text or "",
    )
