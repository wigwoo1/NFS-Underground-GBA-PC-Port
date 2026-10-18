import importlib.util
import json
import hashlib
import struct
import tempfile
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).with_name("build_texture_pack.py")
spec = importlib.util.spec_from_file_location("build_texture_pack", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def write_image(path: Path, size, pixels):
    image = Image.new("RGBA", size)
    image.putdata(pixels)
    image.save(path)


def write_coverage_audit(root: Path, name: str, hashes: list[str], *, status="complete") -> Path:
    inventory = {"format": "NFSUG-SOURCE-TEXTURE-INVENTORY-1", "complete": True,
                 "coverage": "complete synthetic fixture", "texture_count": len(hashes),
                 "textures": [{"hash": value} for value in hashes]}
    inventory_path = root / f"{name}-inventory.json"
    inventory_bytes = json.dumps(inventory).encode("utf-8")
    inventory_path.write_bytes(inventory_bytes)
    audit_path = root / name
    audit = {"format": module.COVERAGE_FORMAT, "status": status,
             "source_hashes": hashes, "inventory_path": inventory_path.name,
             "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest()}
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    return audit_path


with tempfile.TemporaryDirectory(prefix="nfsug-texture-pack-") as temp:
    root = Path(temp)
    source = root / "source.png"
    upscaled = root / "upscaled.png"
    write_image(source, (2, 2), [(1, 2, 3, 255), (4, 5, 6, 128), (7, 8, 9, 0), (10, 11, 12, 255)])
    write_image(upscaled, (8, 8), [(i, i ^ 0x55, 255 - i, 255) for i in range(64)])
    source_rgba, source_width, source_height = module.load_rgba(source)
    source_key = module.source_hash(source_rgba, source_width, source_height)
    audit = write_coverage_audit(root, "coverage-audit.json", [f"{source_key:016x}"])
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"format": module.FORMAT, "complete": True,
                                    "coverage_audit": "coverage-audit.json",
                                    "textures": [{"source": "source.png", "upscaled": "upscaled.png"}]}), encoding="utf-8")
    output = root / "game" / "textures"
    result = module.build(manifest, output)
    assert result["textures"] == 1
    original, width, height = module.load_rgba(source)
    key = module.source_hash(original, width, height)
    asset = output / "4k" / f"{key:016x}.rgba"
    raw = asset.read_bytes()
    magic, version, w, h, stored_hash = raw[:4], *struct.unpack("<IIIQ", raw[4:24])
    assert (magic, version, w, h, stored_hash) == (b"NFGX", 1, 8, 8, key)
    with Image.open(upscaled) as image:
        assert raw[24:] == image.convert("RGBA").tobytes()
    assert (output / "4k" / "pack.ready").read_bytes() == module.READY
    try:
        module.build(manifest, output)
    except FileExistsError:
        pass
    else:
        raise AssertionError("Existing pack was overwritten")

    bad_manifest = root / "bad.json"
    write_image(root / "small.png", (3, 8), [(0, 0, 0, 255)] * 24)
    bad_manifest.write_text(json.dumps({"format": module.FORMAT,
                                       "textures": [{"source": "source.png", "upscaled": "small.png"}]}), encoding="utf-8")
    failed_output = root / "bad-pack"
    try:
        module.build(bad_manifest, failed_output, preview=True)
    except ValueError:
        pass
    else:
        raise AssertionError("Under-scaled texture was accepted")
    assert not failed_output.exists(), "failed build must not publish a partial pack"

    flat = root / "flat.png"
    write_image(flat, (8, 8), [(255, 0, 255, 255)] * 64)
    flat_manifest = root / "flat-manifest.json"
    flat_manifest.write_text(json.dumps({"format": module.FORMAT,
                                         "textures": [{"source": "source.png", "upscaled": "flat.png"}]}), encoding="utf-8")
    flat_output = root / "flat-pack"
    try:
        module.build(flat_manifest, flat_output, preview=True)
    except ValueError as error:
        assert "flat-color probe" in str(error)
    else:
        raise AssertionError("Flat-color probe replacement was accepted")
    assert not flat_output.exists(), "flat-color rejection must not publish a ready pack"
    assert not list(root.glob("flat-pack.building-*")), "flat-color failure must clean its staging directory"

    preview_manifest = root / "preview-manifest.json"
    preview_manifest.write_text(json.dumps({"format": module.FORMAT,
        "textures": [{"source": "source.png", "upscaled": "upscaled.png"}]}), encoding="utf-8")
    preview_output = root / "preview-pack"
    preview_result = module.build(preview_manifest, preview_output, preview=True)
    assert preview_result["complete"] is False
    assert (preview_output / "4k" / "pack.preview").exists()
    assert not (preview_output / "4k" / "pack.ready").exists(), "preview must never activate runtime selector"

    incomplete_audit = write_coverage_audit(
        root, "incomplete-audit.json", [f"{source_key:016x}"], status="incomplete"
    )
    incomplete_manifest = root / "incomplete-manifest.json"
    incomplete_manifest.write_text(json.dumps({"format": module.FORMAT,
        "coverage_audit": "incomplete-audit.json",
        "textures": [{"source": "source.png", "upscaled": "upscaled.png"}]}), encoding="utf-8")
    incomplete_output = root / "incomplete-pack"
    try:
        module.build(incomplete_manifest, incomplete_output)
    except ValueError as error:
        assert "complete coverage audit" in str(error)
    else:
        raise AssertionError("Incomplete coverage audit published a release pack")
    assert not incomplete_output.exists()

    mismatch_audit = write_coverage_audit(
        root, "mismatch-audit.json", [f"{source_key:016x}", "0000000000000001"]
    )
    mismatch_manifest = root / "mismatch-manifest.json"
    mismatch_manifest.write_text(json.dumps({"format": module.FORMAT,
        "coverage_audit": "mismatch-audit.json",
        "textures": [{"source": "source.png", "upscaled": "upscaled.png"}]}), encoding="utf-8")
    mismatch_output = root / "mismatch-pack"
    try:
        module.build(mismatch_manifest, mismatch_output)
    except ValueError as error:
        assert "audited source set" in str(error)
    else:
        raise AssertionError("Manifest omitting an audited source hash was accepted")
    assert not mismatch_output.exists()
    assert not list(root.glob("mismatch-pack.building-*")), "coverage failure must clean its staging directory"

    digest_audit = write_coverage_audit(root, "digest-audit.json", [f"{source_key:016x}"])
    digest_record = json.loads(digest_audit.read_text(encoding="utf-8"))
    digest_record["inventory_sha256"] = "0" * 64
    digest_audit.write_text(json.dumps(digest_record), encoding="utf-8")
    digest_manifest = root / "digest-manifest.json"
    digest_manifest.write_text(json.dumps({"format": module.FORMAT,
        "coverage_audit": digest_audit.name,
        "textures": [{"source": "source.png", "upscaled": "upscaled.png"}]}), encoding="utf-8")
    digest_output = root / "digest-pack"
    try:
        module.build(digest_manifest, digest_output)
    except ValueError as error:
        assert "inventory digest" in str(error)
    else:
        raise AssertionError("Coverage audit with a stale inventory digest was accepted")
    assert not digest_output.exists()

print("PASS: NFGX payload, digest-bound complete inventory, exact audited-set match, incomplete-audit rejection, non-activating preview, overwrite refusal, cleanup, and flat-color probe rejection")
