from .schemas import GradingResult


def validate(raw, provider_metadata=None):
    """Valida/normaliza a resposta crua de QUALQUER provedor (nativo ou
    fallback) contra o contrato GradingResult. Nunca confia que o provedor
    "prometeu" JSON valido - aplica os defaults conservadores aqui.

    raw: dict (ja parseado de JSON, vindo de structured output nativo ou de
         um parsing manual no adapter).
    """
    if not isinstance(raw, dict):
        return GradingResult(
            suggested_score=0,
            rationale="Resposta do provedor não era um objeto JSON.",
            rubric_coverage={},
            review_recommended=True,
            provider_metadata=provider_metadata or {},
            error="invalid_response_type",
        )

    try:
        score = int(raw.get("suggested_score", 0))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))

    rationale = raw.get("rationale")
    if not isinstance(rationale, str):
        rationale = ""

    rubric_coverage = raw.get("rubric_coverage")
    if not isinstance(rubric_coverage, dict):
        rubric_coverage = {}

    review_recommended = raw.get("review_recommended")
    if not isinstance(review_recommended, bool):
        # Sem sinal confiável do provedor: lado conservador é recomendar revisão.
        review_recommended = True

    return GradingResult(
        suggested_score=score,
        rationale=rationale,
        rubric_coverage=rubric_coverage,
        review_recommended=review_recommended,
        provider_metadata=provider_metadata or {},
        error=None,
    )
