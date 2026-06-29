"""Coding judge schemas — request/response models for the DSA coding round."""

from enum import StrEnum
from pydantic import BaseModel, Field


class CodeLanguage(StrEnum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"


class TestCase(BaseModel):
    input: str
    expected_output: str
    label: str = ""


class CodingProblem(BaseModel):
    id: str
    title: str
    difficulty: str          # easy | medium | hard
    category: str            # arrays | strings | trees | …
    tags: list[str] = Field(default_factory=list)
    problem_statement: str
    constraints: list[str] = Field(default_factory=list)
    examples: list[dict] = Field(default_factory=list)   # [{input, output, explanation}]
    starter_code: dict[str, str] = Field(default_factory=dict)  # language → template
    test_cases: list[TestCase] = Field(default_factory=list)


class CodingSubmitRequest(BaseModel):
    problem_id: str
    language: CodeLanguage = CodeLanguage.PYTHON
    source_code: str = Field(min_length=1, max_length=20000)


class TestCaseResult(BaseModel):
    label: str
    input: str
    expected: str
    actual: str
    passed: bool
    runtime_ms: float | None = None


class CodingSubmitResponse(BaseModel):
    problem_id: str
    language: str
    passed: int
    total: int
    all_passed: bool
    results: list[TestCaseResult]
    stderr: str = ""
    timed_out: bool = False
