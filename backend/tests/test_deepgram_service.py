import asyncio
import json

import pytest

from app.schemas.speech import TranscriptEventType
from app.services.deepgram_service import DeepgramStreamingService


class FakeDeepgramSocket:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def recv(self):
        if not self.messages:
            raise StopAsyncIteration
        message = self.messages.pop(0)
        if isinstance(message, Exception):
            raise message
        return message

    async def send(self, payload):
        self.sent.append(payload)


class FakeConnector:
    def __init__(self, sockets):
        self.sockets = list(sockets)
        self.calls = []

    def __call__(self, url, extra_headers):
        self.calls.append((url, extra_headers))
        return self.sockets.pop(0)


async def audio_chunks():
    yield b"audio-1"


def deepgram_payload(text, is_final=False):
    return json.dumps(
        {
            "channel": {"alternatives": [{"transcript": text, "confidence": 0.91}]},
            "is_final": is_final,
        }
    )


async def noop_sleep(_):
    return None


@pytest.mark.asyncio
async def test_deepgram_stream_emits_partial_and_final_transcripts():
    connector = FakeConnector(
        [
            FakeDeepgramSocket(
                [
                    deepgram_payload("hello", is_final=False),
                    deepgram_payload("hello world", is_final=True),
                    StopAsyncIteration(),
                ]
            )
        ]
    )
    service = DeepgramStreamingService(api_key="key", connect=connector, reconnect_attempts=1, timeout_seconds=1)

    events = []
    async for event in service.stream_transcripts(lambda: audio_chunks()):
        events.append(event)

    assert events[0].type == TranscriptEventType.PARTIAL
    assert events[0].text == "hello"
    assert events[1].type == TranscriptEventType.FINAL
    assert events[1].is_final is True
    assert events[-1].type == TranscriptEventType.CLOSED
    assert connector.calls[0][1]["Authorization"] == "Token key"


@pytest.mark.asyncio
async def test_deepgram_stream_reconnects_after_recoverable_error(monkeypatch):
    connector = FakeConnector(
        [
            FakeDeepgramSocket([asyncio.TimeoutError()]),
            FakeDeepgramSocket([deepgram_payload("recovered", is_final=True), StopAsyncIteration()]),
        ]
    )
    monkeypatch.setattr("app.services.deepgram_service.asyncio.sleep", noop_sleep)
    service = DeepgramStreamingService(api_key="key", connect=connector, reconnect_attempts=2, timeout_seconds=1)

    events = []
    async for event in service.stream_transcripts(lambda: audio_chunks()):
        events.append(event)

    assert events[0].type == TranscriptEventType.RECONNECTED
    assert events[1].type == TranscriptEventType.FINAL
    assert events[1].text == "recovered"


@pytest.mark.asyncio
async def test_deepgram_stream_returns_error_after_reconnects_exhausted(monkeypatch):
    connector = FakeConnector([FakeDeepgramSocket([asyncio.TimeoutError()])])
    monkeypatch.setattr("app.services.deepgram_service.asyncio.sleep", noop_sleep)
    service = DeepgramStreamingService(api_key="key", connect=connector, reconnect_attempts=1, timeout_seconds=1)

    events = []
    async for event in service.stream_transcripts(lambda: audio_chunks()):
        events.append(event)

    assert events == [
        events[0],
    ]
    assert events[0].type == TranscriptEventType.ERROR
    assert events[0].error_code == "DEEPGRAM_STREAM_FAILED"
