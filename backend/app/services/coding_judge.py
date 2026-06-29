"""Coding judge service — runs submitted code against test cases using the existing
sandbox (CodeExecutionService) and returns per-test-case pass/fail results.
"""

import time

from app.schemas.code_execution import CodeExecutionRequest
from app.schemas.coding import CodingSubmitRequest, CodingSubmitResponse, TestCaseResult
from app.data.coding_problems import PROBLEMS_BY_ID
from app.services.code_execution_service import CodeExecutionService
from app.core.exceptions import AppError


class CodingJudgeService:
    def __init__(self, execution_service: CodeExecutionService) -> None:
        self.execution_service = execution_service

    def judge(self, request: CodingSubmitRequest) -> CodingSubmitResponse:
        problem = PROBLEMS_BY_ID.get(request.problem_id)
        if not problem:
            raise AppError("PROBLEM_NOT_FOUND", f"Problem '{request.problem_id}' not found.", 404)

        results: list[TestCaseResult] = []
        last_stderr = ""

        for test_case in problem.test_cases:
            start = time.perf_counter()
            try:
                exec_result = self.execution_service.execute(
                    CodeExecutionRequest(
                        language=request.language,
                        source_code=request.source_code,
                        stdin=test_case.input,
                    )
                )
                elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
                actual = exec_result.stdout.strip()
                expected = test_case.expected_output.strip()
                passed = (actual == expected) and not exec_result.timed_out and exec_result.exit_code == 0
                if exec_result.stderr:
                    last_stderr = exec_result.stderr
            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
                actual = ""
                passed = False
                last_stderr = str(exc)

            results.append(
                TestCaseResult(
                    label=test_case.label,
                    input=test_case.input,
                    expected=test_case.expected_output.strip(),
                    actual=actual,
                    passed=passed,
                    runtime_ms=elapsed_ms,
                )
            )

        passed_count = sum(1 for r in results if r.passed)
        return CodingSubmitResponse(
            problem_id=request.problem_id,
            language=request.language,
            passed=passed_count,
            total=len(results),
            all_passed=passed_count == len(results),
            results=results,
            stderr=last_stderr,
        )
