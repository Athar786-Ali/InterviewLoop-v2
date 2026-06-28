import json
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import AppError
from app.schemas.code_execution import BanditIssue, CodeExecutionRequest, CodeExecutionResult, CodeLanguage, RuntimeSpec


RUNTIMES: dict[CodeLanguage, RuntimeSpec] = {
    CodeLanguage.PYTHON: RuntimeSpec(
        language=CodeLanguage.PYTHON,
        label="Python",
        monaco_language="python",
        template='print("Hello from Python")\n',
    ),
    CodeLanguage.CPP: RuntimeSpec(
        language=CodeLanguage.CPP,
        label="C++",
        monaco_language="cpp",
        template='#include <iostream>\nint main() { std::cout << "Hello from C++"; }\n',
    ),
    CodeLanguage.JAVA: RuntimeSpec(
        language=CodeLanguage.JAVA,
        label="Java",
        monaco_language="java",
        template='public class Main { public static void main(String[] args) { System.out.println("Hello from Java"); } }\n',
    ),
    CodeLanguage.JAVASCRIPT: RuntimeSpec(
        language=CodeLanguage.JAVASCRIPT,
        label="JavaScript",
        monaco_language="javascript",
        template='console.log("Hello from JavaScript");\n',
    ),
}


class DockerSandboxRunner:
    def run(self, payload: CodeExecutionRequest) -> CodeExecutionResult:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            source_path = self._write_source(workspace, payload)
            if payload.language == CodeLanguage.PYTHON:
                issues = self._bandit_scan(source_path)
                if issues:
                    return CodeExecutionResult(
                        language=payload.language,
                        status="blocked",
                        stderr="Bandit blocked execution because security issues were found.",
                        bandit_issues=issues,
                    )

            command = self._docker_command(workspace, payload)
            try:
                completed = subprocess.run(
                    command,
                    input=payload.stdin,
                    capture_output=True,
                    text=True,
                    timeout=settings.code_execution_timeout_seconds + 1,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return CodeExecutionResult(language=payload.language, status="timeout", timed_out=True)

            return CodeExecutionResult(
                language=payload.language,
                status="success" if completed.returncode == 0 else "error",
                stdout=completed.stdout,
                stderr=completed.stderr,
                exit_code=completed.returncode,
            )

    def _write_source(self, workspace: Path, payload: CodeExecutionRequest) -> Path:
        filenames = {
            CodeLanguage.PYTHON: "main.py",
            CodeLanguage.CPP: "main.cpp",
            CodeLanguage.JAVA: "Main.java",
            CodeLanguage.JAVASCRIPT: "main.js",
        }
        source_path = workspace / filenames[payload.language]
        source_path.write_text(payload.source_code, encoding="utf-8")
        return source_path

    def _bandit_scan(self, source_path: Path) -> list[BanditIssue]:
        completed = subprocess.run(
            ["bandit", "-q", "-f", "json", str(source_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if not completed.stdout:
            return []
        data = json.loads(completed.stdout)
        return [
            BanditIssue(
                test_id=item.get("test_id", ""),
                severity=item.get("issue_severity", ""),
                confidence=item.get("issue_confidence", ""),
                text=item.get("issue_text", ""),
                line_number=item.get("line_number"),
            )
            for item in data.get("results", [])
        ]

    def _docker_command(self, workspace: Path, payload: CodeExecutionRequest) -> list[str]:
        base = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--memory",
            settings.code_execution_memory_limit,
            "--cpus",
            str(settings.code_execution_cpu_limit),
            "--pids-limit",
            str(settings.code_execution_pids_limit),
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "-v",
            f"{workspace}:/workspace:ro",
            "-w",
            "/workspace",
        ]
        if payload.language == CodeLanguage.PYTHON:
            return base + ["python:3.12-slim", "timeout", str(settings.code_execution_timeout_seconds), "python", "main.py"]
        if payload.language == CodeLanguage.CPP:
            return base + [
                "gcc:13",
                "bash",
                "-lc",
                f"timeout {settings.code_execution_timeout_seconds} g++ main.cpp -O2 -std=c++17 -o /tmp/main && timeout {settings.code_execution_timeout_seconds} /tmp/main",
            ]
        if payload.language == CodeLanguage.JAVA:
            return base + [
                "eclipse-temurin:21",
                "bash",
                "-lc",
                f"timeout {settings.code_execution_timeout_seconds} javac -d /tmp Main.java && timeout {settings.code_execution_timeout_seconds} java -cp /tmp Main",
            ]
        return base + ["node:22-alpine", "timeout", str(settings.code_execution_timeout_seconds), "node", "main.js"]


class CodeExecutionService:
    def __init__(self, runner: DockerSandboxRunner) -> None:
        self.runner = runner

    def runtimes(self) -> list[RuntimeSpec]:
        return list(RUNTIMES.values())

    def execute(self, payload: CodeExecutionRequest) -> CodeExecutionResult:
        if payload.language not in RUNTIMES:
            raise AppError("UNSUPPORTED_LANGUAGE", "Unsupported code execution language.", 422)
        return self.runner.run(payload)
