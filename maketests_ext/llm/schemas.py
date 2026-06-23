from dataclasses import dataclass, field


@dataclass
class GradingPayload:
    """Entrada do contrato de avaliacao semantica (Fase 4).

    expected_topics/context_metadata/run_params sao opcionais: os exemplos
    atuais de QuestionDissertative descrevem os topicos esperados dentro do
    proprio texto de `rubric`, sem precisar de um campo separado.
    """

    statement: str
    rubric: str
    normalized_text: str
    expected_topics: str = None
    context_metadata: dict = None
    run_params: dict = None


@dataclass
class GradingResult:
    """Saida padronizada de qualquer provedor (Fase 4).

    `error` fica None em uma avaliacao bem-sucedida. Quando preenchido, os
    demais campos devem estar em um estado conservador (score baixo,
    review_recommended=True) - nunca representam uma nota real.
    """

    suggested_score: int
    rationale: str
    rubric_coverage: dict = field(default_factory=dict)
    review_recommended: bool = True
    provider_metadata: dict = field(default_factory=dict)
    error: str = None
