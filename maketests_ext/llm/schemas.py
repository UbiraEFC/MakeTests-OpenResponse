from dataclasses import dataclass, field


@dataclass
class GradingPayload:
    """Entrada do contrato de avaliacao semantica (Fase 4; imagem desde o
    roadmap Q3 Fase 1 - ADR-001).

    expected_topics/context_metadata/run_params sao opcionais: os exemplos
    atuais de QuestionDissertative descrevem os topicos esperados dentro do
    proprio texto de `rubric`, sem precisar de um campo separado.

    normalized_text e image_bytes sao mutuamente alternativos, nao ambos
    obrigatorios: caminho legado (OCR+texto) preenche normalized_text;
    caminho vision (ADR-001) preenche image_bytes/image_mime_type. Qual
    provider/prompt usar e decidido pela presenca de image_bytes, nao por
    um provider diferente (ver gemini_provider.py).
    """

    statement: str
    rubric: str
    normalized_text: str = None
    expected_topics: str = None
    context_metadata: dict = None
    run_params: dict = None
    image_bytes: bytes = None
    image_mime_type: str = "image/jpeg"


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
    transcription: str = None
