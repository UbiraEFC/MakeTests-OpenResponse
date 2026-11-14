import os

PROMPT_VERSION = "somativo_v2_vision"

_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")


def _template_path(version):
    return os.path.join(_PROMPTS_DIR, version + ".txt")


def resolve_prompt_version(payload):
    """Versão do prompt usada para este payload: override explícito em
    run_params["prompt_version"] ou o default. Separado de build_prompt
    para que os providers possam registrar a versão em provider_metadata.
    """
    run_params = payload.run_params or {}
    return run_params.get("prompt_version") or PROMPT_VERSION


def build_prompt(payload):
    """payload: GradingPayload -> str (prompt versionado, ver prompts/)."""
    with open(_template_path(resolve_prompt_version(payload)), encoding="utf-8") as f:
        template = f.read()

    expected_topics_block = ""
    if payload.expected_topics:
        expected_topics_block = "\nTópicos esperados:\n{}\n".format(payload.expected_topics)

    return template.format(
        statement=payload.statement or "",
        rubric=payload.rubric or "",
        expected_topics_block=expected_topics_block,
    )
