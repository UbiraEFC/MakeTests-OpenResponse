from dataclasses import dataclass, field

# Thresholds e pesos nomeados — calibração heurística, validada com respostas
# manuscritas reais (ver docs/ADR-001 §8.4). Mantidos aqui em vez de
# espalhados para facilitar ajuste.
SCORE_ALTA_MIN = 70
SCORE_MEDIA_MIN = 40

PENALTY_LLM_REVIEW_RECOMMENDED = 25
PENALTY_RUBRIC_COVERAGE_MAX = 20
PENALTY_USED_FALLBACK = 10
PENALTY_STABILITY_MAX = 20


@dataclass
class ConfidenceSignals:
    """Sinais de entrada para o score de confiança.

    `score_stability_std` é um hook reservado: nenhum código hoje dispara as
    múltiplas chamadas ao LLM necessárias para calculá-lo.
    """

    llm_review_recommended: bool = True
    llm_error: str = None
    rubric_coverage: dict = field(default_factory=dict)
    used_fallback: bool = False
    score_stability_std: float = None


@dataclass
class ConfidenceResult:
    score: int
    level: str
    review_recommended: bool
    reasons: list = field(default_factory=list)


def _level_for(score):
    if score >= SCORE_ALTA_MIN:
        return "alta"
    if score >= SCORE_MEDIA_MIN:
        return "media"
    return "baixa"


def compute(signals: ConfidenceSignals) -> ConfidenceResult:
    """Score 0-100 + nível + decisão de encaminhamento à revisão humana.

    A confiança mede o quanto a avaliação automática é confiável, não a
    qualidade da resposta do aluno. Por isso a cobertura de rubrica baixa
    (resposta incompleta) pesa pouco e, sozinha, não cruza o limiar de
    revisão: quem sinaliza problema de leitura é o próprio avaliador
    (review_recommended), além de erros e fallback.
    """
    if signals.llm_error:
        return ConfidenceResult(
            score=0,
            level="baixa",
            review_recommended=True,
            reasons=["avaliacao_llm_falhou"],
        )

    score = 100
    reasons = []

    if signals.llm_review_recommended:
        score -= PENALTY_LLM_REVIEW_RECOMMENDED
        reasons.append("llm_recomendou_revisao")

    if signals.rubric_coverage:
        covered = sum(1 for v in signals.rubric_coverage.values() if v)
        coverage_ratio = covered / len(signals.rubric_coverage)
        coverage_penalty = (1 - coverage_ratio) * PENALTY_RUBRIC_COVERAGE_MAX
        if coverage_penalty > 0:
            score -= coverage_penalty
            reasons.append("cobertura_de_rubrica_baixa")

    if signals.used_fallback:
        score -= PENALTY_USED_FALLBACK
        reasons.append("resposta_via_fallback")

    if signals.score_stability_std is not None:
        stability_penalty = min(signals.score_stability_std * 100, PENALTY_STABILITY_MAX)
        if stability_penalty > 0:
            score -= stability_penalty
            reasons.append("instabilidade_entre_execucoes")

    score = max(0, min(100, int(round(score))))
    review_recommended = score < SCORE_ALTA_MIN or signals.llm_review_recommended

    return ConfidenceResult(
        score=score,
        level=_level_for(score),
        review_recommended=review_recommended,
        reasons=reasons,
    )
