"""Render a block of terminal text as a PNG "screenshot" for evidence.

Some evidence items (pytest, validators) are plain CLI output. Rather than
saving raw .txt, this renders the exact text into an image that looks like a
terminal capture, so submission/evidence/*.png always contains a real image
with the required content visible.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render(text: str, out_path: Path, title: str | None = None) -> None:
    lines = text.splitlines() or [""]
    font_size = 13
    char_width = font_size * 0.62 / 72  # inches, monospace approx
    line_height = font_size * 1.55 / 72  # inches
    padding = 0.35
    max_len = max((len(l) for l in lines), default=0)
    width = max(6.5, max_len * char_width + padding * 2 + 0.3)
    height = len(lines) * line_height + padding * 2 + (0.4 if title else 0)

    fig = plt.figure(figsize=(width, height), facecolor="#1e1e1e")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_facecolor("#1e1e1e")
    ax.axis("off")

    x = padding / width
    y = 1 - padding / height
    if title:
        ax.text(
            x,
            y,
            title,
            transform=ax.transAxes,
            color="#9cdcfe",
            fontsize=font_size + 1,
            fontfamily="monospace",
            fontweight="bold",
            va="top",
        )
        y -= (line_height + 0.1) / height

    body = "\n".join(lines)
    ax.text(
        x,
        y,
        body,
        transform=ax.transAxes,
        color="#d4d4d4",
        fontsize=font_size,
        fontfamily="monospace",
        va="top",
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default=None)
    parser.add_argument("--file", help="Read text from this file instead of stdin")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    render(text, Path(args.out), args.title)


if __name__ == "__main__":
    main()
