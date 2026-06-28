import asyncio
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from urllib.parse import urlencode

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from app.core.config import settings
from app.core.exceptions import AppError
from app.schemas.speech import TranscriptEvent, TranscriptEventType

logger = logging.getLogger(__name__)
AudioIteratorFactory = Callable[[], AsyncIterator[bytes]]


class DeepgramStreamingService:
    def __init__(
        self,
        api_key: str | None = None,
        websocket_url: str | None = None,
        timeout_seconds: float | None = None,
        reconnect_attempts: int | None = None,
        connect: Callable[..., Awaitable[object]] | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.deepgram_api_key
        self.websocket_url = websocket_url or settings.deepgram_ws_url
        self.timeout_seconds = timeout_seconds or settings.deepgram_timeout_seconds
        self.reconnect_attempts = reconnect_attempts or settings.deepgram_reconnect_attempts
        self.connect = connect or websockets.connect

    async def stream_transcripts(self, audio_factory: AudioIteratorFactory) -> AsyncIterator[TranscriptEvent]:
        if not self.api_key:
            raise AppError("DEEPGRAM_CONFIGURATION_ERROR", "Deepgram API key is not configured.", 500)

        for attempt in range(1, self.reconnect_attempts + 1):
            try:
                if attempt > 1:
                    yield TranscriptEvent(
                        type=TranscriptEventType.RECONNECTED,
                        message=f"Reconnected to Deepgram on attempt {attempt}.",
                    )
                async for event in self._stream_once(audio_factory):
                    yield event
                yield TranscriptEvent(type=TranscriptEventType.CLOSED, message="Deepgram stream closed.")
                return
            except (asyncio.TimeoutError, ConnectionClosed, WebSocketException, OSError) as exc:
                logger.warning("deepgram_stream_error", extra={"attempt": attempt, "error": str(exc)})
                if attempt >= self.reconnect_attempts:
                    yield TranscriptEvent(
                        type=TranscriptEventType.ERROR,
                        error_code="DEEPGRAM_STREAM_FAILED",
                        message="Speech transcription failed. Use typed fallback.",
                    )
                    return
                await asyncio.sleep(0.2 * attempt)

    async def _stream_once(self, audio_factory: AudioIteratorFactory) -> AsyncIterator[TranscriptEvent]:
        async with self.connect(self._url(), extra_headers={"Authorization": f"Token {self.api_key}"}) as websocket:
            sender = asyncio.create_task(self._send_audio(websocket, audio_factory))
            try:
                while True:
                    raw_message = await asyncio.wait_for(websocket.recv(), timeout=self.timeout_seconds)
                    event = self._parse_message(raw_message)
                    if event:
                        yield event
            except (ConnectionClosed, StopAsyncIteration):
                await sender
            finally:
                if not sender.done():
                    sender.cancel()

    async def _send_audio(self, websocket: object, audio_factory: AudioIteratorFactory) -> None:
        async for chunk in audio_factory():
            await websocket.send(chunk)
        await websocket.send(json.dumps({"type": "CloseStream"}))

    def _parse_message(self, raw_message: str | bytes) -> TranscriptEvent | None:
        if isinstance(raw_message, bytes):
            raw_message = raw_message.decode("utf-8")
        payload = json.loads(raw_message)
        if payload.get("type") == "Metadata":
            return None
        channel = payload.get("channel", {})
        alternatives = channel.get("alternatives", [])
        transcript = alternatives[0].get("transcript", "") if alternatives else ""
        if not transcript:
            return None
        is_final = bool(payload.get("is_final") or payload.get("speech_final"))
        confidence = alternatives[0].get("confidence") if alternatives else None
        return TranscriptEvent(
            type=TranscriptEventType.FINAL if is_final else TranscriptEventType.PARTIAL,
            text=transcript,
            is_final=is_final,
            confidence=confidence,
        )

    def _url(self) -> str:
        query = urlencode(
            {
                "model": settings.deepgram_model,
                "language": settings.deepgram_language,
                "encoding": settings.deepgram_encoding,
                "sample_rate": settings.deepgram_sample_rate,
                "interim_results": "true",
                "smart_format": "true",
            }
        )
        return f"{self.websocket_url}?{query}"
