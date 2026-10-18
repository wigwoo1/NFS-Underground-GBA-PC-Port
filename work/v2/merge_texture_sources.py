"""Merge validated, incomplete runtime texture captures without claiming coverage."""
import argparse
import json
import shutil
import tempfile
from pathlib import Path

from build_texture_pack import load_rgba, source_hash

FORMAT = "NFSUG-SOURCE-TEXTURE-INVENTORY-1"


def _read_capture(inventory: Path) -> tuple[dict, list[tuple[dict, Path, bytes]]]:
    inventory = inventory.resolve()
    data = json.loads((inventory / "inventory.json").read_text(encoding="utf-8"))
    if data.get("format") != FORMAT:
        raise ValueError(f"Unsupported source inventory: {inventory}")
    rows = data.get("textures")
    if not isinstance(rows, list):
        raise ValueError(f"Missing texture rows: {inventory}")
    validated = []
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Invalid texture row {index}: {inventory}")
        key = row.get("hash")
        if not isinstance(key, str) or len(key) != 16 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError(f"Invalid source hash on row {index}: {inventory}")
        if key in seen:
            raise ValueError(f"Duplicate source hash in capture row {index}: {inventory}")
        seen.add(key)
        provenance_fields = ("first_seen_process_id", "first_seen_draw_serial")
        provenance_present = tuple(field in row for field in provenance_fields)
        if any(provenance_present) and not all(provenance_present):
            raise ValueError(f"Incomplete draw provenance on row {index}: {inventory}")
        if all(provenance_present):
            for field in provenance_fields:
                value = row[field]
                if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
                    raise ValueError(f"Invalid {field} on row {index}: {inventory}")
        renderer_fields = ("stride", "shade")
        renderer_present = tuple(field in row for field in renderer_fields)
        if any(renderer_present) and not all(renderer_present):
            raise ValueError(f"Incomplete renderer metadata on row {index}: {inventory}")
        if all(renderer_present):
            for field in renderer_fields:
                value = row[field]
                if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
                    raise ValueError(f"Invalid {field} on row {index}: {inventory}")
        image_path = (inventory / row.get("source", "")).resolve()
        try:
            image_path.relative_to(inventory)
        except ValueError as error:
            raise ValueError(f"Texture source escapes inventory: {inventory}") from error
        rgba, width, height = load_rgba(image_path)
        if row.get("width") != width or row.get("height") != height:
            raise ValueError(f"Texture dimensions disagree with source image: {image_path}")
        if source_hash(rgba, width, height) != int(key, 16):
            raise ValueError(f"Texture source hash mismatch: {image_path}")
        validated.append((row, image_path, rgba))
    return data, validated


def merge(inventories: list[Path], destination: Path) -> dict:
    if not inventories:
        raise ValueError("At least one source inventory is required")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite merged inventory: {destination}")

    capture_sets = []
    unique: dict[str, dict] = {}
    total_bytes = 0
    for set_id, inventory in enumerate(inventories):
        data, rows = _read_capture(inventory)
        capture_sets.append({"id": set_id, "name": inventory.name,
                             "captured_texture_count": len(rows), "complete": False})
        for row, image_path, rgba in rows:
            key = row["hash"]
            entry = unique.get(key)
            if entry is None:
                entry = {"hash": key, "width": row["width"], "height": row["height"],
                         "source": f"source/{key}.png", "captures": []}
                unique[key] = entry
                total_bytes += len(rgba)
            elif (entry["width"], entry["height"]) != (row["width"], row["height"]):
                raise ValueError(f"Conflicting dimensions for source hash {key}")
            capture = {"set_id": set_id}
            for field in ("address", "kind", "stride", "shade", "first_seen_process_id", "first_seen_draw_serial"):
                if field in row:
                    capture[field] = row[field]
            entry["captures"].append(capture)

    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=destination.name + ".building-", dir=destination.parent))
    try:
        source_dir = stage / "source"
        source_dir.mkdir()
        for inventory in inventories:
            _, rows = _read_capture(inventory)
            for row, image_path, _ in rows:
                target = source_dir / f"{row['hash']}.png"
                if not target.exists():
                    shutil.copyfile(image_path, target)
        result = {"format": FORMAT, "complete": False,
                  "coverage": "deduplicated union of the listed captures; full ROM coverage not audited",
                  "capture_sets": capture_sets, "texture_count": len(unique),
                  "unique_source_rgba_bytes": total_bytes,
                  "textures": list(unique.values())}
        (stage / "inventory.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        stage.replace(destination)
        return {key: result[key] for key in ("complete", "texture_count", "unique_source_rgba_bytes")}
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="new merged inventory output directory")
    parser.add_argument("inventories", nargs="+", type=Path,
                        help="export directories produced by export_texture_sources.py")
    args = parser.parse_args()
    print(json.dumps(merge(args.inventories, args.destination), indent=2))


if __name__ == "__main__":
    main()
