"""Recover original model polygon dispatcher calls from the supplied ROM."""
import sys,json
from pathlib import Path
sys.path.insert(0,'work/pydeps')
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();cs=Cs(CS_ARCH_ARM,CS_MODE_ARM)
rows=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str) for i in cs.disasm(rom[0x71b0c+0x3d24:0x71b0c+0x3f30],0x03003d24)]
Path('work/camera/model-polygon-dispatch-disassembly.json').write_text(json.dumps(rows,indent=2))
for r in rows:
 if r['mnemonic'] in ('bl','bx'):print(r)
clip=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str) for i in cs.disasm(rom[0x71b0c+0x4270:0x71b0c+0x45e0],0x03004270)]
Path('work/camera/model-polygon-clip-disassembly.json').write_text(json.dumps(clip,indent=2))
print('clip instruction count',len(clip))
for r in clip[:24]:print(r['address'],r['mnemonic'],r['operands'])
