from dataclasses import dataclass, field

# Thresholds e pesos nomeados (Fase 5) — calibração inicial heurística, a
# recalibrar com dados reais na Fase 8. Mantidos aqui em vez de espalhados
# para facilitar ajuste.
SCORE_ALTA_MIN = 70
SCORE_MEDIA_MIN = 40

PENALTY_OCR_CONFIDENCE_UNKNOWN = 25
PENALTY_OCR_CONFIDENCE_MAX = 30
PENALTY_OCR_DOUBT_MAX = 20
PENALTY_LLM_REVIEW_RECOMMENDED = 25
PENALTY_RUBRIC_COVERAGE_MAX = 20
PENALTY_USED_FALLBACK = 10
PENALTY_STABILITY_MAX = 20


@dataclass
class ConfidenceSignals:
    """Sinais de entrada para o score de confiança (Fase 5).

    Cada campo tem uma fonte real já existente no pipeline (Fase 2/4) — ver
    GUIA-IMPLEMENTACAO.md Fase 5. `score_stability_std` é um hook reservado:
    nenhum código hoje dispara as múltiplas chamadas LLM necessárias para
    calculá-lo (custo de quota desproporcional ao Q2).
    """

    ocr_confidence_mean: float = None
    ocr_char_doubt_ratio: float = 0.0
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
    if signals.llm_error:
        return ConfidenceResult(
            score=0,
            level="baixa",
            review_recommended=True,
            reasons=["avaliacao_llm_falhou"],
        )

    score = 100
    reasons = []

    if signals.ocr_confidence_mean is None:
        score -= PENALTY_OCR_CONFIDENCE_UNKNOWN
        reasons.append("ocr_sem_sinal_de_confianca")
    else:
        penalty = (1 - signals.ocr_confidence_mean) * PENALTY_OCR_CONFIDENCE_MAX
        if penalty > 0:
            score -= penalty
            reasons.append("ocr_confianca_baixa")

    doubt_penalty = signals.ocr_char_doubt_ratio * PENALTY_OCR_DOUBT_MAX
    if doubt_penalty > 0:
        score -= doubt_penalty
        reasons.append("ocr_caracteres_duvidosos")

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
