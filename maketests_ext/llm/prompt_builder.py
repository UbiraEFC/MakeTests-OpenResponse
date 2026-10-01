import os

# PROMPT_VERSION segue publico por compatibilidade (gemini_provider.py e
# outros modulos podem importa-lo como "a versao de texto default"), mas a
# escolha de qual versao usar numa chamada especifica e responsabilidade de
# resolve_prompt_version(payload), nao mais uma constante fixa resolvida no
# import do modulo - isso e o que permite as duas versoes (texto/vision)
# coexistirem (ADR-001, roadmap Q3 Fase 1).
PROMPT_VERSION = "somativo_v1"
VISION_PROMPT_VERSION = "somativo_v2_vision"

_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")


def _template_path(version):
    return os.path.join(_PROMPTS_DIR, version + ".txt")


def resolve_prompt_version(payload):
    """Decide qual prompt versionado usar para este payload.

    Prioridade: override explicito em run_params > vision se ha imagem >
    default de texto. Mantido separado de build_prompt para que o caller
    (ex.: gemini_provider.py) possa carimbar a versao escolhida em
    provider_metadata sem reabrir o arquivo de template.
    """
    run_params = payload.run_params or {}
    explicit = run_params.get("prompt_version")
    if explicit:
        return explicit
    if payload.image_bytes:
        return VISION_PROMPT_VERSION
    return PROMPT_VERSION


def build_prompt(payload):
    """payload: GradingPayload -> str (prompt versionado, ver prompts/)."""
    version = resolve_prompt_version(payload)
    with open(_template_path(version), encoding="utf-8") as f:
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
