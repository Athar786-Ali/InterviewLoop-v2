import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.v1.dependencies import get_deepgram_service, get_typed_fallback_service
from app.schemas.common import ApiResponse
from app.schemas.speech import TypedAnswerRequest, TypedAnswerResponse
from app.services.deepgram_service import DeepgramStreamingService
from app.services.speech_service import TypedFallbackService

router = APIRouter(prefix="/speech", tags=["speech"])


@router.websocket("/stream")
async def stream_speech(
    websocket: WebSocket,
    deepgram_service: Annotated[DeepgramStreamingService, Depends(get_deepgram_service)],
) -> None:
    await websocket.accept()
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def audio_factory():
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk

    async def receive_audio() -> None:
        try:
            while True:
                chunk = await websocket.receive_bytes()
                await queue.put(chunk)
        except WebSocketDisconnect:
            await queue.put(None)

    receiver = asyncio.create_task(receive_audio())
    try:
        async for event in deepgram_service.stream_transcripts(audio_factory):
            await websocket.send_json(event.model_dump())
    finally:
        if not receiver.done():
            receiver.cancel()


@router.post("/typed-fallback", response_model=ApiResponse[TypedAnswerResponse])
def typed_fallback(
    payload: TypedAnswerRequest,
    fallback_service: Annotated[TypedFallbackService, Depends(get_typed_fallback_service)],
) -> ApiResponse[TypedAnswerResponse]:
    return ApiResponse(data=fallback_service.submit(payload.session_id, payload.answer), message="Typed answer accepted.")
