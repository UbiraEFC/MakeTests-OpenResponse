import re

from .base import LLMProvider
from .schemas import GradingResult


def _words(text):
    return set(re.findall(r"\w+", (text or "").lower()))


class MockProvider(LLMProvider):
    """Provider determinístico e offline (sem rede, sem API key).

    Heurística deliberadamente simples (sobreposição de palavras entre o
    texto do aluno e a rubrica/tópicos esperados) - não é um grader de
    verdade, é só o suficiente para os testes automatizados (T4.1, T4.4,
    T4.5) exercitarem o contrato sem precisar de credencial. É o default
    quando LLM_PROVIDER não está configurado.
    """

    def grade_answer(self, payload):
        student_words = _words(payload.normalized_text)

        if not student_words:
            return GradingResult(
                suggested_score=0,
                rationale="Resposta vazia ou ilegível.",
                rubric_coverage={},
                review_recommended=True,
                provider_metadata={"provider": "mock", "model": "keyword-overlap-v1"},
            )

        reference = _words(payload.rubric) | _words(payload.expected_topics)
        reference = {w for w in reference if len(w) > 3}  # ignora stopwords curtas
        if not reference:
            overlap_ratio = 0.0
        else:
            overlap_ratio = len(student_words & reference) / len(reference)

        score = round(min(1.0, overlap_ratio) * 100)
        return GradingResult(
            suggested_score=score,
            rationale="[mock] sobreposição de palavras-chave com a rubrica: {:.0%}.".format(overlap_ratio),
            rubric_coverage={},
            review_recommended=score < 60,
            provider_metadata={"provider": "mock", "model": "keyword-overlap-v1"},
        )
