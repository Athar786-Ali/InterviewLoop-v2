"""Ollama LLM service — structured output generation with robust JSON extraction.

Strategy:
  - Send a plain text prompt (no format="json") to maximise model compatibility.
  - The prompt explicitly requests JSON output via QUESTION_OUTPUT_INSTRUCTIONS.
  - Extract the JSON block from the free-text response using a regex.
  - Validate with Pydantic; retry on failure.
"""

import json
import logging
import re
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

# Matches the first {...} block, even if the model adds prose before/after it
_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*?\}", re.DOTALL)


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from a free-text LLM response."""
    # 1. Try the whole text first (ideal case)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 2. Try a markdown code fence (```json ... ``` or ``` ... ```)
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Greedy search — find the longest valid JSON object in the response
    # Walk every '{' position and try to parse forward
    for match in re.finditer(r"\{", text):
        start = match.start()
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break

    raise json.JSONDecodeError("No valid JSON object found in LLM response", text, 0)


class OllamaLLMService:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        retry_attempts: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout_seconds = timeout_seconds or settings.ollama_timeout_seconds
        self.retry_attempts = retry_attempts or settings.ollama_retry_attempts

    def generate_structured(self, prompt: str, schema: type[T]) -> T:
        """Generate a structured response from Ollama and parse it into `schema`."""
        last_error: Exception | None = None

        for attempt in range(1, self.retry_attempts + 1):
            try:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    # NOTE: Do NOT send format="json" — it causes HTTP 500 on some
                    # Ollama builds.  The prompt already instructs the model to
                    # respond with valid JSON, and we extract it robustly below.
                }
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()

                raw_text = response.json().get("response", "")
                logger.debug("ollama_raw_response", extra={"attempt": attempt, "text": raw_text[:500]})

                data = _extract_json(raw_text)
                return schema.model_validate(data)

            except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
                last_error = exc
                logger.warning(
                    "ollama_http_error",
                    extra={"attempt": attempt, "model": self.model, "error": str(exc)},
                )
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                logger.warning(
                    "ollama_parse_error",
                    extra={"attempt": attempt, "model": self.model, "error": str(exc)},
                )

            if attempt < self.retry_attempts:
                time.sleep(0.5 * attempt)

        raise AppError(
            "LLM_GENERATION_FAILED",
            "Unable to generate a structured interview response. "
            "Make sure Ollama is running and the qwen2.5:7b model is loaded.",
            503,
        ) from last_error
