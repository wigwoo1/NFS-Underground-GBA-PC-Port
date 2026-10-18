#!/usr/bin/env python3
"""Create a review-only 3240x2160 menu image with clean, high-resolution labels.

The captured screen supplies the background and exact source identity. This tool
removes only the known label glyphs, fills their small source-resolution holes
with a harmonic neighborhood estimate, enlarges the background, and rerenders
the text with an antialiased font. It does not claim to regenerate the bezel,
logo, or other game artwork.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from texture_hash import source_hash

WIDTH, HEIGHT = 3240, 2160
SCALE = WIDTH / 240.0
FONT_DEFAULT = Path(r"C:\Windows\Fonts\arialbi.ttf")

# Each row gives text, the detection window in source pixels, and role.
LAYOUTS = {
    "main-menu": {
        "header": ("MAIN MENU", (55, 15, 190, 31), "yellow"),
        "rows": [
            ("QUICK RACE", (35, 36, 190, 51), "ink"),
            ("GO UNDERGROUND", (35, 53, 190, 66), "ink"),
            ("MULTIPLAYER MODE", (35, 69, 190, 83), "ink"),
            ("CUSTOMIZE CAR", (35, 86, 190, 100), "ink"),
        ],
    },
    "quick-race": {
        "header": ("QUICK RACE", (55, 15, 190, 31), "yellow"),
        "rows": [
            ("CIRCUIT", (35, 36, 190, 51), "ink"),
            ("SPRINT", (35, 53, 190, 66), "ink"),
            ("DRAG", (35, 69, 190, 83), "ink"),
            ("DRIFT", (35, 86, 190, 100), "ink"),
        ],
    },
    "pause": {
        "header": ("PAUSED", (50, 15, 190, 31), "yellow"),
        "rows": [
            ("CONTINUE", (35, 37, 145, 51), "ink"),
            ("QUIT", (35, 53, 110, 66), "ink"),
            ("SETTINGS", (35, 69, 145, 83), "ink"),
            ("AUDIO", (35, 85, 135, 99), "ink"),
        ],
    },
    "game-options": {
        "header": ("GAME OPTIONS", (50, 15, 190, 31), "yellow"),
        "rows": [
            ("CAMERA", (35, 37, 120, 51), "ink"),
            ("UNITS", (35, 53, 115, 66), "ink"),
            ("HUD", (35, 69, 110, 83), "ink"),
        ],
        "extras": [
            ("CHASE", (145, 37, 202, 51), "yellow"),
            ("MPH", (150, 53, 202, 66), "yellow"),
            ("ON", (165, 69, 202, 83), "yellow"),
        ],
    },
    "audio-options": {
        "header": ("AUDIO OPTIONS", (50, 15, 190, 31), "yellow"),
        "rows": [
            ("MUSIC", (35, 37, 95, 51), "ink"),
            ("SFX", (35, 53, 95, 66), "ink"),
        ],
    },
}

def _dilate(mask: np.ndarray) -> np.ndarray:
    padded = np.pad(mask, 1, mode="constant")
    out = np.zeros_like(mask)
    for dy in range(3):
        for dx in range(3):
            out |= padded[dy : dy + mask.shape[0], dx : dx + mask.shape[1]]
    return out


def _glyph_mask(image: np.ndarray, box: tuple[int, int, int, int], role: str) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    x0, y0, x1, y1 = box
    crop = image[y0:y1, x0:x1, :3]
    r, g, b = crop[..., 0], crop[..., 1], crop[..., 2]
    if role == "yellow":
        local = (r > 160) & (g > 110) & (b < 120) & ((r.astype(np.int16) - b) > 90)
    else:
        local = (r < 95) & (g < 120) & (b < 135)
    if int(local.sum()) < 12:
        raise ValueError(f"Could not identify expected {role} label in source region {box}")
    ys, xs = np.nonzero(local)
    tight = (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1)
    expanded = _dilate(local)
    mask = np.zeros(image.shape[:2], dtype=bool)
    mask[y0:y1, x0:x1] = expanded
    return mask, tight


def _harmonic_inpaint(image: np.ndarray, mask: np.ndarray, iterations: int = 256) -> np.ndarray:
    work = image.astype(np.float32)
    fixed = image.astype(np.float32)
    for _ in range(iterations):
        padded = np.pad(work, ((1, 1), (1, 1), (0, 0)), mode="edge")
        avg = (
            padded[:-2, 1:-1] + padded[2:, 1:-1]
            + padded[1:-1, :-2] + padded[1:-1, 2:]
        ) * 0.25
        work[mask] = avg[mask]
        work[~mask] = fixed[~mask]
    return np.clip(work + 0.5, 0, 255).astype(np.uint8)


def _render_label(
    canvas: Image.Image,
    text: str,
    source_box: tuple[int, int, int, int],
    role: str,
    font_path: Path,
) -> None:
    sx0, sy0, sx1, sy1 = source_box
    x0 = max(0, int(round((sx0 - 1) * SCALE)))
    y0 = max(0, int(round((sy0 - 1) * SCALE)))
    x1 = min(WIDTH, int(round((sx1 + 1) * SCALE)))
    y1 = min(HEIGHT, int(round((sy1 + 1) * SCALE)))
    box_w, box_h = x1 - x0, y1 - y0
    pad_x = max(6, round(box_w * 0.012))
    pad_y = max(5, round(box_h * 0.07))
    fit_w, fit_h = max(1, box_w - 2 * pad_x), max(1, box_h - 2 * pad_y)

    font = ImageFont.truetype(str(font_path), max(24, int(box_h * 1.45)))
    scratch = Image.new("RGBA", (1, 1))
    bounds = ImageDraw.Draw(scratch).textbbox((0, 0), text, font=font, stroke_width=0)
    glyph = Image.new("RGBA", (max(1, bounds[2] - bounds[0]), max(1, bounds[3] - bounds[1])), (255, 255, 255, 0))
    ImageDraw.Draw(glyph).text((-bounds[0], -bounds[1]), text, font=font, fill=(255, 255, 255, 255))
    glyph = glyph.resize((fit_w, fit_h), Image.Resampling.LANCZOS)

    if role == "yellow":
        ink, shadow = (247, 229, 15, 255), (78, 63, 0, 190)
        dx, dy = max(2, round(SCALE * 0.22)), max(2, round(SCALE * 0.28))
    else:
        ink, shadow = (15, 29, 37, 255), (59, 89, 95, 150)
        dx, dy = max(2, round(SCALE * 0.18)), max(2, round(SCALE * 0.22))

    layer = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    alpha = glyph.getchannel("A")
    shade = Image.new("RGBA", glyph.size, shadow)
    shade.putalpha(alpha.point(lambda a: (a * shadow[3]) // 255))
    layer.alpha_composite(shade, (min(dx, box_w - 1), min(dy, box_h - 1)))
    face = Image.new("RGBA", glyph.size, ink)
    face.putalpha(alpha)
    layer.alpha_composite(face, (0, 0))
    canvas.alpha_composite(layer, (x0, y0))


def remaster(screen: str, source_path: Path, output_path: Path, font_path: Path) -> dict:
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite review candidate: {output_path}")
    if screen not in LAYOUTS:
        raise ValueError(f"Unsupported screen layout: {screen}")
    with Image.open(source_path) as loaded:
        rgba = loaded.convert("RGBA")
    if rgba.size != (240, 160):
        raise ValueError(f"Expected a 240x160 captured source, got {rgba.size}")
    src = np.asarray(rgba, dtype=np.uint8)
    source_alpha = src[..., 3]
    if not np.all(source_alpha == source_alpha[0, 0]):
        raise ValueError("Full-screen UI source must have uniform alpha; variable-alpha overlays need a separate path")
    masks: list[np.ndarray] = []
    labels: list[tuple[str, tuple[int, int, int, int], str]] = []
    config = LAYOUTS[screen]
    for text, region, role in [config["header"], *config["rows"], *config.get("extras", [])]:
        mask, tight = _glyph_mask(src, region, role)
        masks.append(mask)
        labels.append((text, tight, role))

    clean = _harmonic_inpaint(src[..., :3], np.logical_or.reduce(masks))
    background = Image.fromarray(clean, "RGB").convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    for text, box, role in labels:
        _render_label(background, text, box, role, font_path)
    # Captured full-screen frames use a constant non-opaque alpha byte (40 in
    # the pause/options captures). Preserve it at every upscaled pixel so the
    # exact source-bound replacement remains faithful to the capture format.
    alpha = Image.fromarray(source_alpha, "L").resize((WIDTH, HEIGHT), Image.Resampling.NEAREST)
    background.putalpha(alpha)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    background.save(output_path, optimize=True)
    digest = source_hash(rgba.tobytes(), 240, 160)
    return {
        "screen": screen,
        "source": str(source_path),
        "source_hash": f"{digest:016x}",
        "upscaled": str(output_path),
        "dimensions": list(background.size),
        "font": str(font_path),
        "label_boxes_source_pixels": [
            {"text": text, "box": list(box), "role": role} for text, box, role in labels
        ],
        "scope": "review-only text regeneration; bezel, icons, logo and background detail are scaled source artwork",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screen", choices=sorted(LAYOUTS))
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--font", type=Path, default=FONT_DEFAULT)
    args = parser.parse_args()
    if not args.font.is_file():
        raise FileNotFoundError(f"Font file not found: {args.font}")
    print(json.dumps(remaster(args.screen, args.source, args.output, args.font), indent=2))


if __name__ == "__main__":
    main()
