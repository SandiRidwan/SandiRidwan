#!/usr/bin/env python3
"""Prep a profile photo for ASCII conversion.

Downsamples the source avatar and boosts local contrast so a flatly-lit face
still separates into the ASCII density ramp. Keeps the subject on a white
background so bright areas map to the blank end of the ramp.

Usage:
    python scripts/prep_photo.py source-photo.jpg
    python scripts/prep_photo.py --url https://github.com/SandiRidwan.png

Output:
    source-prepped.png  (grayscale, high local contrast)
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def load_image(src: str) -> np.ndarray:
    """Load from a local path or an http(s) URL into a BGR ndarray."""
    if src.startswith(("http://", "https://")):
        with urllib.request.urlopen(src) as resp:
            buf = np.frombuffer(resp.read(), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    else:
        img = cv2.imread(src, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"Could not read image: {src}")
    return img


def remove_background(img: np.ndarray) -> np.ndarray:
    """Isolate the subject with rembg if it is installed; otherwise passthrough."""
    try:
        from rembg import remove  # type: ignore
    except Exception:
        print("[prep] rembg not installed -> keeping original background", file=sys.stderr)
        return img
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    cut = remove(Image.fromarray(rgb))
    if cut.mode == "RGBA":
        # Composite onto pure white so background -> blank ASCII glyphs.
        white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
        cut = Image.alpha_composite(white, cut).convert("RGB")
    return cv2.cvtColor(np.array(cut), cv2.COLOR_RGB2BGR)


def boost_contrast(gray: np.ndarray) -> np.ndarray:
    """CLAHE gives a flat face real highlights and shadows."""
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)


def detect_faces(img: np.ndarray) -> list:
    """Haar face detection when available; empty list otherwise.

    opencv-python-headless has no CascadeClassifier / cv2.data, so this degrades
    gracefully to a center crop rather than crashing.
    """
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(cascade_path)
        if cascade.empty():
            return []
        gray0 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray0, 1.1, 6, minSize=(60, 60))
        return list(faces)
    except AttributeError:
        return []


def center_crop(img: np.ndarray, frac: float) -> np.ndarray:
    """Crop the central `frac` of width and height — a face-ish framing fallback."""
    h, w = img.shape[:2]
    nw, nh = int(w * frac), int(h * frac)
    x0, y0 = (w - nw) // 2, (h - nh) // 2
    return img[y0:y0 + nh, x0:x0 + nw]


def main() -> None:
    ap = argparse.ArgumentParser(description="Prep a photo for ASCII conversion")
    ap.add_argument("source", nargs="?", help="path to the source photo")
    ap.add_argument("--url", help="download the source from this URL instead")
    ap.add_argument("--crop", default="center",
                    help="'center' (default) or 'face' if a face is detected")
    ap.add_argument("-o", "--output", default="source-prepped.png")
    args = ap.parse_args()

    src = args.url or args.source
    if not src:
        raise SystemExit("Provide a photo path or --url")

    img = load_image(src)
    img = remove_background(img)

    if args.crop == "face":
        faces = detect_faces(img)
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            pad = int(0.45 * w)
            x0, y0 = max(0, x - pad), max(0, y - pad)
            x1, y1 = min(img.shape[1], x + w + pad), min(img.shape[0], y + h + pad)
            img = img[y0:y1, x0:x1]
            print(f"[prep] face crop -> {w}x{h} region")
        else:
            print("[prep] face detector unavailable/none -> center crop", file=sys.stderr)
            img = center_crop(img, 0.82)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = boost_contrast(gray)
    cv2.imwrite(args.output, gray)
    print(f"[prep] wrote {args.output} ({gray.shape[1]}x{gray.shape[0]})")


if __name__ == "__main__":
    main()
