#!/usr/bin/env python3
"""Convert a prepped grayscale photo into a self-typing monochrome ASCII SVG.

The portrait is drawn row by row; each row is revealed by a horizontal clip
that wipes left-to-right, staggered top to bottom, with a small block "cursor"
riding the wipe edge. It prints once and freezes — SMIL inside the SVG, which
GitHub renders even though it strips <script> and most inline CSS.

Usage:
    python scripts/make_ascii_svg.py source-prepped.png
    python scripts/make_ascii_svg.py source-prepped.png -o sandi-ascii.svg

Options:
    --cols      character columns            (default 100)
    --color     single fill color            (default #00FF9C)
    --font      font-size in px              (default 9)
    --row-delay per-row stagger in seconds   (default 0.05)
    --width     total seconds for the wipe   (default 0.6)
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps

# bright (sparse) -> dark (dense). Leading space clears the background to nothing.
RAMP = " .`:-=+*cs#%@"


def build_rows(image_path: str, cols: int) -> list[str]:
    img = Image.open(image_path).convert("L")
    w, h = img.size
    # Character cells are ~2x taller than wide, so double the row count.
    rows = max(1, int(cols * (h / w) * 0.5))
    small = img.resize((cols, rows), Image.LANCZOS)
    # Autocontrast keeps the ramp well used regardless of source exposure.
    small = ImageOps.autocontrast(small, cutoff=1)
    px = small.load()
    out: list[str] = []
    span = len(RAMP) - 1
    for y in range(rows):
        line = []
        for x in range(cols):
            v = px[x, y]
            # 0 = black -> dense glyph; 255 = white -> leading space.
            idx = int((v / 255.0) * span)
            line.append(RAMP[idx])
        out.append("".join(line).rstrip())
    return out


def escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def make_svg(rows: list[str], color: str, font: float, row_delay: float,
             wipe: float) -> str:
    line_h = font * 1.0
    char_w = font * 0.6
    pad = font * 2
    max_len = max((len(r) for r in rows), default=0)
    width = pad * 2 + max_len * char_w
    height = pad * 2 + len(rows) * line_h

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="#0d1117"/>')

    for i, row in enumerate(rows):
        y = pad + (i + 1) * line_h - font * 0.25
        begin = i * row_delay
        row_w = len(row) * char_w + char_w
        clip_id = f"clip{i}"
        parts.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{pad:.1f}" y="{y - line_h:.1f}" width="0" height="{line_h:.1f}">'
            f'<animate attributeName="width" from="0" to="{row_w:.1f}" '
            f'begin="{begin:.3f}s" dur="{wipe:.3f}s" fill="freeze"/>'
            f'</rect></clipPath>'
        )
        parts.append(
            f'<text x="{pad:.1f}" y="{y:.1f}" font-size="{font:.1f}" '
            f'fill="{color}" clip-path="url(#{clip_id})" '
            f'xml:space="preserve" opacity="0">'
            f'{escape(row)}'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin:.3f}s" dur="0.001s" fill="freeze"/>'
            f'</text>'
        )
        # block cursor riding the wipe edge
        parts.append(
            f'<rect x="{pad:.1f}" y="{y - line_h:.1f}" width="{char_w:.1f}" '
            f'height="{line_h:.1f}" fill="{color}" opacity="0">'
            f'<animate attributeName="x" from="{pad:.1f}" to="{pad + row_w:.1f}" '
            f'begin="{begin:.3f}s" dur="{wipe:.3f}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0;0.9;0" '
            f'begin="{begin:.3f}s" dur="{wipe:.3f}s" fill="freeze"/>'
            f'</rect>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(description="Grayscale photo -> self-typing ASCII SVG")
    ap.add_argument("image", help="path to the prepped grayscale image")
    ap.add_argument("-o", "--output", default="sandi-ascii.svg")
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--color", default="#00FF9C")
    ap.add_argument("--font", type=float, default=9.0)
    ap.add_argument("--row-delay", type=float, default=0.05)
    ap.add_argument("--width", type=float, default=0.6, dest="wipe")
    args = ap.parse_args()

    if not Path(args.image).exists():
        raise SystemExit(f"Missing {args.image} (run prep_photo.py first)")
    rows = build_rows(args.image, args.cols)
    svg = make_svg(rows, args.color, args.font, args.row_delay, args.wipe)
    Path(args.output).write_text(svg, encoding="utf-8")
    print(f"[ascii] wrote {args.output} ({len(rows)} rows x {args.cols} cols)")


if __name__ == "__main__":
    main()
