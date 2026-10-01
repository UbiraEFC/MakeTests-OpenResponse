from .base import LLMProvider


class MaritacaProvider(LLMProvider):
    """Stub documental - ver GUIA-IMPLEMENTACAO.md Fase 4 §Provedores: hoje e depois.

    Testado manualmente nesta sessão: a chave fornecida autentica, mas a
    conta está sem crédito ativo (insufficient_funds em todos os modelos,
    incl. sabiazinho). Reavaliar implementação se/quando houver crédito.
    """

    def grade_answer(self, payload):
        raise NotImplementedError(
            "Provedor 'maritaca' ainda não implementado — ver GUIA-IMPLEMENTACAO.md Fase 4."
        )
