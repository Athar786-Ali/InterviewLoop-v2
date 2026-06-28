from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_code_execution_service
from app.main import create_app
from app.schemas.code_execution import CodeExecutionResult, CodeLanguage, RuntimeSpec


class FakeCodeExecutionService:
    def runtimes(self):
        return [
            RuntimeSpec(
                language=CodeLanguage.PYTHON,
                label="Python",
                monaco_language="python",
                template='print("hi")',
            )
        ]

    def execute(self, payload):
        return CodeExecutionResult(
            language=payload.language,
            status="success",
            stdout="hi\n",
            stderr="",
            exit_code=0,
        )


def test_code_execution_runtime_route_returns_supported_languages():
    app = create_app()
    app.dependency_overrides[get_code_execution_service] = lambda: FakeCodeExecutionService()
    client = TestClient(app)

    response = client.get("/api/v1/code-execution/runtimes")

    assert response.status_code == 200
    assert response.json()["data"][0]["language"] == "python"


def test_code_execution_run_route_returns_result():
    app = create_app()
    app.dependency_overrides[get_code_execution_service] = lambda: FakeCodeExecutionService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/code-execution/run",
        json={"language": "python", "source_code": 'print("hi")', "stdin": ""},
    )

    assert response.status_code == 200
    assert response.json()["data"]["stdout"] == "hi\n"
