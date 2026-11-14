class LLMProvider:
    """Contrato estavel que todo adapter de provedor de LLM implementa.

    Nenhum codigo fora de maketests_ext/llm/ deve conhecer o SDK ou o
    formato de request/response de um provedor especifico - so este
    metodo.
    """

    def grade_answer(self, payload):
        """payload: GradingPayload -> GradingResult"""
        raise NotImplementedError
