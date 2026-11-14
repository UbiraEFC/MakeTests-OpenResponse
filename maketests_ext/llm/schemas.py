from dataclasses import dataclass, field


@dataclass
class GradingPayload:
    """Entrada do contrato de avaliação: enunciado, rubrica e a imagem do
    recorte da área de resposta (ver docs/ADR-001).

    expected_topics/context_metadata/run_params são opcionais: os exemplos
    de QuestionDissertative descrevem os tópicos esperados dentro do próprio
    texto de `rubric`, sem precisar de um campo separado.
    """

    statement: str
    rubric: str
    image_bytes: bytes = None
    image_mime_type: str = "image/jpeg"
    expected_topics: str = None
    context_metadata: dict = None
    run_params: dict = None


@dataclass
class GradingResult:
    """Saída padronizada de qualquer provedor.

    `error` fica None em uma avaliação bem-sucedida. Quando preenchido, os
    demais campos devem estar em um estado conservador (score baixo,
    review_recommended=True) - nunca representam uma nota real.
    """

    suggested_score: int
    rationale: str
    rubric_coverage: dict = field(default_factory=dict)
    review_recommended: bool = True
    provider_metadata: dict = field(default_factory=dict)
    error: str = None
    transcription: str = None
