"""Upscale a captured texture, optionally blending borders for GL_REPEAT.

Experimental single-asset tool only; output is not a complete/release pack.
Optional generated detail supplies RGB; source alpha is preserved. Use
--uv-atlas for non-repeating atlases so opposite borders remain independent.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter


def _seam_mean(pixels: np.ndarray) -> float:
    a = pixels.astype(np.float32)
    return float((np.abs(a[0, ...] - a[-1, ...]).mean() +
                  np.abs(a[:, 0, ...] - a[:, -1, ...]).mean()) * 0.5)


def _blend_axis(pixels: np.ndarray, width: int, axis: int) -> None:
    length = pixels.shape[axis]
    if width < 1 or width * 2 > length:
        raise ValueError("edge_width must be positive and no more than half either output dimension")
    for offset in range(width):
        weight = 0.5 * (1.0 + np.cos(np.pi * offset / width))
        left_index, right_index = offset, length - 1 - offset
        if axis == 1:
            left, right = pixels[:, left_index, :].copy(), pixels[:, right_index, :].copy()
            shared = (left.astype(np.float32) + right.astype(np.float32)) * 0.5
            pixels[:, left_index, :] = left * (1.0 - weight) + shared * weight
            pixels[:, right_index, :] = right * (1.0 - weight) + shared * weight
        else:
            left, right = pixels[left_index, :, :].copy(), pixels[right_index, :, :].copy()
            shared = (left.astype(np.float32) + right.astype(np.float32)) * 0.5
            pixels[left_index, :, :] = left * (1.0 - weight) + shared * weight
            pixels[right_index, :, :] = right * (1.0 - weight) + shared * weight


def create(source_path: Path, output_path: Path, scale: int = 4,
           edge_width_source: int = 2, sharpen_percent: int = 125,
           detail_path: Path | None = None,
           preserve_bright_threshold: int | None = None,
           preserve_bright_feather: int = 24, seamless: bool = True) -> dict:
    if isinstance(scale, bool) or not isinstance(scale, int) or not 2 <= scale <= 16:
        raise ValueError("scale must be an integer from 2 to 16")
    if not isinstance(seamless, bool):
        raise ValueError("seamless must be a boolean")
    if isinstance(edge_width_source, bool) or not isinstance(edge_width_source, int) or edge_width_source < 1:
        raise ValueError("edge_width_source must be a positive integer")
    if isinstance(sharpen_percent, bool) or not isinstance(sharpen_percent, int) or not 0 <= sharpen_percent <= 300:
        raise ValueError("sharpen_percent must be an integer from 0 to 300")
    if preserve_bright_threshold is not None and (
            isinstance(preserve_bright_threshold, bool) or
            not isinstance(preserve_bright_threshold, int) or
            not 0 <= preserve_bright_threshold <= 255):
        raise ValueError("preserve_bright_threshold must be None or an integer from 0 to 255")
    if isinstance(preserve_bright_feather, bool) or not isinstance(preserve_bright_feather, int) or not 1 <= preserve_bright_feather <= 128:
        raise ValueError("preserve_bright_feather must be an integer from 1 to 128")
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    with Image.open(source_path) as opened:
        source = opened.convert("RGBA")
    sw, sh = source.size
    if sw < 2 or sh < 2:
        raise ValueError("source dimensions must be at least 2x2")
    width, height = sw * scale, sh * scale
    if width > 4096 or height > 4096:
        raise ValueError("output exceeds 4096-pixel texture limit")
    strip = edge_width_source * scale if seamless else 0
    if seamless and strip * 2 > min(width, height):
        raise ValueError("edge blend band must fit within half the smaller output dimension")
    resized_source = source.resize((width, height), Image.Resampling.LANCZOS)
    alpha = np.asarray(source.resize((width, height), Image.Resampling.NEAREST).getchannel("A"), dtype=np.uint8)
    if detail_path is None:
        rgb_image = resized_source.convert("RGB")
    else:
        with Image.open(detail_path) as opened_detail:
            detail = opened_detail.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
        if preserve_bright_threshold is None:
            rgb_image = detail
        else:
            source_luma = np.asarray(source.convert("RGB").convert("L"), dtype=np.float32)
            lower = preserve_bright_threshold - preserve_bright_feather * 0.5
            protect = np.clip((source_luma - lower) / preserve_bright_feather, 0.0, 1.0)
            protect_image = Image.fromarray(np.uint8(np.rint(protect * 255)), "L")
            protect_image = protect_image.resize((width, height), Image.Resampling.BILINEAR)
            weight = np.asarray(protect_image, dtype=np.float32)[..., None] / 255.0
            source_rgb = np.asarray(resized_source.convert("RGB"), dtype=np.float32)
            detail_rgb = np.asarray(detail, dtype=np.float32)
            mixed = source_rgb * weight + detail_rgb * (1.0 - weight)
            rgb_image = Image.fromarray(np.clip(np.rint(mixed), 0, 255).astype(np.uint8), "RGB")
    if sharpen_percent:
        rgb_image = rgb_image.filter(ImageFilter.UnsharpMask(
            radius=max(0.5, scale * 0.4), percent=sharpen_percent, threshold=2))
    pixels = np.asarray(rgb_image, dtype=np.float32).copy()
    before = _seam_mean(pixels)
    if seamless:
        _blend_axis(pixels, strip, 1)
        _blend_axis(pixels, strip, 0)
    rgb = np.clip(np.rint(pixels), 0, 255).astype(np.uint8)
    result = Image.fromarray(np.dstack((rgb, alpha)), "RGBA")
    after = _seam_mean(rgb)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path)
    return {
        "source": str(source_path), "source_size": [sw, sh],
        "detail_image": str(detail_path) if detail_path else None,
        "source_rgba_sha256": hashlib.sha256(source.tobytes()).hexdigest(),
        "output": str(output_path), "output_size": [width, height],
        "scale": scale, "seamless": seamless,
        "edge_width_source_pixels": edge_width_source if seamless else 0,
        "edge_blend_output_pixels": strip, "sharpen_percent": sharpen_percent,
        "preserve_bright_threshold": preserve_bright_threshold,
        "preserve_bright_feather": preserve_bright_feather,
        "rgb_seam_mean_before": before, "rgb_seam_mean_after": after,
        "source_alpha_preserved_nearest": True, "complete_pack": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--edge-width-source", type=int, default=2)
    parser.add_argument("--sharpen-percent", type=int, default=125)
    parser.add_argument("--detail-image", type=Path, default=None)
    parser.add_argument("--preserve-bright-threshold", type=int, default=None)
    parser.add_argument("--preserve-bright-feather", type=int, default=24)
    parser.add_argument("--uv-atlas", action="store_true",
                        help="keep opposite borders independent for non-repeating UV atlases")
    args = parser.parse_args()
    print(json.dumps(create(args.source, args.output, args.scale,
                            args.edge_width_source, args.sharpen_percent,
                            args.detail_image, args.preserve_bright_threshold,
                            args.preserve_bright_feather, not args.uv_atlas), indent=2))


if __name__ == "__main__":
    main()
