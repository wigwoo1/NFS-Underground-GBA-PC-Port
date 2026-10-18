#!/usr/bin/env python3
"""Create review-only, hash-checked transparent HUD scale candidates."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
import numpy as np
from PIL import Image

SOURCE_SIZE = (240, 160)
OUTPUT_SIZE = (3240, 2160)

def source_digest(rgba: np.ndarray) -> str:
    return hashlib.sha256(rgba.tobytes()).hexdigest()

def canonical_source_id(rgba: np.ndarray) -> str:
    """Match project FNV-1a identity: dimensions followed by RGBA bytes."""
    value = 14695981039346656037
    for byte in struct.pack("<II", rgba.shape[1], rgba.shape[0]) + rgba.tobytes():
        value = ((value ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"

def resize_premultiplied(rgba: np.ndarray, size: tuple[int, int], resample: Image.Resampling) -> np.ndarray:
    """Resize RGBA without transparent RGB contaminating visible edge colors."""
    if rgba.dtype != np.uint8 or rgba.ndim != 3 or rgba.shape[2] != 4:
        raise ValueError("expected uint8 RGBA input")
    if len(size) != 2 or not (1 <= size[0] <= 8192 and 1 <= size[1] <= 8192):
        raise ValueError("output dimensions must be in [1, 8192]")
    alpha = rgba[..., 3].astype(np.float32) / 255.0
    premultiplied = rgba[..., :3].astype(np.float32) * alpha[..., None]
    resized_alpha = np.asarray(Image.fromarray(alpha, "F").resize(size, resample), dtype=np.float32)
    channels = [np.asarray(Image.fromarray(premultiplied[..., c], "F").resize(size, resample), dtype=np.float32) for c in range(3)]
    rgb_p = np.clip(np.stack(channels, axis=2), 0.0, 255.0)
    resized_alpha = np.clip(resized_alpha, 0.0, 1.0)
    rgb_p = np.minimum(rgb_p, 255.0 * resized_alpha[..., None])
    rgb = np.zeros_like(rgb_p)
    nonzero = resized_alpha > 1e-7
    rgb[nonzero] = rgb_p[nonzero] / resized_alpha[nonzero, None]
    out = np.empty((size[1], size[0], 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.rint(resized_alpha * 255.0), 0, 255).astype(np.uint8)
    out[out[..., 3] == 0, :3] = 0
    return out

def create_candidates(source: Path, output: Path) -> dict:
    with Image.open(source) as im:
        if im.size != SOURCE_SIZE:
            raise ValueError(f"expected {SOURCE_SIZE[0]}x{SOURCE_SIZE[1]} source")
        rgba = np.asarray(im.convert("RGBA"), dtype=np.uint8)
    digest = source_digest(rgba)
    capture_id = canonical_source_id(rgba)
    if re.fullmatch(r"[0-9a-fA-F]{16}", source.stem) and source.stem.lower() != capture_id:
        raise ValueError(f"captured source ID mismatch: filename {source.stem.lower()}, pixels {capture_id}")
    output.mkdir(parents=True, exist_ok=True)
    files = {}
    methods = {"nearest": Image.Resampling.NEAREST,
               "bilinear-premultiplied": Image.Resampling.BILINEAR,
               "bicubic-premultiplied": Image.Resampling.BICUBIC}
    for name, method in methods.items():
        candidate = resize_premultiplied(rgba, OUTPUT_SIZE, method)
        filename = f"hud-{name}-review.png"
        Image.fromarray(candidate, "RGBA").save(output / filename)
        files[filename] = hashlib.sha256((output / filename).read_bytes()).hexdigest()
    report = {"format": "NFSUG-HUD-EDGE-SCALE-REVIEW-1", "release_candidate": False,
              "source": str(source), "source_size": list(SOURCE_SIZE),
              "source_pixel_sha256": digest, "canonical_capture_id": capture_id,
              "output_size": list(OUTPUT_SIZE),
              "method": "RGBA premultiplied before resize; unpremultiplied after; transparent output RGB forced to zero",
              "outputs": files, "runtime_integrated": False,
              "scope": "Filter comparison only; does not regenerate glyph shapes or classify HUD semantics."}
    (output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    print(json.dumps(create_candidates(args.source, args.output), indent=2))

if __name__ == "__main__":
    main()
