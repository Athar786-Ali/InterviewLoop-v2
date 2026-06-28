import subprocess
from types import SimpleNamespace

from app.schemas.code_execution import CodeExecutionRequest, CodeLanguage
from app.services.code_execution_service import CodeExecutionService, DockerSandboxRunner


class FakeRunner:
    def __init__(self):
        self.payload = None

    def run(self, payload):
        self.payload = payload
        return SimpleNamespace(language=payload.language, status="success", stdout="ok", stderr="", exit_code=0, timed_out=False, bandit_issues=[])


def test_code_execution_service_lists_supported_runtimes():
    service = CodeExecutionService(FakeRunner())

    languages = {runtime.language for runtime in service.runtimes()}

    assert languages == {CodeLanguage.PYTHON, CodeLanguage.CPP, CodeLanguage.JAVA, CodeLanguage.JAVASCRIPT}


def test_docker_runner_uses_network_cpu_memory_and_pid_limits(monkeypatch):
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[0] == "bandit":
            return SimpleNamespace(stdout='{"results":[]}', returncode=0)
        return SimpleNamespace(stdout="hello\n", stderr="", returncode=0)

    monkeypatch.setattr("app.services.code_execution_service.subprocess.run", fake_run)
    result = DockerSandboxRunner().run(
        CodeExecutionRequest(language=CodeLanguage.PYTHON, source_code='print("hello")')
    )

    docker_command = commands[-1]
    assert result.status == "success"
    assert "--network" in docker_command
    assert "none" in docker_command
    assert "--memory" in docker_command
    assert "--cpus" in docker_command
    assert "--pids-limit" in docker_command
    assert "--read-only" in docker_command


def test_bandit_findings_block_python_execution(monkeypatch):
    def fake_run(command, **kwargs):
        return SimpleNamespace(
            stdout='{"results":[{"test_id":"B101","issue_severity":"LOW","issue_confidence":"HIGH","issue_text":"assert used","line_number":1}]}',
            returncode=1,
        )

    monkeypatch.setattr("app.services.code_execution_service.subprocess.run", fake_run)

    result = DockerSandboxRunner().run(
        CodeExecutionRequest(language=CodeLanguage.PYTHON, source_code="assert True")
    )

    assert result.status == "blocked"
    assert result.bandit_issues[0].test_id == "B101"


def test_execution_timeout_is_reported(monkeypatch):
    def fake_run(command, **kwargs):
        if command[0] == "bandit":
            return SimpleNamespace(stdout='{"results":[]}', returncode=0)
        raise subprocess.TimeoutExpired(command, timeout=1)

    monkeypatch.setattr("app.services.code_execution_service.subprocess.run", fake_run)

    result = DockerSandboxRunner().run(
        CodeExecutionRequest(language=CodeLanguage.PYTHON, source_code='print("slow")')
    )

    assert result.status == "timeout"
    assert result.timed_out is True
