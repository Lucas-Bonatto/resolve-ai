"""Fail CI on high-confidence secrets in tracked text files without printing values."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "openai_key": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "github_token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "jwt": re.compile(rb"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> None:
    findings: list[tuple[str, str]] = []
    files = tracked_files()
    for path in files:
        try:
            content = path.read_bytes()
        except OSError:
            continue
        if b"\0" in content:
            continue
        for rule, pattern in PATTERNS.items():
            if pattern.search(content):
                findings.append((path.relative_to(ROOT).as_posix(), rule))

    if findings:
        for filename, rule in findings:
            print(f"SECRET_SCAN_FAIL file={filename} rule={rule}")
        raise SystemExit(1)
    print(f"SECRET_SCAN_PASS tracked_files={len(files)} findings=0")


if __name__ == "__main__":
    main()
