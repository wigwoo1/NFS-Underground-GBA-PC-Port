"""Validate captured source RGBA blobs and convert them to a reviewable PNG inventory."""
import argparse
import json
import shutil
import struct
import zlib
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

from texture_hash import source_hash

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)

def _rgba_png_bytes(width: int, height: int, rgba: bytes) -> bytes:
    if not width or not height or len(rgba) != width * height * 4:
        raise ValueError("RGBA payload length does not match PNG dimensions")
    row_bytes = width * 4
    raw = b"".join(b"\x00" + rgba[y * row_bytes:(y + 1) * row_bytes]
                   for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (PNG_SIGNATURE + _png_chunk(b"IHDR", header) +
            _png_chunk(b"IDAT", zlib.compress(raw)) +
            _png_chunk(b"IEND", b""))

def _write_rgba_png(path: Path, width: int, height: int, rgba: bytes) -> None:
    path.write_bytes(_rgba_png_bytes(width, height, rgba))


def export(inventory: Path, destination: Path) -> dict:
    rows_path = inventory / "source-inventory.tsv"
    if not rows_path.is_file():
        raise FileNotFoundError(rows_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite texture source export: {destination}")
    stage = Path(tempfile.mkdtemp(prefix=destination.name + ".building-", dir=destination.parent))
    try:
        # Keep exported PNGs flat in the staging directory. Besides simplifying
        # inventory paths, this permits atomic export in restricted workspaces
        # that allow a temporary directory but disallow nested directory creation.
        png_dir = stage
        entries = {}
        total_bytes = 0
        for line_number, raw_line in enumerate(rows_path.read_text(encoding="ascii").splitlines(), 1):
            fields = raw_line.split("\t")
            if len(fields) not in (5, 7, 9):
                raise ValueError(f"Malformed inventory row {line_number}")
            key, width_text, height_text, address_text, kind_text = fields[:5]
            provenance = {}
            if len(fields) == 7:
                process_text, draw_serial_text = fields[5:]
                process_id, draw_serial = int(process_text), int(draw_serial_text)
                if not 0 <= process_id <= 0xFFFFFFFF or not 0 <= draw_serial <= 0xFFFFFFFF:
                    raise ValueError(f"Invalid provenance on inventory row {line_number}")
                provenance = {"first_seen_process_id": process_id,
                              "first_seen_draw_serial": draw_serial}
            elif len(fields) == 9:
                stride_text, shade_text, process_text, draw_serial_text = fields[5:]
                stride, shade = int(stride_text), int(shade_text)
                process_id, draw_serial = int(process_text), int(draw_serial_text)
                values = (stride, shade, process_id, draw_serial)
                if any(not 0 <= value <= 0xFFFFFFFF for value in values):
                    raise ValueError(f"Invalid renderer metadata on inventory row {line_number}")
                provenance = {"stride": stride, "shade": shade,
                              "first_seen_process_id": process_id,
                              "first_seen_draw_serial": draw_serial}
            width, height = int(width_text), int(height_text)
            if width <= 0 or height <= 0 or width * height > 4096 * 4096:
                raise ValueError(f"Invalid dimensions on inventory row {line_number}")
            blob = (inventory / f"{key}.rgba").read_bytes()
            if len(blob) != width * height * 4:
                raise ValueError(f"RGBA byte count mismatch on inventory row {line_number}")
            calculated = source_hash(blob, width, height)
            if calculated != int(key, 16):
                raise ValueError(f"Source hash mismatch on inventory row {line_number}")
            if key in entries:
                if entries[key]["width"] != width or entries[key]["height"] != height:
                    raise ValueError(f"Conflicting dimensions for texture {key}")
                continue
            name = f"{key}.png"
            if Image is None:
                _write_rgba_png(png_dir / name, width, height, blob)
            else:
                Image.frombytes("RGBA", (width, height), blob).save(png_dir / name)
            entries[key] = {"hash": key, "width": width, "height": height,
                            "address": int(address_text, 16), "kind": int(kind_text),
                            "source": name, **provenance}
            total_bytes += len(blob)
        result = {"format": "NFSUG-SOURCE-TEXTURE-INVENTORY-1",
                  "complete": False,
                  "coverage": "captured only from the ROM states and frames exercised",
                  "texture_count": len(entries),
                  "source_rgba_bytes": total_bytes,
                  "textures": list(entries.values())}
        (stage / "inventory.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        stage.replace(destination)
        return result
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path, help="texture-source-inventory directory from the renderer")
    parser.add_argument("destination", type=Path, help="new output directory for source PNGs and inventory.json")
    args = parser.parse_args()
    result = export(args.inventory, args.destination)
    print(json.dumps({key: value for key, value in result.items() if key != "textures"}, indent=2))


if __name__ == "__main__":
    main()
