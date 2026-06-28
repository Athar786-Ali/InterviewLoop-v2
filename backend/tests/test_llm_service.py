import httpx
import pytest

from app.core.exceptions import AppError
from app.schemas.interview import Difficulty, InterviewQuestion
from app.services.llm_service import OllamaLLMService


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("bad status", request=None, response=None)

    def json(self):
        return self.payload


class FakeClient:
    calls = []
    responses = []

    def __init__(self, timeout):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def post(self, url, json):
        self.calls.append((url, json, self.timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_ollama_service_parses_structured_json(monkeypatch):
    FakeClient.calls = []
    FakeClient.responses = [
        FakeResponse(
            {
                "response": '{"question":"Explain indexes.","topic":"SQL","difficulty":"medium","expected_signals":["btree"]}'
            }
        )
    ]
    monkeypatch.setattr("app.services.llm_service.httpx.Client", FakeClient)

    service = OllamaLLMService(base_url="http://ollama", model="qwen2.5:7b", timeout_seconds=3, retry_attempts=1)
    result = service.generate_structured("prompt", InterviewQuestion)

    assert result.question == "Explain indexes."
    assert result.difficulty == Difficulty.MEDIUM
    assert FakeClient.calls[0][1]["model"] == "qwen2.5:7b"
    assert FakeClient.calls[0][1]["format"] == "json"


def test_ollama_service_retries_then_succeeds(monkeypatch):
    FakeClient.calls = []
    FakeClient.responses = [
        httpx.TimeoutException("timeout"),
        FakeResponse(
            {
                "response": '{"question":"Explain locks.","topic":"DB","difficulty":"hard","expected_signals":["isolation"]}'
            }
        ),
    ]
    monkeypatch.setattr("app.services.llm_service.httpx.Client", FakeClient)
    monkeypatch.setattr("app.services.llm_service.time.sleep", lambda _: None)

    service = OllamaLLMService(base_url="http://ollama", model="qwen2.5:7b", timeout_seconds=3, retry_attempts=2)

    assert service.generate_structured("prompt", InterviewQuestion).difficulty == Difficulty.HARD
    assert len(FakeClient.calls) == 2


def test_ollama_service_raises_structured_error_after_retries(monkeypatch):
    FakeClient.calls = []
    FakeClient.responses = [FakeResponse({"response": "not-json"})]
    monkeypatch.setattr("app.services.llm_service.httpx.Client", FakeClient)
    service = OllamaLLMService(base_url="http://ollama", model="qwen2.5:7b", timeout_seconds=3, retry_attempts=1)

    with pytest.raises(AppError) as error:
        service.generate_structured("prompt", InterviewQuestion)

    assert error.value.code == "LLM_GENERATION_FAILED"
