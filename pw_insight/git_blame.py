from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class OwnerInfo:
    name: str
    email: str
    date: str


_UNKNOWN = OwnerInfo(name="Unknown", email="", date="")


def _run_git(repo_path: str, file_path: str) -> OwnerInfo:
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "log", "--follow", "-1", "--format=%an|%ae|%ad", "--", file_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        line = result.stdout.strip()
        if not line:
            return _UNKNOWN
        parts = line.split("|", 2)
        if len(parts) < 3:
            return _UNKNOWN
        return OwnerInfo(name=parts[0] or "Unknown", email=parts[1], date=parts[2])
    except Exception:
        return _UNKNOWN


def build_ownership_cache(repo_path: str, file_paths: list[str]) -> dict[str, OwnerInfo]:
    cache: dict[str, OwnerInfo] = {}
    for fp in file_paths:
        if fp not in cache:
            cache[fp] = _run_git(repo_path, fp)
    return cache
