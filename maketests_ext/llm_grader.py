from maketests_ext.llm.provider_factory import get_provider
from maketests_ext.llm.schemas import GradingResult


def grade(payload):
    """Fachada/orquestrador da Fase 4 - único ponto que o resto do MakeTests
    chama. Escolhe o adapter ativo via provider_factory; qualquer exceção
    que escape do adapter é capturada aqui como rede de segurança final
    (nunca propaga para QuestionDissertative.doCorrection).
    """
    try:
        provider = get_provider()
        return provider.grade_answer(payload)
    except Exception as e:
        return GradingResult(
            suggested_score=0,
            rationale="",
            rubric_coverage={},
            review_recommended=True,
            provider_metadata={},
            error="llm_grader_failure: {}".format(e),
        )
