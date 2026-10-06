#!/usr/bin/env python3
"""Hand-author a neofetch-style info-card SVG for the profile.

A title bar plus colored key/value rows that fade in line by line, so the panel
looks like it is printing next to the ASCII portrait. Keep the story here, not
the GitHub stats (the contribution graph covers those).

Usage:
    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py   # frozen frame for preview

Edit the ROWS list below to change the content.
"""
from __future__ import annotations

import os
from pathlib import Path

# (key, value, value-color). Keep it tight — this is the story, not a résumé.
ROWS: list[tuple[str, str, str]] = [
    ("Now", "Data Analyst @ Automation Architect"),
    ("Prev", "Web-scraping & anti-bot engineer"),
    ("Stack", "Python · DuckDB/SQL · pandas · FastAPI"),
    ("", "Playwright · Docker · Streamlit · AWS"),
    ("Focus", "Data pipelines that never sleep"),
    ("Live", "ab-testing-lab.streamlit.app"),
    ("", "geo-access-atlas...streamlit.app"),
    ("Note", "Insight + Recommendation + Risk per chart"),
]

ACCENT = "#00FF9C"
KEY_COLOR = "#58a6ff"
VAL_COLOR = "#c9d1d9"
BG = "#0d1117"
TITLE = "sandi@sandiridwan"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_svg() -> str:
    static = os.environ.get("STATIC") == "1"
    font = 14.0
    pad = 18.0
    line_h = 22.0
    title_h = 30.0
    width = 490.0
    height = pad * 2 + title_h + len(ROWS) * line_h
    key_x = pad
    val_x = pad + 76

    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )
    p.append(f'<rect width="100%" height="100%" rx="8" fill="{BG}"/>')
    p.append(f'<rect width="100%" height="100%" rx="8" fill="none" '
             f'stroke="{ACCENT}" stroke-opacity="0.35"/>')

    # title bar
    p.append(f'<circle cx="{pad}" cy="{pad + 10:.0f}" r="4" fill="#ff5f56"/>')
    p.append(f'<circle cx="{pad + 14}" cy="{pad + 10:.0f}" r="4" fill="#ffbd2e"/>')
    p.append(f'<circle cx="{pad + 28}" cy="{pad + 10:.0f}" r="4" fill="#27c93f"/>')
    p.append(
        f'<text x="{width - pad:.0f}" y="{pad + 15:.0f}" font-size="12" '
        f'fill="{ACCENT}" text-anchor="end">{TITLE}</text>'
    )
    p.append(f'<line x1="{pad}" y1="{pad + title_h:.0f}" x2="{width - pad:.0f}" '
             f'y2="{pad + title_h:.0f}" stroke="{ACCENT}" stroke-opacity="0.3"/>')

    for i, (key, val, *_rest) in enumerate(ROWS):
        y = pad + title_h + (i + 1) * line_h - 6
        begin = 0.15 * i
        anim = ("" if static else
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="0.35s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-14 0" to="0 0" begin="{begin:.2f}s" dur="0.35s" '
                f'fill="freeze"/>')
        p.append(f'<g opacity="{1 if static else 0}">{anim}')
        if key:
            p.append(f'<text x="{key_x:.0f}" y="{y:.0f}" font-size="{font:.0f}" '
                     f'fill="{KEY_COLOR}">{esc(key)}</text>')
            p.append(f'<text x="{key_x + 56:.0f}" y="{y:.0f}" font-size="{font:.0f}" '
                     f'fill="{ACCENT}">:</text>')
        p.append(f'<text x="{val_x:.0f}" y="{y:.0f}" font-size="{font:.0f}" '
                 f'fill="{VAL_COLOR}">{esc(val)}</text>')
        p.append("</g>")

    p.append("</svg>")
    return "\n".join(p)


def main() -> None:
    out = Path("info-card.svg")
    out.write_text(make_svg(), encoding="utf-8")
    print(f"[info-card] wrote {out}")


if __name__ == "__main__":
    main()
