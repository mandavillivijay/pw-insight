from __future__ import annotations

import json
import zipfile
from pathlib import Path

from .parser import FailedTest


def _find_data_dir(report_path: Path) -> Path:
    if report_path.is_dir():
        return report_path / "data"
    # given index.html — look next to it
    return report_path.parent / "data"


def parse_html_report(report_path: str) -> tuple[list[FailedTest], int, int]:
    p = Path(report_path)
    data_dir = _find_data_dir(p)

    if not data_dir.exists():
        raise FileNotFoundError(
            f"No data/ directory found alongside {p}. "
            "Make sure you point --report at the playwright-report/ folder or its index.html."
        )

    main_report: dict | None = None
    test_details: dict[str, dict] = {}

    for zip_path in sorted(data_dir.glob("*.zip")):
        try:
            with zipfile.ZipFile(zip_path) as zf:
                for name in zf.namelist():
                    if not name.endswith(".json"):
                        continue
                    try:
                        data = json.loads(zf.read(name).decode("utf-8"))
                    except Exception:
                        continue
                    if "files" in data and "stats" in data:
                        main_report = data
                    elif "testId" in data and "results" in data:
                        test_details[data["testId"]] = data
        except Exception:
            continue

    if main_report is None:
        raise ValueError(
            "Could not find report data inside the HTML report's data/ directory. "
            "The format may be unsupported — try regenerating with --reporter=json instead."
        )

    failures: list[FailedTest] = []
    for file_info in main_report.get("files", []):
        file_name = file_info.get("fileName", "")
        for test in file_info.get("tests", []):
            outcome = test.get("outcome", "")
            ok = test.get("ok", True)
            if ok and outcome not in ("unexpected", "flaky"):
                continue

            test_id = test.get("testId", "")
            detail = test_details.get(test_id, {})

            error_message = ""
            stack_trace = ""
            for result in detail.get("results", []):
                errors = result.get("errors", [])
                if errors:
                    error_message = errors[0].get("message", "")
                    stack_trace = errors[0].get("stack", "")
                    break

            path_parts = test.get("path", [])
            title = test.get("title", "")
            full_title = " > ".join(path_parts + [title]) if path_parts else title

            failures.append(FailedTest(
                file=file_name,
                title=title,
                full_title=full_title,
                error_message=error_message,
                stack_trace=stack_trace,
            ))

    stats = main_report.get("stats", {})
    total = stats.get("total", 0) or (len(failures) + stats.get("expected", 0))
    passed = stats.get("expected", max(0, total - len(failures)))

    return failures, passed, total
