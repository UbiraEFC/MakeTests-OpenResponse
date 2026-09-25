import os

_dotenv_loaded = False


def ensure_dotenv_loaded():
    """Carrega .env uma única vez (idempotente). Pública desde o roadmap Q3
    Fase 1 (ADR-001): MakeTests.py precisa ler LLM_VISION_MODE do .env
    *antes* de montar o payload/chamar get_provider(), então não pode mais
    depender só do carregamento implícito feito dentro de get_provider().
    """
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    _dotenv_loaded = True


def get_provider(name=None):
    """Lê LLM_PROVIDER (default 'mock' — não exige credencial) e devolve a
    instância do adapter correspondente. Trocar de provedor é trocar essa
    variável de ambiente, nunca código-cliente.
    """
    ensure_dotenv_loaded()
    name = (name or os.environ.get("LLM_PROVIDER") or "mock").strip().lower()

    if name == "mock":
        from .mock_provider import MockProvider
        return MockProvider()
    if name == "gemini":
        from .gemini_provider import GeminiProvider
        return GeminiProvider()
    if name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()
    if name == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    if name == "maritaca":
        from .maritaca_provider import MaritacaProvider
        return MaritacaProvider()

    raise ValueError(
        "LLM_PROVIDER desconhecido: '{}'. Opções: mock, gemini, openai, anthropic, maritaca.".format(name)
    )
