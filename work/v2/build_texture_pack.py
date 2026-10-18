"""Build validated NFGX texture packs, or non-activating preview packs.

Release packs require a separately reviewed coverage audit whose source hashes
exactly match the manifest. Preview builds never publish pack.ready.
"""
import argparse
import hashlib
import json
import re
import shutil
import struct
import tempfile
from pathlib import Path

from PIL import Image
from texture_hash import source_hash

MAGIC = b"NFGX"
FORMAT = "NFSUG-UPCALED-TEXTURE-SOURCES-1"
COVERAGE_FORMAT = "NFSUG-TEXTURE-COVERAGE-AUDIT-1"
READY = b"NFSUG-UPSCALED-TEXTURES 1\ncomplete=1\n"
PREVIEW = b"NFSUG-UPSCALED-TEXTURES 1\ncomplete=0\n"
MAX_DIM = 4096
MAX_PIXELS = MAX_DIM * MAX_DIM
HASH_RE = re.compile(r"^[0-9a-f]{16}$")


def load_rgba(path: Path) -> tuple[bytes, int, int]:
    with Image.open(path) as source:
        image = source.convert("RGBA")
        width, height = image.size
        if not width or not height or width * height > MAX_PIXELS:
            raise ValueError(f"Invalid or oversized texture: {path}")
        return image.tobytes(), width, height


def _sampled_composite_colors(path: Path) -> int:
    # Bound quality checking to 64x64 and composite alpha against black so
    # hidden RGB bytes cannot disguise a flat-color swatch.
    with Image.open(path) as source:
        sample = source.convert("RGBA")
    sample.thumbnail((64, 64), Image.Resampling.NEAREST)
    background = Image.new("RGBA", sample.size, (0, 0, 0, 255))
    visible = Image.alpha_composite(background, sample).convert("RGB")
    return len(visible.getcolors(maxcolors=64 * 64) or ())


def _is_flat_color_probe(source_path: Path, upscaled_path: Path) -> bool:
    return (
        _sampled_composite_colors(source_path) > 3
        and _sampled_composite_colors(upscaled_path) <= 2
    )


def _load_complete_coverage(path: Path) -> set[str]:
    audit = json.loads(path.read_text(encoding="utf-8"))
    if audit.get("format") != COVERAGE_FORMAT or audit.get("status") != "complete":
        raise ValueError(
            "Release build requires a separately reviewed complete coverage audit"
        )
    hashes = audit.get("source_hashes")
    if not isinstance(hashes, list) or not hashes:
        raise ValueError("Coverage audit must list every required source texture hash")
    if any(not isinstance(item, str) or not HASH_RE.fullmatch(item) for item in hashes):
        raise ValueError(
            "Coverage audit hashes must be 16-character lowercase hexadecimal values"
        )
    if len(set(hashes)) != len(hashes):
        raise ValueError("Coverage audit contains duplicate source hashes")

    inventory_name = audit.get("inventory_path")
    inventory_digest = audit.get("inventory_sha256")
    if not isinstance(inventory_name, str) or not inventory_name:
        raise ValueError("Coverage audit must identify its source inventory")
    if not isinstance(inventory_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", inventory_digest):
        raise ValueError("Coverage audit must include the inventory SHA-256")
    inventory_path = (path.parent / inventory_name).resolve()
    inventory_bytes = inventory_path.read_bytes()
    if hashlib.sha256(inventory_bytes).hexdigest() != inventory_digest:
        raise ValueError("Coverage inventory digest does not match the reviewed audit")
    inventory = json.loads(inventory_bytes.decode("utf-8"))
    if inventory.get("format") != "NFSUG-SOURCE-TEXTURE-INVENTORY-1":
        raise ValueError("Coverage audit references an unsupported source inventory")
    if inventory.get("complete") is not True:
        raise ValueError("Coverage inventory is not marked complete")
    inventory_textures = inventory.get("textures")
    if not isinstance(inventory_textures, list) or not inventory_textures:
        raise ValueError("Complete coverage inventory has no texture records")
    inventory_hashes = [row.get("hash") for row in inventory_textures if isinstance(row, dict)]
    if len(inventory_hashes) != len(inventory_textures):
        raise ValueError("Coverage inventory contains malformed texture records")
    if any(not isinstance(item, str) or not HASH_RE.fullmatch(item) for item in inventory_hashes):
        raise ValueError("Coverage inventory contains invalid source hashes")
    if len(set(inventory_hashes)) != len(inventory_hashes) or set(inventory_hashes) != set(hashes):
        raise ValueError("Coverage audit hashes do not exactly match its source inventory")
    return set(hashes)


def build(manifest_path: Path, output_path: Path, *, preview: bool = False) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != FORMAT:
        raise ValueError("Manifest must use the supported texture format")
    entries = manifest.get("textures")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Texture manifest must contain at least one entry")

    expected = None
    if not preview:
        coverage_name = manifest.get("coverage_audit")
        if not isinstance(coverage_name, str) or not coverage_name:
            raise ValueError(
                "Release build requires coverage_audit; use --preview for diagnostics"
            )
        audit_path = (manifest_path.parent / coverage_name).resolve()
        expected = _load_complete_coverage(audit_path)
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing texture pack: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=output_path.name + ".building-", dir=output_path.parent)
    )
    pack_dir = stage / "textures" / "4k"
    pack_dir.mkdir(parents=True)
    seen = set()
    try:
        base = manifest_path.parent
        for index, row in enumerate(entries):
            if not isinstance(row, dict) or set(row) != {"source", "upscaled"}:
                raise ValueError(
                    f"Texture row {index} must contain source and upscaled paths"
                )
            source_path = (base / row["source"]).resolve()
            upscale_path = (base / row["upscaled"]).resolve()
            original, original_width, original_height = load_rgba(source_path)
            upscaled, upscaled_width, upscaled_height = load_rgba(upscale_path)
            if (
                upscaled_width < 2 * original_width
                or upscaled_height < 2 * original_height
            ):
                raise ValueError(
                    f"Upscaled image must be at least 2x in both dimensions: {upscale_path}"
                )
            if _is_flat_color_probe(source_path, upscale_path):
                raise ValueError(
                    f"Replacement collapses a detailed source to a flat-color probe: {upscale_path}"
                )

            key = source_hash(original, original_width, original_height)
            hex_key = f"{key:016x}"
            if hex_key in seen:
                raise ValueError(f"Duplicate source texture hash at manifest row {index}")
            seen.add(hex_key)
            header = MAGIC + struct.pack(
                "<IIIQ", 1, upscaled_width, upscaled_height, key
            )
            (pack_dir / f"{hex_key}.rgba").write_bytes(header + upscaled)

        if expected is not None:
            missing = expected - seen
            unexpected = seen - expected
            if missing or unexpected:
                raise ValueError(
                    "Manifest does not exactly match the audited source set "
                    f"(missing={len(missing)}, unexpected={len(unexpected)})"
                )

        # Preview output cannot activate the selector, even when copied beside
        # the executable. Release marker appears only after coverage validation.
        marker = "pack.preview" if preview else "pack.ready"
        marker_bytes = PREVIEW if preview else READY
        (pack_dir / marker).write_bytes(marker_bytes)
        (stage / "textures").replace(output_path)
        try:
            stage.rmdir()
        except OSError:
            pass
        return {
            "format": FORMAT,
            "textures": len(seen),
            "complete": not preview,
            "output": str(output_path),
        }
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest", type=Path, help="JSON manifest with exact source/upscaled PNG pairs"
    )
    parser.add_argument(
        "output", type=Path, help="new executable-relative textures directory"
    )
    parser.add_argument(
        "--preview", action="store_true", help="build diagnostic pack without pack.ready"
    )
    args = parser.parse_args()
    result = build(args.manifest, args.output, preview=args.preview)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
