"""Dedicated audit log for sensitive admin actions (incident toggles).

Separate from the observability log in app/logging_config.py: the audit
log is append-only, never scrubbed/rotated by the request pipeline, and
exists specifically to answer "who changed what control, and when" -
independent of whether tracing or request logging is enabled.

Schema (one JSON object per line):
    ts             ISO-8601 UTC timestamp of the action
    action         dotted action name, e.g. "incident.enable"
    target         the resource the action was applied to, e.g. "rag_slow"
    result         "ok" or "error"
    correlation_id request correlation ID that triggered the action, if any

Retention (documented policy for this lab; not auto-enforced by code):
    keep 90 days of audit records. In a real deployment this file would be
    rotated daily (e.g. data/audit-YYYY-MM-DD.jsonl) and a scheduled job
    would archive/delete files older than 90 days.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))
RETENTION_DAYS = 90


def record_audit_event(
    action: str,
    target: str,
    result: str,
    correlation_id: str | None = None,
) -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "target": target,
        "result": result,
        "correlation_id": correlation_id,
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
