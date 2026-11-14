from .base import LLMProvider
from .schemas import GradingResult


class MockProvider(LLMProvider):
    """Provider determinístico e offline (sem rede, sem API key) — default
    quando LLM_PROVIDER não está configurado, e o usado pela suíte de testes.

    Não lê a imagem: devolve sempre um resultado conservador e honesto sobre
    essa limitação (nunca finge uma transcrição), o suficiente para exercitar
    o contrato e o pipeline completo sem custo/rede.
    """

    def grade_answer(self, payload):
        return GradingResult(
            suggested_score=0,
            rationale="[mock] avaliação indisponível em modo offline.",
            rubric_coverage={},
            review_recommended=True,
            provider_metadata={"provider": "mock", "model": "offline"},
            transcription="[mock] transcrição indisponível em modo offline",
        )
