from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from .parser import FailedTest


def _find_data_dir(p: Path) -> Path | None:
    """Return the data/ directory for an HTML report path, or None if absent."""
    candidates = [
        p / "data",          # given the report directory
        p.parent / "data",   # given index.html inside the report directory
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def _parse_data_dir(data_dir: Path) -> tuple[list[FailedTest], int, int]:
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
            "Found the data/ directory but could not read report data from it. "
            "The Playwright version may use an unsupported format — "
            "try re-running with --reporter=json and pass the results.json file instead."
        )

    failures: list[FailedTest] = []
    for file_info in main_report.get("files", []):
        file_name = file_info.get("fileName", "")
        for test in file_info.get("tests", []):
            if test.get("ok", True) and test.get("outcome") not in ("unexpected", "flaky"):
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


def parse_html_report(report_path: str) -> tuple[list[FailedTest], int, int]:
    p = Path(report_path)
    data_dir = _find_data_dir(p)

    if data_dir is None:
        if p.suffix in (".html", ".htm"):
            raise FileNotFoundError(
                f"Only found '{p.name}' — the test data is missing.\n"
                "\n"
                "For Playwright < 1.43, index.html is just the viewer; the actual data\n"
                "lives in data/ next to it. Your CI artifact is probably only uploading\n"
                "index.html and not the full playwright-report/ folder.\n"
                "\n"
                "Fix A — upload the full directory in your CI:\n"
                "\n"
                "    # GitHub Actions\n"
                "    - uses: actions/upload-artifact@v4\n"
                "      with:\n"
                "        name: playwright-report\n"
                "        path: playwright-report/      # <-- must be the folder, not index.html\n"
                "\n"
                "    Then download that artifact and run:\n"
                "        pw-insight --report playwright-report.zip --output report.html\n"
                "\n"
                "Fix B — add JSON reporter to playwright.config.ts (no CI change needed):\n"
                "\n"
                "    reporter: [['html'], ['json', { outputFile: 'playwright-report/results.json' }]]\n"
                "\n"
                "    Upload results.json as a CI artifact, download it, then run:\n"
                "        pw-insight --report results.json --output report.html"
            )
        raise FileNotFoundError(
            f"No data/ directory found in '{p}'. "
            "Point --report at the playwright-report/ folder, its index.html, "
            "a zip of that folder, or a results.json file."
        )

    return _parse_data_dir(data_dir)


def parse_zip_report(zip_path: str) -> tuple[list[FailedTest], int, int]:
    """Extract a zipped playwright-report/ artifact and parse it."""
    tmp = tempfile.mkdtemp(prefix="pw_insight_")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp)

        tmp_p = Path(tmp)

        # Common CI artifact layouts after extraction:
        #   tmp/data/*.zip                        (artifact uploaded from inside playwright-report/)
        #   tmp/playwright-report/data/*.zip      (artifact uploaded from project root)
        #   tmp/<any-dir>/data/*.zip              (any other nesting)
        for candidate in [tmp_p, *sorted(tmp_p.rglob("data"))]:
            data_dir = candidate if candidate.name == "data" else candidate / "data"
            if data_dir.is_dir() and any(data_dir.glob("*.zip")):
                return _parse_data_dir(data_dir)

        raise FileNotFoundError(
            "Could not find a data/ directory with Playwright report zips inside the archive.\n"
            "\n"
            "  Make sure the zip contains the full playwright-report/ folder, not just index.html.\n"
            "  In GitHub Actions, upload the artifact like this:\n"
            "\n"
            "      - uses: actions/upload-artifact@v4\n"
            "        with:\n"
            "          name: playwright-report\n"
            "          path: playwright-report/"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
