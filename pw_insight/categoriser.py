from __future__ import annotations

import re

_RULES: list[tuple[str, str]] = [
    (r"timeout|timed out", "Timeout"),
    (r"tobevisible|not visible|locator.*not found|no element", "Element Not Found"),
    (r"expect|tobe|tohave|tocontain|toequal", "Assertion Failed"),
    (r"net::|econnrefused|err_name|navigation.*timeout", "Network Error"),
    (r"401|403|unauthorized|forbidden", "Auth Error"),
    (r"500|server error|internal error", "Server Error"),
    (r"typeerror|cannot read|undefined is not|null is not", "JS Error"),
    (r"screenshot|visual|image.*diff", "Visual Diff"),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), c) for p, c in _RULES]


def categorise(error_message: str, stack_trace: str) -> str:
    combined = error_message + " " + stack_trace
    for pattern, category in _COMPILED:
        if pattern.search(combined):
            return category
    return "Other"
