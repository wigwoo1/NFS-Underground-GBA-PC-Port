"""Make a UV-preserving masonry replacement for one audited facade texture.

The captured source owns the UV composition. A caller-supplied preservation rectangle
keeps architectural features such as windows aligned; a feathered polygon can
preserve their silhouettes while regenerated material fills the wall. Captured
features receive a 4x Lanczos resize with modest sharpening. This is per-asset
experimental output, never a complete pack.
"""
from __future__ import annotations
import json
import struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def source_hash(image: Image.Image) -> int:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    value = 14695981039346656037
    for byte in struct.pack("<II", width, height) + rgba.tobytes():
        value = ((value ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return value


def _crop_aspect(image: Image.Image, aspect: float) -> Image.Image:
    width, height = image.size
    if width / height > aspect:
        crop_width = max(1, round(height * aspect))
        left = (width - crop_width) // 2
        return image.crop((left, 0, left + crop_width, height))
    crop_height = max(1, round(width / aspect))
    top = (height - crop_height) // 2
    return image.crop((0, top, width, top + crop_height))


def _rect(rect: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    if not isinstance(rect, (tuple, list)) or len(rect) != 4:
        raise ValueError("preserve_rect must be (left, top, right, bottom)")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in rect):
        raise ValueError("preserve_rect coordinates must be integers")
    left, top, right, bottom = rect
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError("preserve_rect must be a non-empty rectangle within the source")
    return left, top, right, bottom


def _polygon(points, width: int, height: int):
    if not isinstance(points, (tuple, list)) or len(points) < 3:
        raise ValueError("preserve_polygon must contain at least three (x, y) points")
    checked = []
    for point in points:
        if not isinstance(point, (tuple, list)) or len(point) != 2:
            raise ValueError("preserve_polygon points must be (x, y) pairs")
        x, y = point
        if any(isinstance(value, bool) or not isinstance(value, int) for value in point):
            raise ValueError("preserve_polygon coordinates must be integers")
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError("preserve_polygon points must be within the source")
        checked.append((x, y))
    return checked


def regenerate(source_path: Path, material_path: Path, output_path: Path,
               preserve_rect: tuple[int, int, int, int], scale: int = 4,
               source_blend: float = 0.08,
               feather_source_pixels: float = 2.0,
               preserve_polygon=None, preserve_polygons=None) -> dict:
    if isinstance(scale, bool) or not isinstance(scale, int) or not 2 <= scale <= 16:
        raise ValueError("scale must be an integer between 2 and 16")
    if not 0.0 <= source_blend <= 0.25:
        raise ValueError("source_blend must be between 0 and 0.25")
    if not 0.0 <= feather_source_pixels <= 16.0:
        raise ValueError("feather_source_pixels must be between 0 and 16")
    source = Image.open(source_path).convert("RGBA")
    source_width, source_height = source.size
    if not source_width or not source_height:
        raise ValueError("source texture must be non-empty")
    output_width, output_height = source_width * scale, source_height * scale
    if output_width > 4096 or output_height > 4096:
        raise ValueError("output exceeds texture-pack dimension limit")
    left, top, right, bottom = _rect(preserve_rect, source_width, source_height)
    if preserve_polygon is not None and preserve_polygons is not None:
        raise ValueError("use preserve_polygon or preserve_polygons, not both")
    if preserve_polygons is not None:
        if not isinstance(preserve_polygons, (tuple, list)) or not preserve_polygons:
            raise ValueError("preserve_polygons must contain at least one polygon")
        feature_polygons = [_polygon(poly, source_width, source_height)
                            for poly in preserve_polygons]
    elif preserve_polygon is not None:
        feature_polygons = [_polygon(preserve_polygon, source_width, source_height)]
    else:
        feature_polygons = []
    material = Image.open(material_path).convert("RGB")
    material = _crop_aspect(material, output_width / output_height).resize(
        (output_width, output_height), Image.Resampling.LANCZOS)

    original = np.asarray(source, dtype=np.uint8)
    nearest = np.asarray(source.resize((output_width, output_height),
                                       Image.Resampling.NEAREST), dtype=np.uint8)
    smooth_image = source.resize((output_width, output_height), Image.Resampling.LANCZOS).convert("RGBA")
    smooth_rgb = smooth_image.convert("RGB").filter(
        ImageFilter.UnsharpMask(radius=max(0.5, scale * 0.4), percent=125, threshold=2))
    smooth_rgb.putalpha(smooth_image.getchannel("A"))
    smooth_source = np.asarray(smooth_rgb, dtype=np.uint8)
    high = np.asarray(material, dtype=np.float32)
    preserve_image = Image.new("L", (source_width, source_height), 255)
    preserve_draw = ImageDraw.Draw(preserve_image)
    if feature_polygons:
        for polygon in feature_polygons:
            preserve_draw.polygon(polygon, fill=0)
    else:
        preserve_draw.rectangle((left, top, right - 1, bottom - 1), fill=0)
    preserve_pixels = np.asarray(preserve_image, dtype=np.uint8) == 0
    wall_pixels = original[..., :3][~preserve_pixels].astype(np.float32)
    if wall_pixels.size == 0:
        raise ValueError("preserve_rect leaves no material area to regenerate")

    # Match the generated tile to the captured facade's color range so the new
    # masonry does not introduce a broad exposure or palette shift.
    source_mean = wall_pixels.mean(axis=0)
    source_std = wall_pixels.std(axis=0)
    material_mean = high.reshape(-1, 3).mean(axis=0)
    material_std = high.reshape(-1, 3).std(axis=0)
    gain = np.clip(source_std / np.maximum(material_std, 1e-5), 0.35, 1.1)
    high = np.clip((high - material_mean) * gain + source_mean, 0, 255)
    if source_blend:
        high = np.clip(high * (1.0 - source_blend) + smooth_source[..., :3] * source_blend,
                       0, 255)

    # Feather the material transition outside the exact UV feature region. Keep
    # the protected window itself fully sourced from the captured texture so the
    # replacement changes wall material without shifting or repainting geometry.
    detail_mask_image = preserve_image.copy()
    if feather_source_pixels:
        detail_mask_image = detail_mask_image.filter(
            ImageFilter.GaussianBlur(radius=feather_source_pixels))
        # Restore the exact protected shape after blurring it into the blend.
        detail_draw = ImageDraw.Draw(detail_mask_image)
        if feature_polygons:
            for polygon in feature_polygons:
                detail_draw.polygon(polygon, fill=0)
        else:
            detail_draw.rectangle((left, top, right - 1, bottom - 1), fill=0)
    material_weight_image = detail_mask_image.resize(
        (output_width, output_height), Image.Resampling.BILINEAR)
    # Ensure resize filtering never alters source pixels inside the feature.
    output_draw = ImageDraw.Draw(material_weight_image)
    if feature_polygons:
        for polygon in feature_polygons:
            output_draw.polygon([(x * scale, y * scale) for x, y in polygon], fill=0)
    else:
        output_draw.rectangle((left * scale, top * scale,
                               right * scale - 1, bottom * scale - 1), fill=0)
    material_weight = np.asarray(material_weight_image, dtype=np.float32)[..., None] / 255.0
    rgb = smooth_source[..., :3].astype(np.float32) * (1.0 - material_weight) + high * material_weight
    alpha = nearest[..., 3]
    result = Image.fromarray(np.dstack((rgb.astype(np.uint8), alpha)), "RGBA")
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path)
    return {
        "source": str(source_path), "source_width": source_width,
        "source_height": source_height,
        "source_hash_fnv1a64": f"{source_hash(source):016x}",
        "upscaled": str(output_path), "width": output_width,
        "height": output_height, "scale": scale,
        "preserved_rect": [left, top, right, bottom],
        "preserved_polygon": feature_polygons[0] if len(feature_polygons) == 1 else None,
        "preserved_polygons": feature_polygons,
        "feather_source_pixels": feather_source_pixels,
        "regenerated_pixel_fraction": float(material_weight.mean()),
        "complete_pack": False,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("material", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--preserve-rect", required=True,
                        help="source-space left,top,right,bottom rectangle")
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--source-blend", type=float, default=0.08)
    parser.add_argument("--feather-source-pixels", type=float, default=2.0,
                        help="Gaussian transition width in source pixels; 0 disables feathering")
    parser.add_argument("--preserve-polygon",
                        help="source-space polygon as x,y;x,y;x,y for an irregular feature")
    parser.add_argument("--preserve-polygons",
                        help="multiple polygons separated by |, each polygon as x,y;x,y;x,y")
    args = parser.parse_args()
    try:
        rect = tuple(int(value) for value in args.preserve_rect.split(","))
        if len(rect) != 4:
            raise ValueError("preserve-rect requires four comma-separated integers")
        polygon = None
        if args.preserve_polygon:
            polygon = [tuple(int(v) for v in pair.split(","))
                       for pair in args.preserve_polygon.split(";")]
            if any(len(point) != 2 for point in polygon):
                raise ValueError("preserve-polygon points require x,y pairs")
        polygons = None
        if args.preserve_polygons:
            polygons = []
            for encoded in args.preserve_polygons.split("|"):
                points = [tuple(int(v) for v in pair.split(","))
                          for pair in encoded.split(";")]
                if any(len(point) != 2 for point in points):
                    raise ValueError("preserve-polygons points require x,y pairs")
                polygons.append(points)
        print(json.dumps(regenerate(args.source, args.material, args.output, rect,
                                    args.scale, args.source_blend,
                                    args.feather_source_pixels, polygon, polygons), indent=2))
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
