"""Verify a non-release UI-art candidate stays tied to its captured source frame."""
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texture_hash import source_hash

SIGNATURE = bytes((137, 80, 78, 71, 13, 10, 26, 10))

def png_info(path):
    data = path.read_bytes()
    assert data.startswith(SIGNATURE), f"not PNG: {path}"
    pos = len(SIGNATURE)
    width = height = color = depth = interlace = None
    compressed = bytearray()
    seen = []
    while pos < len(data):
        size = struct.unpack_from(">I", data, pos)[0]
        pos += 4
        kind = data[pos:pos + 4]
        pos += 4
        payload = data[pos:pos + size]
        pos += size
        crc = struct.unpack_from(">I", data, pos)[0]
        pos += 4
        assert zlib.crc32(kind + payload) & 0xffffffff == crc, f"PNG CRC: {path}"
        seen.append(kind)
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            assert compression == filtering == 0
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    assert seen[0] == b"IHDR" and seen[-1] == b"IEND" and b"IDAT" in seen
    assert pos == len(data), f"trailing PNG data: {path}"
    assert depth == 8 and color in (2, 6) and interlace == 0
    raw = zlib.decompress(compressed)
    channels = 4 if color == 6 else 3
    assert len(raw) == height * (width * channels + 1), f"PNG scanline length: {path}"
    return width, height

def main():
    proof = Path(sys.argv[1]).resolve()
    capture = Path(sys.argv[2]).resolve()
    manifest = json.loads((proof / "candidate-art-manifest.json").read_text(encoding="utf-8"))
    assert manifest["format"] == "NFSUG-UI-ART-CANDIDATES-1"
    assert manifest["complete"] is False
    assert len(manifest["assets"]) == 1
    row = manifest["assets"][0]
    key = row["source_hash"]
    assert row["source_kind"] == 5 and row["source_size"] == [240, 160]
    raw = (capture / f"{key}.rgba").read_bytes()
    assert len(raw) == 240 * 160 * 4
    assert source_hash(raw, 240, 160) == int(key, 16)
    source = (proof / row["source_export"]).resolve()
    assert png_info(source) == (240, 160)
    candidate = (proof / row["candidate"]).resolve()
    assert png_info(candidate) == (3240, 2160)
    assert row["candidate_size"] == [3240, 2160]
    assert hashlib.sha256(candidate.read_bytes()).hexdigest().upper() == row["candidate_sha256"]
    print(f"PASS: kind-5 source {key}, raw-pixel hash, source PNG, 3240x2160 candidate PNG, and incomplete/non-release manifest")

if __name__ == "__main__":
    main()
