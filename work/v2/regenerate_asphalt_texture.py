"""Create a UV-safe high-resolution asphalt candidate from a captured NFSUG texture.

The captured RGBA image remains the authority for road layout and markings. A
separate generated material contributes only high-frequency asphalt luminance
inside neutral-gray source pixels. This is a per-asset proof workflow, not a
claim that a complete game texture pack exists.
"""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter


def source_hash(image: Image.Image) -> int:
    rgba = image.convert("RGBA")
    w, h = rgba.size
    value = 14695981039346656037
    for byte in struct.pack("<II", w, h) + rgba.tobytes():
        value = ((value ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return value


def _crop_aspect(image: Image.Image, aspect: float) -> Image.Image:
    w, h = image.size
    if w / h > aspect:
        crop_w = max(1, round(h * aspect))
        left = (w - crop_w) // 2
        return image.crop((left, 0, left + crop_w, h))
    crop_h = max(1, round(w / aspect))
    top = (h - crop_h) // 2
    return image.crop((0, top, w, top + crop_h))


def _make_periodic(detail: np.ndarray, axis: int, band: int) -> np.ndarray:
    """Blend opposite edge bands so the high-pass material has no hard wrap."""
    out = detail.copy()
    length = out.shape[axis]
    band = min(max(1, band), length // 2)
    for distance in range(band):
        left_index, right_index = distance, length - 1 - distance
        amount = 1.0 - distance / band
        left = [slice(None)] * out.ndim
        right = [slice(None)] * out.ndim
        left[axis], right[axis] = left_index, right_index
        average = (out[tuple(left)] + out[tuple(right)]) * 0.5
        out[tuple(left)] = out[tuple(left)] * (1.0 - amount) + average * amount
        out[tuple(right)] = out[tuple(right)] * (1.0 - amount) + average * amount
    return out


def regenerate(source_path: Path, material_path: Path, output_path: Path,
               scale: int = 4, strength: float = 9.0,
               grain_strength: float = 4.0) -> dict:
    if scale < 2 or scale > 16:
        raise ValueError("scale must be between 2 and 16")
    if strength < 0 or strength > 24:
        raise ValueError("strength must be between 0 and 24")
    if grain_strength < 0 or grain_strength > 16:
        raise ValueError("grain_strength must be between 0 and 16")
    source = Image.open(source_path).convert("RGBA")
    sw, sh = source.size
    ow, oh = sw * scale, sh * scale
    if ow > 4096 or oh > 4096:
        raise ValueError("output exceeds texture-pack dimension limit")
    base_image = source.resize((ow, oh), Image.Resampling.LANCZOS)
    base = np.asarray(base_image, dtype=np.float32)
    original = np.asarray(source, dtype=np.uint8)
    mx = original[..., :3].max(axis=2).astype(np.int16)
    mn = original[..., :3].min(axis=2).astype(np.int16)
    luma = (original[..., 0].astype(np.float32) * .2126 +
            original[..., 1].astype(np.float32) * .7152 +
            original[..., 2].astype(np.float32) * .0722)
    # Neutral mid-gray only: yellow paint, white shoulders, dark edge bands,
    # transparent regions and colored detail remain controlled by the source.
    asphalt = (luma >= 58) & (luma <= 190) & ((mx - mn) <= 38) & (original[..., 3] > 0)
    mask = np.asarray(Image.fromarray((asphalt.astype(np.uint8) * 255), "L").resize(
        (ow, oh), Image.Resampling.NEAREST), dtype=np.float32) / 255.0
    nearest = np.asarray(source.resize((ow, oh), Image.Resampling.NEAREST), dtype=np.float32)
    # Reconstruct neutral asphalt as neutral luminance before adding aggregate;
    # old source texels can carry blocky channel-to-channel color noise. Keep
    # painted markings, rails, colored pixels, and alpha edges nearest-neighbor.
    asphalt_luma = (base[..., 0] * .2126 + base[..., 1] * .7152 +
                    base[..., 2] * .0722)
    neutral_asphalt = np.repeat(asphalt_luma[..., None], 3, axis=2)
    base[..., :3] = np.where(mask[..., None] > 0.5, neutral_asphalt, nearest[..., :3])

    material = Image.open(material_path).convert("RGB")
    material = _crop_aspect(material, ow / oh).resize((ow, oh), Image.Resampling.LANCZOS)
    blur_radius = max(3.0, 2.0 * scale)
    low = np.asarray(material.convert("L").filter(ImageFilter.GaussianBlur(blur_radius)), dtype=np.float32)
    high = np.asarray(material.convert("L"), dtype=np.float32) - low
    # Keep stone detail subtle and tile-safe instead of copying the AI material's
    # broad lighting variation or possible border seam into the game texture.
    high -= float(np.mean(high))
    deviation = float(np.std(high))
    if deviation > 1e-5:
        high *= strength / deviation
    high = np.clip(high, -2.5 * strength, 2.5 * strength)
    high = _make_periodic(high, axis=1, band=min(32 * scale, ow // 2))
    high = _make_periodic(high, axis=0, band=min(16 * scale, oh // 2))

    # Add deterministic micro-grain after resizing the material. Without this
    # output-resolution term, linear texture filtering can erase most generated
    # aggregate and leave the road looking like softened low-resolution source.
    digest = source_hash(source)
    raw_grain = np.random.default_rng(digest).standard_normal((oh, ow)).astype(np.float32)
    # A small periodic 3x3 blur avoids a harsh white-noise/sparkle appearance.
    grain = (raw_grain * 0.40 +
             (np.roll(raw_grain, 1, 0) + np.roll(raw_grain, -1, 0) +
              np.roll(raw_grain, 1, 1) + np.roll(raw_grain, -1, 1)) * 0.10 +
             (np.roll(np.roll(raw_grain, 1, 0), 1, 1) +
              np.roll(np.roll(raw_grain, 1, 0), -1, 1) +
              np.roll(np.roll(raw_grain, -1, 0), 1, 1) +
              np.roll(np.roll(raw_grain, -1, 0), -1, 1)) * 0.05)
    grain -= float(np.mean(grain))
    grain_deviation = float(np.std(grain))
    if grain_deviation > 1e-5:
        grain *= grain_strength / grain_deviation
    grain = _make_periodic(grain, axis=1, band=min(16 * scale, ow // 2))
    grain = _make_periodic(grain, axis=0, band=min(8 * scale, oh // 2))

    detail = high + grain
    rgb = np.clip(base[..., :3] + (detail[..., None] * mask[..., None]), 0, 255).astype(np.uint8)
    alpha = np.asarray(source.getchannel("A").resize((ow, oh), Image.Resampling.NEAREST), dtype=np.uint8)
    result = Image.fromarray(np.dstack((rgb, alpha)), "RGBA")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    result.save(output_path)
    return {
        "source": str(source_path), "source_width": sw, "source_height": sh,
        "source_hash_fnv1a64": f"{digest:016x}",
        "upscaled": str(output_path), "width": ow, "height": oh,
        "scale": scale, "detail_strength": strength,
        "grain_strength": grain_strength,
        "asphalt_source_pixel_fraction": float(asphalt.mean()),
        "changed_output_pixel_fraction": float(np.any(rgb != np.asarray(base[..., :3], dtype=np.uint8), axis=2).mean()),
        "complete_pack": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("material", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--strength", type=float, default=9.0)
    parser.add_argument("--grain-strength", type=float, default=4.0,
                        help="deterministic micro-grain standard deviation (0..16)")
    args = parser.parse_args()
    print(json.dumps(regenerate(args.source, args.material, args.output,
                                args.scale, args.strength,
                                args.grain_strength), indent=2))


if __name__ == "__main__":
    main()
