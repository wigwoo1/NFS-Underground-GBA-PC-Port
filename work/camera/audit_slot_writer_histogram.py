import json,sys,csv
from pathlib import Path
sys.path.insert(0,str(Path('work/tools').resolve()))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
r=json.loads(Path(sys.argv[1]).read_text());path=Path(r['model_pose_trace']).with_suffix('.slot-writers.csv');rows=list(csv.DictReader(path.open()));rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
for row in rows:
 pc=int(row['pc'],16);print(row)
 if 0x08000000<=pc<0x08800000:
  for i in cs.disasm(rom[pc-0x08000000-16:pc-0x08000000+20],pc-16):print(hex(i.address),i.mnemonic,i.op_str)
assert rows,'No source slot writers captured'

