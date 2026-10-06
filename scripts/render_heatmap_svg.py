#!/usr/bin/env python3
"""Render data/contributions.json as an animated contribution-heatmap SVG.

Classic 53-week x 7-day calendar of rounded boxes that slide in diagonally,
then freeze (no looping). Green ramp with a neon top end, a Less->More legend,
and a stats footer. Pure SVG/CSS animation — GitHub renders it, no JS.

Usage:
    python scripts/render_heatmap_svg.py
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
ACCENT = "#00FF9C"
BG = "#0d1117"

CELL = 12.0
GAP = 3.0
TOP_PAD = 46.0
LEFT_PAD = 34.0
BOTTOM_PAD = 40.0


def level_color(level: int) -> str:
    return PALETTE[max(0, min(level, len(PALETTE) - 1))]


def build_svg(data: dict) -> str:
    days = data["days"]
    by_date = {d["date"]: d for d in days}
    stats = data["stats"]

    start = dt.date.fromisoformat(stats["start"])
    end = dt.date.fromisoformat(stats["end"])
    # Align to the Sunday on or before the start.
    grid_start = start - dt.timedelta(days=(start.weekday() + 1) % 7)
    weeks = ((end - grid_start).days // 7) + 1

    width = LEFT_PAD + weeks * (CELL + GAP) + 20
    height = TOP_PAD + 7 * (CELL + GAP) + BOTTOM_PAD

    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )
    p.append(f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>')

    # header
    p.append(
        f'<text x="{LEFT_PAD:.0f}" y="26" font-size="15" fill="{ACCENT}">'
        f'{stats["total"]:,} contributions in the last year</text>'
    )
    p.append(
        f'<text x="{width - 20:.0f}" y="26" font-size="11" fill="#8b949e" '
        f'text-anchor="end">{stats["start"]} → {stats["end"]}</text>'
    )

    # weekday labels (Mon / Wed / Fri)
    for idx, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = TOP_PAD + idx * (CELL + GAP) + CELL * 0.75
        p.append(f'<text x="6" y="{y:.0f}" font-size="9" fill="#8b949e">{label}</text>')

    # cells with a diagonal reveal (stagger by week+day)
    for week in range(weeks):
        for wd in range(7):
            day = grid_start + dt.timedelta(days=week * 7 + wd)
            if day > end or day < start:
                continue
            info = by_date.get(day.isoformat())
            lvl = info["level"] if info else 0
            x = LEFT_PAD + week * (CELL + GAP)
            y = TOP_PAD + wd * (CELL + GAP)
            begin = (week + wd) * 0.006
            p.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL:.1f}" '
                f'height="{CELL:.1f}" rx="2.5" fill="{level_color(lvl)}" '
                f'opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.3f}s" dur="0.30s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="0 -6" to="0 0" begin="{begin:.3f}s" dur="0.30s" '
                f'fill="freeze"/>'
                f'</rect>'
            )

    # legend
    legend_y = TOP_PAD + 7 * (CELL + GAP) + 12
    lx = width - 20 - 5 * (CELL + GAP) - 46
    p.append(f'<text x="{lx - 6:.0f}" y="{legend_y + CELL * 0.8:.0f}" '
             f'font-size="10" fill="#8b949e" text-anchor="end">Less</text>')
    for i in range(5):
        x = lx + i * (CELL + GAP)
        p.append(f'<rect x="{x:.1f}" y="{legend_y:.1f}" width="{CELL:.1f}" '
                 f'height="{CELL:.1f}" rx="2.5" fill="{PALETTE[i]}"/>')
    p.append(f'<text x="{lx + 5 * (CELL + GAP) + 2:.0f}" '
             f'y="{legend_y + CELL * 0.8:.0f}" font-size="10" fill="#8b949e">More</text>')

    # stats footer
    p.append(
        f'<text x="{LEFT_PAD:.0f}" y="{legend_y + CELL * 0.8:.0f}" '
        f'font-size="10" fill="#c9d1d9">'
        f'current {stats["current_streak"]}d · longest {stats["longest_streak"]}d · '
        f'best {stats["best_day"]["count"]} ({stats["best_day"]["date"]})</text>'
    )

    p.append("</svg>")
    return "\n".join(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", default="data/contributions.json")
    ap.add_argument("-o", "--output", default="contrib-heatmap.svg")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    Path(args.output).write_text(build_svg(data), encoding="utf-8")
    print(f"[heatmap] wrote {args.output}")


if __name__ == "__main__":
    main()
