from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """Stub documental - ver GUIA-IMPLEMENTACAO.md Fase 4 §Provedores: hoje e depois."""

    def grade_answer(self, payload):
        raise NotImplementedError(
            "Provedor 'openai' ainda não implementado — ver GUIA-IMPLEMENTACAO.md Fase 4."
        )
