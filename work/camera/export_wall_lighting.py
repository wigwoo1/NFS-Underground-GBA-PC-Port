"""Retain lighting by surface identity; raw tables remain private replay data."""
from pathlib import Path
import os,struct,json
from scene_batches import batches
root=Path('work/camera');serial=int(os.environ.get('NF_REPLAY_SCENE','10'))
scene=list(batches(root/'shading.bin'))[serial]
roads=sum(e['pc']==0x030032f0 for e in scene['events'])
walls=[e for e in scene['events'] if e['pc']==0x03000304]
data=bytearray(struct.pack('<2I',0x314c464e,roads+len(walls)));shaded=0
for _ in range(roads):data.extend(struct.pack('<I',0))
for e in walls:
 b=e['blocks'];enabled=not(e['regs'][2]&256);data.extend(struct.pack('<I',enabled))
 if not enabled:continue
 shaded+=1;source=b[5][1];mat=b[8][1]
 width=1<<struct.unpack_from('<H',mat,36)[0];height=struct.unpack_from('<H',mat,38)[0]
 table=b[74][1];pixels=b[66][1];palette=struct.unpack('<256H',b[67][1])
 assert len(table)==4096 and len(pixels)==width*height
 data.extend(struct.pack('<4I',source[60],source[61],width,height))
 for level in range(16):
  for texel in pixels:
   color=palette[table[texel*16+level]]
   data.extend(bytes(((color&31)*255//31,((color>>5)&31)*255//31,((color>>10)&31)*255//31,255 if texel else 0)))
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
data.extend(rom[0x627700:0x627700+32768*4])
(root/'wall-lighting.bin').write_bytes(data)
report={'scene':serial,'surfaces':roads+len(walls),'shaded_walls':shaded,'variants_per_shaded_wall':16}
(root/'wall-lighting-input.json').write_text(json.dumps(report,indent=2));print(report)
