"""Pre-commit style scan for leaked API keys/secrets and raw PII in source.

Bonus automation (docs/RUBRIC.md section H): catches the exact class of
mistake found manually during this lab (a Langfuse public_key visible in a
trace-metadata screenshot) before it reaches a commit.

Usage:
    python scripts/scan_secrets.py
Exit code 0 = clean, 1 = findings printed to stdout.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.pii import PII_PATTERNS

SECRET_PATTERNS: dict[str, str] = {
    "langfuse_secret_key": r"sk-lf-[a-zA-Z0-9-]{8,}",
    "langfuse_public_key": r"pk-lf-[a-zA-Z0-9-]{8,}",
    "generic_aws_key": r"AKIA[0-9A-Z]{16}",
    "generic_bearer_token": r"(?i)bearer\s+[a-zA-Z0-9._-]{20,}",
}

TEXT_EXTENSIONS = {
    ".py", ".md", ".yaml", ".yml", ".json", ".txt", ".env", ".cfg", ".ini",
}

# Test fixtures and evidence-capture notes intentionally contain fake PII
# samples; only scan them for real secrets, not for the PII patterns they
# exist to exercise.
PII_SCAN_EXCLUDES = {REPO_ROOT / "tests", REPO_ROOT / "docs" / "CP4.md"}

ALWAYS_EXCLUDE_DIRS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", ".antigravity",
}


def iter_text_files() -> list[Path]:
    files = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ALWAYS_EXCLUDE_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        # config/challenge.json and .env are gitignored on purpose; scanning
        # them locally is still useful (catches accidental force-add later).
        files.append(path)
    return files


def scan_file(path: Path) -> list[str]:
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    for name, pattern in SECRET_PATTERNS.items():
        for match in re.finditer(pattern, text):
            findings.append(f"[SECRET:{name}] {path.relative_to(REPO_ROOT)} -> {match.group(0)[:12]}...")

    if not any(path.is_relative_to(excluded) for excluded in PII_SCAN_EXCLUDES):
        for name, pattern in PII_PATTERNS.items():
            for match in re.finditer(pattern, text):
                findings.append(f"[PII:{name}] {path.relative_to(REPO_ROOT)} -> {match.group(0)}")

    return findings


def main() -> None:
    all_findings: list[str] = []
    for path in iter_text_files():
        all_findings.extend(scan_file(path))

    if all_findings:
        print("--- Secret/PII scan: FOUND ISSUES ---")
        for line in all_findings:
            print(line)
        print(f"\n{len(all_findings)} finding(s). Fix before committing.")
        sys.exit(1)

    print("--- Secret/PII scan: clean ---")
    print("No API keys, tokens, or raw PII detected in tracked text files.")


if __name__ == "__main__":
    main()
