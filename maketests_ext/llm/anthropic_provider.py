import base64
import json
import os
import re
import urllib.error
import urllib.request

from .base import LLMProvider
from .prompt_builder import build_prompt, resolve_prompt_version
from .response_validator import validate
from .schemas import GradingResult

DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_TOKENS = 2048
API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"

_JSON_BLOB_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_json_response(text):
    """Extrai o objeto JSON da resposta em texto. Ao contrario do Gemini, a
    Messages API da Anthropic nao tem um modo equivalente ao responseSchema
    nativo para este caso: structured outputs (output_config.format) exige
    additionalProperties=false em todo objeto do schema, incompativel com
    rubric_coverage (chaves dinamicas, uma por criterio da rubrica) - por
    isso o JSON e pedido via prompt (ja e o que somativo_v1/v2_vision fazem)
    e parseado defensivamente aqui, tolerando texto acessorio ao redor.
    """
    try:
        return json.loads(text)
    except ValueError:
        pass
    match = _JSON_BLOB_RE.search(text)
    if match:
        try:
            return json.loads(match.group(0))
        except ValueError:
            return None
    return None


class AnthropicProvider(LLMProvider):
    """Adapter (roadmap Q3 Fase 1/3 - ADR-001) - chama a Messages API da
    Anthropic via urllib (stdlib, sem SDK), no mesmo padrao de
    gemini_provider.py. Suporta o caminho vision (payload.image_bytes) e o
    caminho texto legado (payload.normalized_text) via GradingPayload.
    """

    def __init__(self, api_key=None, model=None, timeout=None, max_tokens=None):
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.model = model or os.environ.get("LLM_MODEL") or DEFAULT_MODEL
        self.timeout = float(timeout or os.environ.get("LLM_TIMEOUT") or DEFAULT_TIMEOUT)
        self.max_tokens = int(max_tokens or DEFAULT_MAX_TOKENS)

    def grade_answer(self, payload):
        run_params = payload.run_params or {}
        model = run_params.get("model", self.model)
        modality = "vision" if payload.image_bytes else "text"
        provider_metadata = {
            "provider": "anthropic",
            "model": model,
            "prompt_version": resolve_prompt_version(payload),
            "modality": modality,
        }

        if not self.api_key:
            return GradingResult(
                suggested_score=0,
                rationale="",
                rubric_coverage={},
                review_recommended=True,
                provider_metadata=provider_metadata,
                error="missing_api_key",
            )

        prompt = build_prompt(payload)
        content = []
        if payload.image_bytes:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": payload.image_mime_type or "image/jpeg",
                    "data": base64.b64encode(payload.image_bytes).decode("ascii"),
                },
            })
        content.append({"type": "text", "text": prompt})

        body = json.dumps({
            "model": model,
            "max_tokens": run_params.get("max_tokens", self.max_tokens),
            "messages": [{"role": "user", "content": content}],
        }).encode("utf-8")

        req = urllib.request.Request(
            API_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": API_VERSION,
            },
        )

        try:
            timeout = run_params.get("timeout", self.timeout)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_response = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                error = "rate_limited: {}".format(e.read().decode("utf-8", "replace")[:300])
            else:
                error = "http_{}: {}".format(e.code, e.read().decode("utf-8", "replace")[:300])
            return GradingResult(
                suggested_score=0,
                rationale="",
                rubric_coverage={},
                review_recommended=True,
                provider_metadata=provider_metadata,
                error=error,
            )
        except (urllib.error.URLError, TimeoutError) as e:
            return GradingResult(
                suggested_score=0,
                rationale="",
                rubric_coverage={},
                review_recommended=True,
                provider_metadata=provider_metadata,
                error="network_error: {}".format(e),
            )

        usage = raw_response.get("usage", {})
        provider_metadata["usage"] = usage

        # Safety classifiers podem recusar a requisicao (stop_reason
        # "refusal") - HTTP 200, sem excecao, mas sem conteudo util. Trata
        # como erro conservador em vez de tentar parsear JSON de um content
        # vazio ou parcial.
        if raw_response.get("stop_reason") == "refusal":
            return GradingResult(
                suggested_score=0,
                rationale="",
                rubric_coverage={},
                review_recommended=True,
                provider_metadata=provider_metadata,
                error="provider_refusal",
            )

        text = "".join(
            block.get("text", "") for block in raw_response.get("content", [])
            if block.get("type") == "text"
        )
        parsed = _parse_json_response(text)
        if parsed is None:
            return GradingResult(
                suggested_score=0,
                rationale="",
                rubric_coverage={},
                review_recommended=True,
                provider_metadata=provider_metadata,
                error="unparseable_response: resposta nao continha JSON valido",
            )

        return validate(parsed, provider_metadata=provider_metadata)
