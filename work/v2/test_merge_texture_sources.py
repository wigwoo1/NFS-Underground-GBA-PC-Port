"""Test hash-verified, atomic, deduplicating texture capture merges."""
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image

here = Path(__file__).resolve().parent
module_dir = here / "v2"
if not module_dir.is_dir():
    module_dir = here.parent / "v2"
if not module_dir.is_dir():
    module_dir = here
sys.path.insert(0, str(module_dir))

from build_texture_pack import source_hash
from merge_texture_sources import merge


def capture(root: Path, textures: list[tuple[int, int, bytes]],
            process_id: int | None = None, first_draw_serial: int = 0,
            renderer_metadata: dict[int, tuple[int, int]] | None = None) -> Path:
    root.mkdir()
    rows = []
    for index, (width, height, rgba) in enumerate(textures):
        key = source_hash(rgba, width, height)
        name = f"{key:016x}.png"
        Image.frombytes("RGBA", (width, height), rgba).save(root / name)
        row = {"hash": f"{key:016x}", "width": width, "height": height,
               "address": 0x08000000 + index * 4, "kind": 1,
               "source": name}
        if process_id is not None:
            row["first_seen_process_id"] = process_id
            row["first_seen_draw_serial"] = first_draw_serial + index
        if renderer_metadata and index in renderer_metadata:
            row["stride"], row["shade"] = renderer_metadata[index]
        rows.append(row)
    (root / "inventory.json").write_text(json.dumps({
        "format": "NFSUG-SOURCE-TEXTURE-INVENTORY-1", "complete": False,
        "coverage": "test fixture", "texture_count": len(rows), "textures": rows
    }), encoding="utf-8")
    return root


with tempfile.TemporaryDirectory(prefix="nfsug-merge-source-test-") as temp:
    root = Path(temp)
    shared = (2, 1, bytes((255, 0, 0, 255, 0, 255, 0, 128)))
    first_only = (1, 1, bytes((0, 0, 255, 255)))
    second_only = (1, 2, bytes((255, 255, 0, 255, 25, 50, 75, 0)))
    a = capture(root / "capture-a", [shared, first_only], process_id=4001, first_draw_serial=50,
                renderer_metadata={0: (64, 7)})
    b = capture(root / "capture-b", [shared, second_only], process_id=4002, first_draw_serial=308,
                renderer_metadata={0: (128, 9)})
    output = root / "merged"
    result = merge([a, b], output)
    assert result == {"complete": False, "texture_count": 3,
                      "unique_source_rgba_bytes": 20}
    manifest = json.loads((output / "inventory.json").read_text(encoding="utf-8"))
    assert len(manifest["capture_sets"]) == 2 and manifest["complete"] is False
    shared_key = f"{source_hash(shared[2], shared[0], shared[1]):016x}"
    entry = next(row for row in manifest["textures"] if row["hash"] == shared_key)
    assert entry["captures"] == [
        {"set_id": 0, "address": 0x08000000, "kind": 1, "stride": 64, "shade": 7,
         "first_seen_process_id": 4001, "first_seen_draw_serial": 50},
        {"set_id": 1, "address": 0x08000000, "kind": 1, "stride": 128, "shade": 9,
         "first_seen_process_id": 4002, "first_seen_draw_serial": 308},
    ], "duplicate source should retain address, process, and draw-serial provenance"
    with Image.open(output / entry["source"]) as image:
        assert image.size == shared[:2] and image.convert("RGBA").tobytes() == shared[2]
    try:
        merge([a, b], output)
    except FileExistsError:
        pass
    else:
        raise AssertionError("merge must not overwrite a prior inventory")

    legacy = capture(root / "capture-legacy", [shared])
    legacy_output = root / "merged-legacy"
    merge([legacy], legacy_output)
    legacy_manifest = json.loads((legacy_output / "inventory.json").read_text(encoding="utf-8"))
    legacy_key = f"{source_hash(shared[2], shared[0], shared[1]):016x}"
    legacy_entry = next(row for row in legacy_manifest["textures"] if row["hash"] == legacy_key)
    assert legacy_entry["captures"] == [{"set_id": 0, "address": 0x08000000, "kind": 1}], "legacy inventories should remain valid without draw-serial fields"

    incomplete_provenance = capture(root / "capture-incomplete-provenance", [shared], process_id=5001)
    incomplete_row = json.loads((incomplete_provenance / "inventory.json").read_text(encoding="utf-8"))
    del incomplete_row["textures"][0]["first_seen_draw_serial"]
    (incomplete_provenance / "inventory.json").write_text(json.dumps(incomplete_row), encoding="utf-8")
    incomplete_output = root / "failed-provenance"
    try:
        merge([incomplete_provenance], incomplete_output)
    except ValueError:
        pass
    else:
        raise AssertionError("partial draw provenance must be rejected")
    assert not incomplete_output.exists(), "failed provenance validation must not publish partial output"

    partial_renderer = capture(root / "capture-partial-renderer", [shared])
    partial_row = json.loads((partial_renderer / "inventory.json").read_text(encoding="utf-8"))
    partial_row["textures"][0]["stride"] = 64
    (partial_renderer / "inventory.json").write_text(json.dumps(partial_row), encoding="utf-8")
    partial_renderer_output = root / "failed-partial-renderer"
    try:
        merge([partial_renderer], partial_renderer_output)
    except ValueError:
        pass
    else:
        raise AssertionError("partial renderer metadata must be rejected")
    assert not partial_renderer_output.exists(), "partial renderer metadata must not publish output"

    invalid_renderer = capture(root / "capture-invalid-renderer", [shared])
    invalid_row = json.loads((invalid_renderer / "inventory.json").read_text(encoding="utf-8"))
    invalid_row["textures"][0].update(stride=64, shade=0x100000000)
    (invalid_renderer / "inventory.json").write_text(json.dumps(invalid_row), encoding="utf-8")
    invalid_renderer_output = root / "failed-invalid-renderer"
    try:
        merge([invalid_renderer], invalid_renderer_output)
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range renderer metadata must be rejected")
    assert not invalid_renderer_output.exists(), "invalid renderer metadata must not publish output"

    bad_provenance = capture(root / "capture-bad-provenance", [shared], process_id=5002)
    bad_row = json.loads((bad_provenance / "inventory.json").read_text(encoding="utf-8"))
    bad_row["textures"][0]["first_seen_process_id"] = -1
    (bad_provenance / "inventory.json").write_text(json.dumps(bad_row), encoding="utf-8")
    bad_provenance_output = root / "failed-bad-provenance"
    try:
        merge([bad_provenance], bad_provenance_output)
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range draw provenance must be rejected")
    assert not bad_provenance_output.exists(), "failed provenance validation must not publish partial output"

    bad = capture(root / "capture-bad", [shared])
    row = json.loads((bad / "inventory.json").read_text(encoding="utf-8"))
    row["textures"][0]["hash"] = "0000000000000000"
    (bad / "inventory.json").write_text(json.dumps(row), encoding="utf-8")
    failed = root / "failed"
    try:
        merge([a, bad], failed)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid source hash must be rejected")
    assert not failed.exists(), "failed validation must not publish partial output"

print("PASS: source hash validation, timed cache-key provenance merge, legacy compatibility, PNG parity, and atomic cleanup")
