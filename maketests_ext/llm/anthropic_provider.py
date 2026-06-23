from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Stub documental - ver GUIA-IMPLEMENTACAO.md Fase 4 §Provedores: hoje e depois."""

    def grade_answer(self, payload):
        raise NotImplementedError(
            "Provedor 'anthropic' ainda não implementado — ver GUIA-IMPLEMENTACAO.md Fase 4."
        )
