#!/usr/bin/env python3
"""Audit captured transparent HUD states without modifying source captures."""
from __future__ import annotations
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from PIL import Image
from texture_hash import source_hash

WIDTH, HEIGHT = 240, 160

def _bands(mask: np.ndarray, axis: int) -> list[list[int]]:
    counts = mask.sum(axis=axis)
    result: list[list[int]] = []
    i = 0
    while i < len(counts):
        if counts[i] == 0:
            i += 1
            continue
        j = i + 1
        while j < len(counts) and counts[j] > 0:
            j += 1
        result.append([int(i), int(j), int(counts[i:j].sum())])
        i = j
    return result

def _components(mask: np.ndarray) -> list[dict[str, int]]:
    seen = np.zeros(mask.shape, dtype=bool)
    h, w = mask.shape
    items: list[dict[str, int]] = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        stack = [(int(y), int(x))]
        seen[y, x] = True
        x0 = x1 = int(x); y0 = y1 = int(y); area = 0
        while stack:
            cy, cx = stack.pop(); area += 1
            x0 = min(x0, cx); x1 = max(x1, cx)
            y0 = min(y0, cy); y1 = max(y1, cy)
            for ny in range(max(0, cy - 1), min(h, cy + 2)):
                for nx in range(max(0, cx - 1), min(w, cx + 2)):
                    if mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; stack.append((ny, nx))
        items.append({"x": x0, "y": y0, "width": x1 - x0 + 1,
                      "height": y1 - y0 + 1, "pixels": area})
    return sorted(items, key=lambda a: (-a["pixels"], a["y"], a["x"]))

def audit(export_dir: Path, output_dir: Path, persistent_fraction: float = 0.90) -> dict:
    if not 0.5 <= persistent_fraction <= 1.0:
        raise ValueError("persistent_fraction must be in [0.5, 1.0]")
    manifest_path = export_dir / "inventory.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != "NFSUG-SOURCE-TEXTURE-INVENTORY-1":
        raise ValueError("unsupported source inventory format")
    rows = [r for r in manifest.get("textures", []) if r.get("kind") == 4]
    if not rows:
        raise ValueError("inventory contains no kind-4 HUD overlays")
    occupancy = np.zeros((HEIGHT, WIDTH), dtype=np.uint16)
    rgb_sum = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint64)
    rgb_sq = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint64)
    alpha_hist: Counter[int] = Counter()
    process_counts: Counter[str] = Counter()
    entries = []
    ordered: dict[str, list[tuple[int, np.ndarray, str]]] = defaultdict(list)
    for row in rows:
        key = str(row["hash"]).lower()
        if row.get("width") != WIDTH or row.get("height") != HEIGHT:
            raise ValueError(f"unexpected source dimensions for {key}")
        with Image.open(export_dir / row["source"]) as im:
            rgba = np.asarray(im.convert("RGBA"), dtype=np.uint8)
        if rgba.shape != (HEIGHT, WIDTH, 4):
            raise ValueError(f"decoded dimensions do not match for {key}")
        if f"{source_hash(rgba.tobytes(), WIDTH, HEIGHT):016x}" != key:
            raise ValueError(f"source-pixel hash mismatch for {key}")
        alpha = rgba[..., 3]
        visible = alpha > 0
        ys, xs = np.nonzero(visible)
        bbox = None if len(xs) == 0 else [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        alpha_hist.update(int(v) for v in alpha.ravel())
        occupancy += visible
        rgb = rgba[..., :3].astype(np.uint64)
        rgb_sum += rgb * visible[..., None]
        rgb_sq += rgb * rgb * visible[..., None]
        pid = str(row.get("first_seen_process_id", "unknown"))
        serial = int(row.get("first_seen_draw_serial", -1))
        process_counts[pid] += 1
        ordered[pid].append((serial, visible.copy(), key))
        entries.append({"source_hash": key, "process_id": pid, "draw_serial": serial,
                        "visible_pixels": int(visible.sum()), "alpha_values": sorted(int(v) for v in np.unique(alpha)),
                        "bounds_xyxy": bbox})
    total = len(rows)
    persistent = occupancy >= int(np.ceil(total * persistent_fraction))
    dynamic = (occupancy > 0) & ~persistent
    denom = np.maximum(occupancy, 1)[..., None].astype(np.float64)
    mean = rgb_sum / denom
    variance = np.maximum(0.0, rgb_sq / denom - mean * mean).mean(axis=2)
    changing_color = (occupancy > 0) & (variance > 64.0)
    output_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.where(persistent, 255, 0).astype(np.uint8), "L").save(output_dir / "persistent-art-mask.png")
    Image.fromarray(np.where(dynamic, 255, 0).astype(np.uint8), "L").save(output_dir / "state-varying-mask.png")
    heat = np.clip(np.rint(occupancy.astype(np.float32) * (255.0 / max(1, total))), 0, 255).astype(np.uint8)
    Image.fromarray(heat, "L").save(output_dir / "occupancy-map.png")
    Image.fromarray(np.clip(np.rint(np.sqrt(variance) * 2.0), 0, 255).astype(np.uint8), "L").save(output_dir / "color-variation-map.png")
    transitions = []
    for pid, sequence in ordered.items():
        sequence.sort(key=lambda item: item[0])
        for (sa, a, ha), (sb, b, hb) in zip(sequence, sequence[1:]):
            if sa >= 0 and sb >= 0:
                transitions.append({"process_id": pid, "from_draw": sa, "to_draw": sb,
                                   "from_hash": ha, "to_hash": hb,
                                   "visible_mask_changed_pixels": int(np.count_nonzero(a != b))})
    all_visible = occupancy > 0
    bbox = None
    ys, xs = np.nonzero(all_visible)
    if len(xs): bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    report = {
        "format": "NFSUG-HUD-OVERLAY-SPATIAL-AUDIT-1", "complete": False,
        "inventory_complete": bool(manifest.get("complete", False)),
        "export_directory": str(export_dir), "captured_visible_states": int(sum(e["visible_pixels"] > 0 for e in entries)),
        "captured_empty_states": int(sum(e["visible_pixels"] == 0 for e in entries)),
        "state_count": total, "dimensions": [WIDTH, HEIGHT],
        "source_hashes_verified": total, "process_state_counts": dict(process_counts),
        "alpha_histogram_pixel_samples": {str(k): int(v) for k, v in sorted(alpha_hist.items())},
        "visible_union_bounds_xyxy": bbox,
        "persistent_fraction": persistent_fraction,
        "persistent_art_pixels": int(persistent.sum()), "state_varying_pixels": int(dynamic.sum()),
        "changing_color_pixels_variance_gt_64": int(changing_color.sum()),
        "persistent_components": _components(persistent),
        "state_varying_components": _components(dynamic),
        "persistent_x_bands": _bands(persistent, 0), "persistent_y_bands": _bands(persistent, 1),
        "state_varying_x_bands": _bands(dynamic, 0), "state_varying_y_bands": _bands(dynamic, 1),
        "adjacent_capture_transitions": transitions,
        "assets": entries,
        "outputs": {name: name for name in ("persistent-art-mask.png", "state-varying-mask.png", "occupancy-map.png", "color-variation-map.png")},
        "scope": "Only overlays captured in the supplied ROM states; masks are diagnostic regions, not semantic HUD labels or regenerated artwork."
    }
    (output_dir / "hud-overlay-spatial-audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_dir", type=Path, help="directory containing inventory.json and hashed PNG captures")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--persistent-fraction", type=float, default=0.90)
    args = parser.parse_args()
    result = audit(args.export_dir, args.output_dir, args.persistent_fraction)
    print(json.dumps({k: v for k, v in result.items() if k not in {"assets", "adjacent_capture_transitions", "alpha_histogram_pixel_samples"}}, indent=2))

if __name__ == "__main__":
    main()
