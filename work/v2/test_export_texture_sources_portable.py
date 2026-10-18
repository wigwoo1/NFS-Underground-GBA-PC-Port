"""Pure-standard-library parity tests for PNG export and source identity."""
import struct
import json
import shutil
import tempfile
import zlib
from pathlib import Path
from export_texture_sources import PNG_SIGNATURE, _rgba_png_bytes, export
from texture_hash import source_hash

def decode_rgba_png(data):
    assert data.startswith(PNG_SIGNATURE)
    pos = len(PNG_SIGNATURE); chunks = []; compressed = bytearray(); width = height = None
    while pos < len(data):
        size = struct.unpack_from(">I", data, pos)[0]; pos += 4
        kind = data[pos:pos + 4]; pos += 4
        payload = data[pos:pos + size]; pos += size
        crc = struct.unpack_from(">I", data, pos)[0]; pos += 4
        assert zlib.crc32(kind + payload) & 0xFFFFFFFF == crc
        chunks.append(kind)
        if kind == b"IHDR":
            width, height, depth, color, comp, filt, interlace = struct.unpack(">IIBBBBB", payload)
            assert (depth, color, comp, filt, interlace) == (8, 6, 0, 0, 0)
        elif kind == b"IDAT": compressed.extend(payload)
        elif kind == b"IEND": break
    assert chunks == [b"IHDR", b"IDAT", b"IEND"]
    return width, height, zlib.decompress(compressed)

samples = [
    (2, 2, bytes((255,0,0,255, 0,255,0,128, 0,0,255,0, 25,50,75,255))),
    (3, 1, bytes((1,2,3,4, 5,6,7,8, 9,10,11,12))),
]
for width, height, rgba in samples:
    png = _rgba_png_bytes(width, height, rgba)
    out_w, out_h, raw = decode_rgba_png(png)
    row_bytes = width * 4
    expected = b"".join(b"\x00" + rgba[y * row_bytes:(y + 1) * row_bytes]
                        for y in range(height))
    assert (out_w, out_h, raw) == (width, height, expected)
assert source_hash(samples[0][2], 2, 2) != source_hash(samples[0][2], 1, 4)
for width, height, rgba in ((2,2,b"short"),(0,2,b"")):
    try: _rgba_png_bytes(width, height, rgba)
    except ValueError: pass
    else: raise AssertionError("invalid PNG input was accepted")

# Exercise the real inventory exporter for both newly captured UI source kinds
# without requiring Pillow, so menu/HUD provenance is checked in minimal builds.
width, height, rgba = samples[0]
key = source_hash(rgba, width, height)
with tempfile.TemporaryDirectory(prefix="nfsug-ui-export-") as temp_dir:
    root = Path(temp_dir)
    # Keep all fixture files directly in the temporary root. Some restricted
    # runners permit a temporary directory but deny Python-created subfolders.
    inventory = root
    export_destinations = []
    for kind in (4, 5):
        (inventory / f"{key:016x}.rgba").write_bytes(rgba)
        (inventory / "source-inventory.tsv").write_text(
            f"{key:016x}\t{width}\t{height}\tffffffff\t{kind}\t240\t0\t4321\t999\n",
            encoding="ascii")
        destination = root.parent / f"{root.name}-export-{kind}"
        result = export(inventory, destination)
        manifest = json.loads((destination / "inventory.json").read_text(encoding="utf-8"))
        assert result["texture_count"] == 1 and manifest["complete"] is False
        row = manifest["textures"][0]
        assert row["kind"] == kind and row["hash"] == f"{key:016x}"
        assert row["stride"] == 240 and row["shade"] == 0
        assert row["first_seen_process_id"] == 4321
        assert row["first_seen_draw_serial"] == 999
        assert decode_rgba_png((destination / row["source"]).read_bytes()) == (
            width, height,
            b"".join(b"\x00" + rgba[y * width * 4:(y + 1) * width * 4]
                    for y in range(height)))
        export_destinations.append(destination)
    for destination in export_destinations:
        shutil.rmtree(destination)

print("PASS: Pillow-free RGBA PNG parity, invalid-input checks, and kind-4/5 UI inventory export")
