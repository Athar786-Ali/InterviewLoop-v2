import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.schemas.websocket import ClientInterviewEvent, InterviewEventType
from app.services.websocket_manager import connection_manager

router = APIRouter(prefix="/interviews", tags=["interview-websocket"])


@router.websocket("/{session_id}/events")
async def interview_events(
    websocket: WebSocket,
    session_id: str,
    last_sequence: int | None = Query(default=None),
) -> None:
    await connection_manager.connect(session_id, websocket, last_sequence)
    stop_heartbeat = asyncio.Event()
    heartbeat_task = asyncio.create_task(connection_manager.heartbeat(session_id, websocket, stop_heartbeat))
    try:
        while True:
            raw_message = await websocket.receive_json()
            try:
                message = ClientInterviewEvent.model_validate(raw_message)
                await connection_manager.handle_client_event(session_id, message)
            except ValidationError as exc:
                await connection_manager.broadcast(
                    session_id,
                    InterviewEventType.ERROR,
                    {"code": "INVALID_EVENT", "message": str(exc.errors()[0]["msg"])},
                )
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id, websocket)
    finally:
        stop_heartbeat.set()
        heartbeat_task.cancel()
