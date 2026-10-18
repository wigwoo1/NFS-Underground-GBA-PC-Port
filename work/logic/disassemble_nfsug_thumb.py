"""Disassemble audited NFSUG ARM7TDMI/Thumb routine windows from the ROM."""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

PROJECT = next((p for p in Path(__file__).resolve().parents
                if (p / "work" / "tools" / "capstone" / "__init__.py").is_file()), None)
if PROJECT is None:
    raise FileNotFoundError("project work/tools/capstone is unavailable")
sys.path.insert(0, str(PROJECT / "work" / "tools"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

GBA_ROM_BASE = 0x08000000


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: disassemble_nfsug_thumb.py ROM OUTPUT.txt [START:END ...]")
    rom_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    ranges = [tuple(int(v, 16) for v in item.split(":")) for item in sys.argv[3:]]
    if not ranges:
        # Keep executable basic blocks separate around the literal/data pool at 0x0800977A.
        ranges = [
            (0x08009580, 0x08009680),
            (0x08009730, 0x08009744),
            (0x0800975C, 0x0800977A),
            (0x08009784, 0x080097A2),
            (0x080097AA, 0x080097F4),
        ]
    rom = rom_path.read_bytes()
    digest = hashlib.sha256(rom).hexdigest().upper()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    lines = ["NFS Underground GBA Thumb routine windows",
             f"ROM: {rom_path}", f"ROM SHA-256: {digest}",
             "Mode: ARM7TDMI Thumb, little-endian", ""]
    for start, end in ranges:
        if start < GBA_ROM_BASE or end <= start or end - GBA_ROM_BASE > len(rom):
            raise ValueError(f"range outside ROM: {start:#x}:{end:#x}")
        blob = rom[start - GBA_ROM_BASE:end - GBA_ROM_BASE]
        lines.append(f"[{start:08X}..{end:08X})")
        for insn in md.disasm(blob, start):
            raw = bytes(insn.bytes).hex(" ").upper()
            lines.append(f"{insn.address:08X}: {raw:<8} {insn.mnemonic:<8} {insn.op_str}")
        lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({len(lines)} lines); ROM SHA-256 {digest}")


if __name__ == "__main__":
    main()
