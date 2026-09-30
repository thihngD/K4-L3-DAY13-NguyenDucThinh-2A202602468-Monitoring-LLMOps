"""Render the 6-panel dashboard contract (config/dashboard.yaml) as a static PNG.

Reads data/logs.jsonl (structured logs), computes the same aggregations
described in config/dashboard.yaml / docs/DASHBOARD_SETUP.md, and draws
them with matplotlib. This satisfies the lab's "script local tạo biểu đồ"
option — no external dashboard tool required.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"


def load_records() -> list[dict]:
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    return float(np.percentile(values, p))


def build_metrics(records: list[dict]) -> dict:
    received = [r for r in records if r.get("event") == "request_received"]
    responded = [r for r in records if r.get("event") == "response_sent"]
    failed = [r for r in records if r.get("event") == "request_failed"]

    latency = [r["latency_ms"] for r in responded if r.get("latency_ms") is not None]
    ttft = [r["ttft_ms"] for r in responded if r.get("ttft_ms") is not None]
    cost = [r["cost_usd"] for r in responded if r.get("cost_usd") is not None]
    tokens_in = [r["tokens_in"] for r in responded if r.get("tokens_in") is not None]
    tokens_out = [r["tokens_out"] for r in responded if r.get("tokens_out") is not None]
    quality = [r["quality_score"] for r in responded if r.get("quality_score") is not None]

    tool_records = [r for r in records if r.get("tool_success") is not None]
    tool_success = [r for r in tool_records if r["tool_success"] is True]

    total_received = len(received)
    total_failed = len(failed)
    error_rate_pct = (total_failed / total_received * 100) if total_received else 0.0
    retrieval_success_pct = (
        len(tool_success) / len(tool_records) * 100 if tool_records else 100.0
    )

    error_types: dict[str, int] = {}
    for r in failed:
        et = r.get("error_type", "unknown")
        error_types[et] = error_types.get(et, 0) + 1

    timestamps = [r["ts"] for r in received if r.get("ts")]
    minutes = sorted({ts[:16] for ts in timestamps})  # yyyy-mm-ddTHH:MM
    traffic_by_minute = {m: 0 for m in minutes}
    for ts in timestamps:
        traffic_by_minute[ts[:16]] += 1

    return {
        "latency_p50": percentile(latency, 50),
        "latency_p95": percentile(latency, 95),
        "latency_p99": percentile(latency, 99),
        "ttft_p95": percentile(ttft, 95),
        "traffic_by_minute": traffic_by_minute,
        "total_requests": total_received,
        "error_rate_pct": error_rate_pct,
        "retrieval_success_pct": retrieval_success_pct,
        "error_types": error_types,
        "cost_total": sum(cost),
        "tokens_in_total": sum(tokens_in),
        "tokens_out_total": sum(tokens_out),
        "quality_mean": (sum(quality) / len(quality)) if quality else 0.0,
    }


def threshold_line(ax, panel: dict, value_for_label: str) -> None:
    th = panel.get("threshold") or {}
    if "value" not in th:
        return
    ax.axhline(th["value"], color="crimson", linestyle="--", linewidth=1.2)
    ax.text(
        0.99,
        th["value"],
        f"SLO {th['operator']} {th['value']} ({value_for_label})",
        color="crimson",
        fontsize=7,
        ha="right",
        va="bottom",
        transform=ax.get_yaxis_transform(),
    )


def render(metrics: dict, dashboard_cfg: dict, out_path: Path) -> None:
    panels = {p["id"]: p for p in dashboard_cfg["panels"]}
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle(
        f"{dashboard_cfg['title']} — time_range={dashboard_cfg['time_range_minutes']}m, "
        f"refresh={dashboard_cfg['refresh_seconds']}s — generated {generated_at}\n"
        f"Source: data/logs.jsonl ({metrics['total_requests']} request_received)",
        fontsize=11,
    )

    # 1. Latency
    ax = axes[0, 0]
    p = panels["latency"]
    labels = ["p50", "p95", "p99", "ttft_p95"]
    values = [metrics["latency_p50"], metrics["latency_p95"], metrics["latency_p99"], metrics["ttft_p95"]]
    ax.bar(labels, values, color=["#4c78a8", "#f58518", "#e45756", "#72b7b2"])
    ax.set_title(f"{p['title']} ({p['unit']})")
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.0f}", ha="center", va="bottom", fontsize=8)
    threshold_line(ax, p, "p95")

    # 2. Traffic
    ax = axes[0, 1]
    p = panels["traffic"]
    tbm = metrics["traffic_by_minute"]
    if tbm:
        mins = list(tbm.keys())
        counts = list(tbm.values())
        ax.plot(range(len(mins)), counts, marker="o", color="#4c78a8")
        ax.set_xticks(range(len(mins)))
        ax.set_xticklabels([m[-5:] for m in mins], rotation=45, fontsize=7)
    ax.set_title(f"{p['title']} ({p['unit']})")
    threshold_line(ax, p, "rate_per_minute")

    # 3. Errors
    ax = axes[0, 2]
    p = panels["errors"]
    ax.bar(
        ["error_rate_pct", "retrieval_success_pct"],
        [metrics["error_rate_pct"], metrics["retrieval_success_pct"]],
        color=["#e45756", "#54a24b"],
    )
    ax.set_title(f"{p['title']} ({p['unit']})")
    for i, v in enumerate([metrics["error_rate_pct"], metrics["retrieval_success_pct"]]):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
    threshold_line(ax, p, "error_rate_pct")

    # 4. Cost
    ax = axes[1, 0]
    p = panels["cost"]
    ax.bar(["total"], [metrics["cost_total"]], color="#f58518")
    ax.text(0, metrics["cost_total"], f"${metrics['cost_total']:.4f}", ha="center", va="bottom", fontsize=8)
    ax.set_title(f"{p['title']} ({p['unit']})")
    threshold_line(ax, p, "total")

    # 5. Tokens
    ax = axes[1, 1]
    p = panels["tokens"]
    ax.bar(
        ["tokens_in", "tokens_out"],
        [metrics["tokens_in_total"], metrics["tokens_out_total"]],
        color=["#72b7b2", "#b279a2"],
    )
    for i, v in enumerate([metrics["tokens_in_total"], metrics["tokens_out_total"]]):
        ax.text(i, v, f"{v}", ha="center", va="bottom", fontsize=8)
    ax.set_title(f"{p['title']} ({p['unit']})")
    threshold_line(ax, p, "sum_by_field")

    # 6. Quality
    ax = axes[1, 2]
    p = panels["quality"]
    ax.bar(["mean"], [metrics["quality_mean"]], color="#54a24b")
    ax.set_ylim(0, 1)
    ax.text(0, metrics["quality_mean"], f"{metrics['quality_mean']:.2f}", ha="center", va="bottom", fontsize=8)
    ax.set_title(f"{p['title']} ({p['unit']})")
    threshold_line(ax, p, "mean")

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f"Saved dashboard to {out_path}")
    print(json.dumps(metrics, ensure_ascii=False, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="submission/evidence/11-dashboard-overview.png")
    args = parser.parse_args()

    records = load_records()
    metrics = build_metrics(records)
    dashboard_cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
    render(metrics, dashboard_cfg, REPO_ROOT / args.out)


if __name__ == "__main__":
    main()
