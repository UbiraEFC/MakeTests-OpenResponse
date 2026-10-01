import base64
import json
import os
import urllib.error
import urllib.request

from .base import LLMProvider
from .prompt_builder import build_prompt, resolve_prompt_version
from .response_validator import validate
from .schemas import GradingResult

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT = 30
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "suggested_score": {"type": "integer"},
        "rationale": {"type": "string"},
        "rubric_coverage": {"type": "object"},
        "review_recommended": {"type": "boolean"},
        "transcription": {"type": "string"},
    },
    "required": ["suggested_score", "rationale", "review_recommended"],
}


class GeminiProvider(LLMProvider):
    """Adapter inicial (Fase 4) - chama a Gemini API via urllib (stdlib, sem
    SDK) usando structured output nativo (responseSchema/responseMimeType).
    """

    def __init__(self, api_key=None, model=None, timeout=None, temperature=None):
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.model = model or os.environ.get("LLM_MODEL") or DEFAULT_MODEL
        self.timeout = float(timeout or os.environ.get("LLM_TIMEOUT") or DEFAULT_TIMEOUT)
        self.temperature = float(temperature if temperature is not None else os.environ.get("LLM_TEMPERATURE", 0.2))

    def grade_answer(self, payload):
        run_params = payload.run_params or {}
        model = run_params.get("model", self.model)
        modality = "vision" if payload.image_bytes else "text"
        provider_metadata = {
            "provider": "gemini",
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
        parts = [{"text": prompt}]
        if payload.image_bytes:
            parts.append({
                "inlineData": {
                    "mimeType": payload.image_mime_type or "image/jpeg",
                    "data": base64.b64encode(payload.image_bytes).decode("ascii"),
                }
            })
        body = json.dumps({
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": run_params.get("temperature", self.temperature),
                "responseMimeType": "application/json",
                "responseSchema": RESPONSE_SCHEMA,
            },
        }).encode("utf-8")

        url = "{}/{}:generateContent".format(API_BASE, model)
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "X-goog-api-key": self.api_key},
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

        try:
            text = raw_response["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
        except (KeyError, IndexError, ValueError) as e:
            return GradingResult(
                suggested_score=0,
                rationale="",
                rubric_coverage={},
                review_recommended=True,
                provider_metadata=provider_metadata,
                error="unparseable_response: {}".format(e),
            )

        usage = raw_response.get("usageMetadata", {})
        provider_metadata["usage"] = usage
        return validate(parsed, provider_metadata=provider_metadata)
