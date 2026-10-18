import json
import tempfile
import sys
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
from export_texture_sources import export


with tempfile.TemporaryDirectory(prefix="nfsug-source-export-test-") as temp:
    root = Path(temp)
    inventory = root / "captured"
    inventory.mkdir()
    rgba = bytes((255, 0, 0, 255, 0, 255, 0, 128, 0, 0, 255, 0, 25, 50, 75, 255))
    key = source_hash(rgba, 2, 2)
    (inventory / f"{key:016x}.rgba").write_bytes(rgba)
    (inventory / "source-inventory.tsv").write_text(
        f"{key:016x}\t2\t2\t08001234\t3\n", encoding="ascii")
    destination = root / "export"
    result = export(inventory, destination)
    assert result["texture_count"] == 1 and result["complete"] is False
    row = json.loads((destination / "inventory.json").read_text(encoding="utf-8"))["textures"][0]
    assert row["hash"] == f"{key:016x}" and row["address"] == 0x08001234 and row["kind"] == 3
    with Image.open(destination / row["source"]) as image:
        assert image.size == (2, 2)
        assert image.convert("RGBA").tobytes() == rgba

    timed_inventory = root / "captured-timed"
    timed_inventory.mkdir()
    (timed_inventory / f"{key:016x}.rgba").write_bytes(rgba)
    (timed_inventory / "source-inventory.tsv").write_text(
        f"{key:016x}\t2\t2\t0200d154\t2\t4321\t987\n", encoding="ascii")
    timed_result = export(timed_inventory, root / "export-timed")
    timed_row = json.loads((root / "export-timed" / "inventory.json").read_text(encoding="utf-8"))["textures"][0]
    assert timed_result["texture_count"] == 1
    assert timed_row["first_seen_process_id"] == 4321 and timed_row["first_seen_draw_serial"] == 987

    renderer_inventory = root / "captured-renderer-metadata"
    renderer_inventory.mkdir()
    (renderer_inventory / f"{key:016x}.rgba").write_bytes(rgba)
    (renderer_inventory / "source-inventory.tsv").write_text(
        f"{key:016x}\t2\t2\t0200d154\t2\t256\t7\t4321\t988\n", encoding="ascii")
    renderer_result = export(renderer_inventory, root / "export-renderer-metadata")
    renderer_row = json.loads((root / "export-renderer-metadata" / "inventory.json").read_text(encoding="utf-8"))["textures"][0]
    assert renderer_result["texture_count"] == 1
    assert renderer_row["stride"] == 256 and renderer_row["shade"] == 7
    assert renderer_row["first_seen_process_id"] == 4321 and renderer_row["first_seen_draw_serial"] == 988

    # UI captures use distinct renderer kinds so menu frames and transparent
    # HUD overlays remain identifiable in the exported review inventory.
    for ui_kind in (4, 5):
        ui_inventory = root / f"captured-ui-kind-{ui_kind}"
        ui_inventory.mkdir()
        (ui_inventory / f"{key:016x}.rgba").write_bytes(rgba)
        (ui_inventory / "source-inventory.tsv").write_text(
            f"{key:016x}\t2\t2\tffffffff\t{ui_kind}\t240\t0\t4321\t999\n",
            encoding="ascii")
        ui_result = export(ui_inventory, root / f"export-ui-kind-{ui_kind}")
        ui_row = json.loads((root / f"export-ui-kind-{ui_kind}" / "inventory.json")
                            .read_text(encoding="utf-8"))["textures"][0]
        assert ui_result["texture_count"] == 1
        assert ui_row["kind"] == ui_kind
        assert ui_row["stride"] == 240 and ui_row["shade"] == 0
        assert ui_row["first_seen_process_id"] == 4321
        assert ui_row["first_seen_draw_serial"] == 999
        with Image.open(root / f"export-ui-kind-{ui_kind}" / ui_row["source"]) as image:
            assert image.convert("RGBA").tobytes() == rgba

    partial_renderer_inventory = root / "captured-partial-renderer-metadata"
    partial_renderer_inventory.mkdir()
    (partial_renderer_inventory / f"{key:016x}.rgba").write_bytes(rgba)
    (partial_renderer_inventory / "source-inventory.tsv").write_text(
        f"{key:016x}\t2\t2\t0200d154\t2\t256\t7\t4321\n", encoding="ascii")
    try:
        export(partial_renderer_inventory, root / "failed-partial-renderer-metadata")
    except ValueError:
        pass
    else:
        raise AssertionError("Partial renderer metadata row was accepted")

    malformed_schema = root / "bad-schema"
    malformed_schema.mkdir()
    (malformed_schema / f"{key:016x}.rgba").write_bytes(rgba)
    (malformed_schema / "source-inventory.tsv").write_text(
        f"{key:016x}\t2\t2\t08001234\t3\t4321\n", encoding="ascii")
    try:
        export(malformed_schema, root / "failed-schema")
    except ValueError:
        pass
    else:
        raise AssertionError("Partially extended provenance row was accepted")
    assert not (root / "failed-schema").exists()

    bad_inventory = root / "bad"
    bad_inventory.mkdir()
    (bad_inventory / f"{key:016x}.rgba").write_bytes(rgba[:-1])
    (bad_inventory / "source-inventory.tsv").write_text(
        f"{key:016x}\t2\t2\t08001234\t3\n", encoding="ascii")
    failed = root / "failed"
    try:
        export(bad_inventory, failed)
    except ValueError:
        pass
    else:
        raise AssertionError("Malformed source blob was accepted")
    assert not failed.exists(), "failed conversion must not publish a partial inventory"

print("PASS: legacy and timed RGBA inventories, provenance, PNG parity, and atomic failure cleanup")
