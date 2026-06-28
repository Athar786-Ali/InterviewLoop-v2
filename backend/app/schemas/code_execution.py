from enum import StrEnum

from pydantic import BaseModel, Field


class CodeLanguage(StrEnum):
    PYTHON = "python"
    CPP = "cpp"
    JAVA = "java"
    JAVASCRIPT = "javascript"


class CodeExecutionRequest(BaseModel):
    language: CodeLanguage
    source_code: str = Field(min_length=1, max_length=20000)
    stdin: str = Field(default="", max_length=8000)


class BanditIssue(BaseModel):
    test_id: str
    severity: str
    confidence: str
    text: str
    line_number: int | None = None


class CodeExecutionResult(BaseModel):
    language: CodeLanguage
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    timed_out: bool = False
    bandit_issues: list[BanditIssue] = Field(default_factory=list)


class RuntimeSpec(BaseModel):
    language: CodeLanguage
    label: str
    monaco_language: str
    template: str
