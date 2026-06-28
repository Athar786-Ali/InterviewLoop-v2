import pytest
from starlette.websockets import WebSocketState

from app.schemas.websocket import ClientInterviewEvent, InterviewEventType
from app.services.websocket_manager import InterviewConnectionManager


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.closed = False
        self.messages = []
        self.client_state = None

    async def accept(self):
        self.accepted = True
        self.client_state = WebSocketState.CONNECTED

    async def send_json(self, payload):
        self.messages.append(payload)

    async def close(self, code=1000):
        self.closed = True


@pytest.mark.asyncio
async def test_connection_manager_connects_broadcasts_and_disconnects():
    manager = InterviewConnectionManager(heartbeat_seconds=1, history_limit=10)
    websocket = FakeWebSocket()

    await manager.connect("session-1", websocket)
    event = await manager.broadcast("session-1", InterviewEventType.ANSWER_SUBMITTED, {"answer": "hello"})
    manager.disconnect("session-1", websocket)

    assert websocket.accepted is True
    assert websocket.messages[0]["type"] == "connected"
    assert websocket.messages[-1]["payload"] == {"answer": "hello"}
    assert event.sequence == 2
    assert "session-1" not in manager.active


@pytest.mark.asyncio
async def test_connection_manager_replays_events_after_last_sequence():
    manager = InterviewConnectionManager(heartbeat_seconds=1, history_limit=10)
    first = FakeWebSocket()
    await manager.connect("session-1", first)
    await manager.broadcast("session-1", InterviewEventType.TRANSCRIPT_PARTIAL, {"text": "one"})
    await manager.broadcast("session-1", InterviewEventType.TRANSCRIPT_FINAL, {"text": "two"})
    reconnect = FakeWebSocket()

    await manager.connect("session-1", reconnect, last_sequence=2)

    assert reconnect.messages[0]["type"] == "reconnected"
    assert reconnect.messages[1]["type"] == "transcript_final"
    assert reconnect.messages[1]["payload"]["text"] == "two"


@pytest.mark.asyncio
async def test_connection_manager_maps_ping_to_pong():
    manager = InterviewConnectionManager(heartbeat_seconds=1, history_limit=10)
    websocket = FakeWebSocket()
    await manager.connect("session-1", websocket)

    await manager.handle_client_event("session-1", ClientInterviewEvent(type="ping"))

    assert websocket.messages[-1]["type"] == "pong"


@pytest.mark.asyncio
async def test_connection_manager_cleanup_closes_connections_and_clears_history():
    manager = InterviewConnectionManager(heartbeat_seconds=1, history_limit=10)
    websocket = FakeWebSocket()
    await manager.connect("session-1", websocket)
    await manager.broadcast("session-1", InterviewEventType.QUESTION_STARTED, {"id": "q1"})

    await manager.cleanup_session("session-1")

    assert websocket.closed is True
    assert "session-1" not in manager.active
    assert "session-1" not in manager.history
