from fastapi.testclient import TestClient

from app.main import create_app


def test_interview_websocket_accepts_ping_and_returns_pong():
    client = TestClient(create_app())

    with client.websocket_connect("/api/v1/interviews/session-route/events") as websocket:
        connected = websocket.receive_json()
        websocket.send_json({"type": "ping", "payload": {}})
        pong = websocket.receive_json()

    assert connected["type"] == "connected"
    assert pong["type"] == "pong"
    assert pong["session_id"] == "session-route"
