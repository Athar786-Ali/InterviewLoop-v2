import json
import logging
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


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
        last_error: Exception | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                }
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                raw_text = response.json().get("response", "")
                return schema.model_validate(json.loads(raw_text))
            except (httpx.TimeoutException, httpx.HTTPError, json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                logger.warning("ollama_generation_failed", extra={"attempt": attempt, "model": self.model})
                if attempt < self.retry_attempts:
                    time.sleep(0.2 * attempt)

        raise AppError("LLM_GENERATION_FAILED", "Unable to generate a structured interview response.", 503) from last_error
