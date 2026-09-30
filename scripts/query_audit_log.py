"""Example query over the audit log (bonus: audit log riêng - truy vấn minh họa).

Usage:
    python scripts/query_audit_log.py                      # show all
    python scripts/query_audit_log.py --action incident.enable
    python scripts/query_audit_log.py --target rag_slow --result ok
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

AUDIT_LOG_PATH = Path("data/audit.jsonl")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", help="Filter by exact action, e.g. incident.enable")
    parser.add_argument("--target", help="Filter by target, e.g. rag_slow")
    parser.add_argument("--result", choices=["ok", "error"], help="Filter by result")
    args = parser.parse_args()

    if not AUDIT_LOG_PATH.exists():
        print(f"No audit log at {AUDIT_LOG_PATH} yet. Trigger an incident enable/disable first.")
        return

    matched = 0
    for line in AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if args.action and record.get("action") != args.action:
            continue
        if args.target and record.get("target") != args.target:
            continue
        if args.result and record.get("result") != args.result:
            continue
        print(json.dumps(record, ensure_ascii=False))
        matched += 1

    print(f"\n{matched} matching audit record(s).")


if __name__ == "__main__":
    main()
