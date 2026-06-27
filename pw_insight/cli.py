from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

_VERSION = "1.0.0"
_SEP = "─" * 30


def _try_tqdm():
    try:
        from tqdm import tqdm
        return tqdm
    except ImportError:
        return None


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="pw-insight",
        description="Playwright test failure analyser — offline, no API keys.",
    )
    ap.add_argument("--report", required=True, help="Path to Playwright results.json")
    ap.add_argument("--repo", default=".", help="Git repository root (default: .)")
    ap.add_argument("--output", default="./pw-insight-report.html", help="Output HTML path")
    ap.add_argument("--limit", type=int, default=None, help="Cap number of failures to process")
    args = ap.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"Error: report file not found: {report_path}", file=sys.stderr)
        sys.exit(1)

    repo_path = str(Path(args.repo).resolve())

    print(f"pw-insight v{_VERSION}")
    print(_SEP)

    # Step 1 — parse
    print(f"→ Parsing {report_path.name}...", end=" ", flush=True)
    from pw_insight.parser import parse_results
    failures, passed, total = parse_results(str(report_path))
    print(f"{total:,} tests found")
    print(f"→ Extracting failures... {len(failures)} failed")

    if args.limit is not None:
        failures = failures[: args.limit]

    # Step 2 — git ownership
    print("→ Looking up git ownership...", end=" ", flush=True)
    from pw_insight.git_blame import build_ownership_cache
    unique_files = list({f.file for f in failures if f.file})
    ownership = build_ownership_cache(repo_path, unique_files)
    unique_authors = {v.name for v in ownership.values() if v.name != "Unknown"}
    print(f"done ({len(unique_authors)} unique authors)")

    # Step 3 & 4 — explain + categorise
    print("→ Explaining failures...", end=" ", flush=True)
    from pw_insight.explainer import explain
    from pw_insight.categoriser import categorise

    tqdm = _try_tqdm()
    iterable = tqdm(failures, desc="  processing", unit="test", leave=False) if tqdm else failures

    enriched: list[dict] = []
    for f in iterable:
        info = ownership.get(f.file)
        enriched.append({
            "file": f.file,
            "title": f.title,
            "full_title": f.full_title,
            "error_message": f.error_message,
            "owner": info.name if info else "Unknown",
            "email": info.email if info else "",
            "date": info.date if info else "",
            "reason": explain(f.error_message, f.stack_trace),
            "category": categorise(f.error_message, f.stack_trace),
        })

    print("done (local, instant)")

    # Step 5 — generate HTML
    print("→ Generating report...")
    from pw_insight.reporter import generate_report
    generate_report(enriched, passed, total, args.output)

    print(f"\n✓ Report ready: {args.output}\n")

    failed_count = len(enriched)
    fail_pct = (failed_count / total * 100) if total else 0.0
    pass_pct = 100.0 - fail_pct
    author_count = len({e["owner"] for e in enriched if e["owner"] != "Unknown"})
    cat_counts = Counter(e["category"] for e in enriched)
    top_cat, top_count = cat_counts.most_common(1)[0] if cat_counts else ("—", 0)

    print("Summary:")
    print(f"  Failed:  {failed_count:<6} ({fail_pct:.1f}%)")
    print(f"  Passed:  {passed:<6} ({pass_pct:.1f}%)")
    print(f"  Authors: {author_count}")
    print(f"  Top failure: {top_cat} ({top_count} tests)")


if __name__ == "__main__":
    main()
