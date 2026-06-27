from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FailedTest:
    file: str
    title: str
    full_title: str
    error_message: str
    stack_trace: str


def _walk_suites(suites: list[dict[str, Any]], parent_title: str = "", parent_file: str = "") -> list[FailedTest]:
    failures: list[FailedTest] = []
    for suite in suites:
        suite_title = suite.get("title", "")
        file_path = suite.get("file", "") or parent_file
        full_suite = f"{parent_title} > {suite_title}".strip(" >") if parent_title else suite_title

        nested = suite.get("suites", [])
        if nested:
            failures.extend(_walk_suites(nested, full_suite, file_path))

        for spec in suite.get("specs", []):
            spec_title = spec.get("title", "")
            full_title = f"{full_suite} > {spec_title}".strip(" >") if full_suite else spec_title

            for test in spec.get("tests", []):
                results = test.get("results", [])
                for result in results:
                    r_status = result.get("status", "")
                    if r_status in ("passed", "skipped"):
                        continue
                    error = result.get("error") or {}
                    message = error.get("message", "")
                    stack = error.get("stack", "")
                    if r_status == "timedOut" and not message:
                        message = "Test timed out"
                    if message or stack or r_status in ("failed", "timedOut"):
                        failures.append(FailedTest(
                            file=file_path,
                            title=spec_title,
                            full_title=full_title,
                            error_message=message,
                            stack_trace=stack,
                        ))
                        break

    return failures


def _count_tests(suites: list[dict[str, Any]]) -> int:
    count = 0
    for suite in suites:
        for spec in suite.get("specs", []):
            count += len(spec.get("tests", []))
        count += _count_tests(suite.get("suites", []))
    return count


def parse_results(report_path: str) -> tuple[list[FailedTest], int, int]:
    data = json.loads(Path(report_path).read_text(encoding="utf-8"))
    suites = data.get("suites", [])
    failures = _walk_suites(suites)
    total = _count_tests(suites)
    passed = total - len(failures)
    return failures, passed, total
