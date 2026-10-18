#!/usr/bin/env python3
"""Build diagnostic atlases from the game's owned original bitmap glyph calls."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HEADER_SIZE = 64
MAX_ASSET = 4096
TARGET_SCALE = 14

def parse_capture(binary: bytes, completion_csv: Path) -> list[dict]:
    with completion_csv.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    result, offset = [], 0
    for ordinal, row in enumerate(rows):
        if int(row["index"]) != ordinal:
            raise ValueError(f"completion indices are not contiguous at {ordinal}")
        if len(binary) - offset < HEADER_SIZE:
            raise ValueError(f"truncated glyph header at record {ordinal}")
        rec = struct.unpack_from("<16I", binary, offset)
        width, height, draw_width = rec[7], rec[8], rec[9]
        size = rec[13]
        if not (0 < width <= 256 and 0 < height <= 256 and draw_width <= width and 0 < size <= MAX_ASSET and size == width * height):
            raise ValueError(f"invalid glyph geometry at record {ordinal}")
        end = offset + HEADER_SIZE + size
        if end > len(binary):
            raise ValueError(f"truncated glyph pixels at record {ordinal}")
        done_destination = int(row["destination"], 16)
        if rec[0] != int(row["begin"]) or rec[4] != done_destination:
            raise ValueError(f"entry/completion metadata mismatch at record {ordinal}")
        if rec[15] != 0x0806fc60:
            raise ValueError(f"unexpected original glyph-draw target at record {ordinal}")
        result.append({
            "call": ordinal, "glyph": rec[3], "destination": rec[4], "stride": rec[5],
            "palette_offset": rec[6] & 0xffffffff, "width": width, "height": height,
            "draw_width": draw_width, "flags": rec[10], "transparent": rec[11],
            "source": rec[12], "asset": binary[offset + HEADER_SIZE:end],
            "begin": rec[0], "end": int(row["end"]),
        })
        offset = end
    if offset != len(binary):
        raise ValueError(f"unclaimed trailing glyph bytes: {len(binary)-offset}")
    return result

def unique_glyphs(records: list[dict]) -> list[dict]:
    unique = {}
    for r in records:
        key = (r["glyph"], r["width"], r["height"], r["draw_width"], r["flags"], r["transparent"], r["palette_offset"], r["asset"])
        if key not in unique:
            unique[key] = dict(r, calls=[])
        unique[key]["calls"].append(r["call"])
    return list(unique.values())

def _normalized_glyph(g: dict) -> tuple[Image.Image, Image.Image]:
    w, h = g["width"], g["height"]
    values = np.frombuffer(g["asset"], dtype=np.uint8).reshape(h, w).astype(np.float32)
    crop = values[:, :g["draw_width"]]
    lo, hi = float(crop.min()), float(crop.max())
    grey = np.zeros(crop.shape, dtype=np.uint8) if hi <= lo else np.rint((crop - lo) * (255.0 / (hi - lo))).clip(0,255).astype(np.uint8)
    if g["flags"] & 1:
        alpha = np.where(crop == g["transparent"], 0, 255).astype(np.uint8)
    else:
        alpha = np.full(crop.shape, 255, dtype=np.uint8)
    return Image.fromarray(grey, "L"), Image.fromarray(alpha, "L")

def sdf_coverage(mask: np.ndarray, scale: int, edge_px: float = 1.0,
                 preserve_area: bool = False) -> Image.Image:
    """Supersample a tiny binary glyph mask through a signed-distance edge.

    When requested, solve a small signed-distance bias so antialiasing changes
    edge smoothness without changing the glyph's integrated ink area.
    """
    if (mask.ndim != 2 or mask.dtype != np.bool_ or not (2 <= scale <= 24)
            or not (0.5 <= edge_px <= 2.0) or not isinstance(preserve_area, bool)):
        raise ValueError("invalid glyph mask, scale, edge width, or area mode")
    h, w = mask.shape
    padded = np.pad(mask, 1, constant_values=False)
    inside = np.argwhere(padded)
    outside = np.argwhere(~padded)
    if not len(inside):
        return Image.new("L", (w*scale,h*scale), 0)
    sdf = np.empty((h,w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            yy, xx = y+1, x+1
            candidates = outside if padded[yy,xx] else inside
            distances = np.sqrt(((candidates[:,0]-yy)**2)+((candidates[:,1]-xx)**2))
            d = float(distances.min()) - 0.5
            sdf[y,x] = d if mask[y,x] else -d
    high = np.asarray(Image.fromarray(sdf,"F").resize((w*scale,h*scale),Image.Resampling.BILINEAR),dtype=np.float32)
    bias = 0.0
    if preserve_area and mask.any():
        target = float(mask.sum()) * scale * scale
        low, high_bias = -2.0, 2.0
        for _ in range(28):
            mid = (low + high_bias) * 0.5
            if np.clip(0.5 + (high + mid)*scale/edge_px, 0.0, 1.0).sum() < target:
                low = mid
            else:
                high_bias = mid
        candidates = (low, high_bias, (low + high_bias) * 0.5)
        bias = min(candidates, key=lambda v: abs(
            np.clip(0.5 + (high + v)*scale/edge_px, 0.0, 1.0).sum() - target))
    alpha = np.clip(0.5 + (high + bias)*scale/edge_px,0.0,1.0)
    return Image.fromarray(np.rint(alpha*255).astype(np.uint8),"L")
def make_atlases(records: list[dict], output: Path, scale: int = TARGET_SCALE) -> dict:
    if not records:
        raise ValueError("capture contains no glyph records")
    if not 2 <= scale <= 24:
        raise ValueError("scale must be in [2, 24]")
    glyphs = unique_glyphs(records)
    columns = 7
    cell_w, cell_h = 300, 300
    variants = {"nearest": Image.Resampling.NEAREST,
                "bilinear": Image.Resampling.BILINEAR,
                "bicubic": Image.Resampling.BICUBIC,
                "sdf-1px": "sdf", "sdf-1px-area": "sdf-area"}
    output.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default()
    output_hashes = {}
    for name, method in variants.items():
        sheet = Image.new("RGB", (columns*cell_w, math.ceil(len(glyphs)/columns)*cell_h), (18,18,22))
        draw = ImageDraw.Draw(sheet)
        for i,g in enumerate(glyphs):
            x=(i%columns)*cell_w+10; y=(i//columns)*cell_h+10
            grey,alpha=_normalized_glyph(g)
            size=(grey.width*scale, grey.height*scale)
            if method in ("sdf", "sdf-area"):
                color=grey.resize(size,Image.Resampling.NEAREST)
                coverage=sdf_coverage(np.asarray(alpha,dtype=np.uint8)>=128,scale,
                                      preserve_area=(method == "sdf-area"))
            else:
                color=grey.resize(size,method)
                coverage=alpha.resize(size,method)
            rgba=Image.new("RGBA",size,(0,0,0,0)); rgba.putalpha(coverage)
            rgba_rgb=Image.merge("RGBA",(color,color,color,coverage))
            sheet.paste(rgba_rgb.convert("RGB"),(x,y),coverage)
            label=f"id {g['glyph']:03d}  {g['width']}x{g['height']} dw{g['draw_width']}  n={len(g['calls'])}"
            draw.text((x,y+size[1]+5),label,fill=(230,230,230),font=font)
        path=output/f"glyph-atlas-{name}-review.png"
        sheet.save(path)
        output_hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    ids={str(k):sum(1 for r in records if r["glyph"]==k) for k in sorted({r["glyph"] for r in records})}
    desc={}
    for r in records:
        key=f"{r['width']}x{r['height']}/dw{r['draw_width']}/f{r['flags']}/t{r['transparent']}/p{r['palette_offset']}"
        desc[key]=desc.get(key,0)+1
    area_source=0.0; area_sdf=0.0; area_sdf_balanced=0.0
    area_ratios=[]; area_balanced_ratios=[]
    for g in glyphs:
        _,a=_normalized_glyph(g)
        mask=np.asarray(a,dtype=np.uint8)>=128
        source_area=float(mask.sum())
        if source_area:
            coverage=np.asarray(sdf_coverage(mask,scale),dtype=np.float32)/255.0
            balanced=np.asarray(sdf_coverage(mask,scale,preserve_area=True),dtype=np.float32)/255.0
            sdf_area=float(coverage.sum())/(scale*scale)
            balanced_area=float(balanced.sum())/(scale*scale)
            area_source+=source_area;area_sdf+=sdf_area;area_sdf_balanced+=balanced_area
            area_ratios.append(sdf_area/source_area)
            area_balanced_ratios.append(balanced_area/source_area)
    report={"format":"NFSUG-OWNED-GLYPH-ATLAS-REVIEW-1","release_candidate":False,
            "runtime_integrated":False,"call_count":len(records),"unique_glyph_shapes":len(glyphs),
            "source_asset_bytes_sha256":hashlib.sha256(b"".join(r["asset"] for r in records)).hexdigest(),
            "source_asset_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scale":scale,"variants":list(variants),"outputs":output_hashes,
            "sdf_equivalent_source_area_ratio":area_sdf/area_source if area_source else None,
            "sdf_per_glyph_area_ratio_min":min(area_ratios) if area_ratios else None,
            "sdf_per_glyph_area_ratio_max":max(area_ratios) if area_ratios else None,
            "area_balanced_sdf_equivalent_source_area_ratio":area_sdf_balanced/area_source if area_source else None,
            "area_balanced_sdf_per_glyph_area_ratio_min":min(area_balanced_ratios) if area_balanced_ratios else None,
            "area_balanced_sdf_per_glyph_area_ratio_max":max(area_balanced_ratios) if area_balanced_ratios else None,
            "glyph_call_counts":ids,"descriptor_counts":desc,
            "scope":"Grayscale-normalized source-index diagnostic atlas only. Original palette, menu background, final font contours, and runtime substitution are not represented."}
    (output/"manifest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("binary",type=Path);ap.add_argument("completion_csv",type=Path);ap.add_argument("output",type=Path)
    ap.add_argument("--scale",type=int,default=TARGET_SCALE)
    a=ap.parse_args()
    records=parse_capture(a.binary.read_bytes(),a.completion_csv)
    print(json.dumps(make_atlases(records,a.output,a.scale),indent=2))
if __name__=="__main__": main()





