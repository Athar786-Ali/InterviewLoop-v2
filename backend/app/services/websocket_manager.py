import asyncio
import logging
from collections import defaultdict, deque

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.core.config import settings
from app.schemas.websocket import ClientInterviewEvent, InterviewEvent, InterviewEventType

logger = logging.getLogger(__name__)


class InterviewConnectionManager:
    def __init__(self, heartbeat_seconds: int | None = None, history_limit: int | None = None) -> None:
        self.heartbeat_seconds = heartbeat_seconds or settings.websocket_heartbeat_seconds
        self.history_limit = history_limit or settings.websocket_event_history_limit
        self.active: dict[str, set[WebSocket]] = defaultdict(set)
        self.history: dict[str, deque[InterviewEvent]] = defaultdict(lambda: deque(maxlen=self.history_limit))
        self.sequences: dict[str, int] = defaultdict(int)

    async def connect(self, session_id: str, websocket: WebSocket, last_sequence: int | None = None) -> None:
        await websocket.accept()
        self.active[session_id].add(websocket)
        event_type = InterviewEventType.RECONNECTED if last_sequence else InterviewEventType.CONNECTED
        await self.send_personal(
            websocket,
            self._event(session_id, event_type, {"heartbeat_seconds": self.heartbeat_seconds}),
            persist=False,
        )
        if last_sequence is not None:
            await self.replay(session_id, websocket, last_sequence)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        self.active[session_id].discard(websocket)
        if not self.active[session_id]:
            self.active.pop(session_id, None)

    async def broadcast(self, session_id: str, event_type: InterviewEventType, payload: dict) -> InterviewEvent:
        event = self._event(session_id, event_type, payload)
        self.history[session_id].append(event)
        stale_connections = []
        for websocket in self.active.get(session_id, set()):
            try:
                await self.send_personal(websocket, event, persist=False)
            except RuntimeError:
                stale_connections.append(websocket)
        for websocket in stale_connections:
            self.disconnect(session_id, websocket)
        return event

    async def send_personal(self, websocket: WebSocket, event: InterviewEvent, persist: bool = False) -> None:
        if persist:
            self.history[event.session_id].append(event)
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json(event.model_dump(mode="json"))

    async def replay(self, session_id: str, websocket: WebSocket, last_sequence: int) -> None:
        for event in self.history.get(session_id, []):
            if event.sequence > last_sequence:
                await self.send_personal(websocket, event, persist=False)

    async def heartbeat(self, session_id: str, websocket: WebSocket, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            await asyncio.sleep(self.heartbeat_seconds)
            try:
                await self.send_personal(websocket, self._event(session_id, InterviewEventType.HEARTBEAT, {}))
            except RuntimeError:
                stop_event.set()

    async def handle_client_event(self, session_id: str, message: ClientInterviewEvent) -> None:
        event_type = self._map_client_event_type(message.type)
        await self.broadcast(session_id, event_type, message.payload)

    async def cleanup_session(self, session_id: str) -> None:
        await self.broadcast(session_id, InterviewEventType.SESSION_CLEANUP, {"reason": "session_closed"})
        for websocket in list(self.active.get(session_id, set())):
            await websocket.close(code=1000)
        self.active.pop(session_id, None)
        self.history.pop(session_id, None)
        self.sequences.pop(session_id, None)

    def _event(self, session_id: str, event_type: InterviewEventType, payload: dict) -> InterviewEvent:
        self.sequences[session_id] += 1
        return InterviewEvent(type=event_type, session_id=session_id, sequence=self.sequences[session_id], payload=payload)

    def _map_client_event_type(self, event_type: str) -> InterviewEventType:
        mapping = {
            "ping": InterviewEventType.PONG,
            "question_started": InterviewEventType.QUESTION_STARTED,
            "transcript_partial": InterviewEventType.TRANSCRIPT_PARTIAL,
            "transcript_final": InterviewEventType.TRANSCRIPT_FINAL,
            "answer_submitted": InterviewEventType.ANSWER_SUBMITTED,
            "evaluation_ready": InterviewEventType.EVALUATION_READY,
        }
        return mapping.get(event_type, InterviewEventType.ERROR)


connection_manager = InterviewConnectionManager()
