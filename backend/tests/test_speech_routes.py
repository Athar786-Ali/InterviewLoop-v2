from fastapi.testclient import TestClient

from app.main import create_app


def test_typed_fallback_route_accepts_answer_without_secondary_stt():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/speech/typed-fallback",
        json={"session_id": "session-1", "answer": "I prefer service layers for testability."},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"] == {
        "session_id": "session-1",
        "transcript": "I prefer service layers for testability.",
        "source": "typed",
    }
