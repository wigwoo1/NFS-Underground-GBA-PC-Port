"""Owned HUD row/display switch provenance, no framebuffer3D capture."""
from pathlib import Path
import struct,json,hashlib
p=Path(__file__).resolve().parent;checks=[]
for serial in [22,38]:
 hud=(p/f'road-bundle-{serial}-owned-hud.bin').read_bytes();palette=(p/f'road-bundle-{serial}-display-palette.bin').read_bytes();meta=json.loads((p/f'road-bundle-{serial}-display-palette.json').read_text());bundle=(p/f'road-bundle-{serial}.bin').read_bytes();h=struct.unpack_from('<8I',bundle);page=struct.unpack_from('<I',bundle,h[5]+20)[0]
 assert len(hud)==160*34944 and len(palette)==81920
 rows=[];runs=[]
 for y in range(160):
  row=hud[y*34944:(y+1)*34944];refresh,number=struct.unpack_from('<2I',row);display=struct.unpack_from('<H',row,8)[0]
  assert refresh==meta['refresh'] and number==y and row[32896:33408]==palette[y*512:(y+1)*512]
  record=dict(page=(display>>4)&1,mode=display&7,forced_blank=bool(display&128),obj_enabled=bool(display&4096),window_bits=(display>>13)&7,bg2_priority=struct.unpack_from('<H',row,20)[0]&3,blend=list(struct.unpack_from('<3H',row,88)))
  rows.append(record)
  if not runs or runs[-1]['state']!=record:runs.append(dict(begin=y,end=y+1,state=record))
  else:runs[-1]['end']=y+1
 mismatch=[i for i,row in enumerate(rows) if row['page']!=page]
 checks.append(dict(serial=serial,epoch=meta['epoch'],refresh=meta['refresh'],hud_sha256=hashlib.sha256(hud).hexdigest(),scene_page=page,rows_on_other_page=len(mismatch),runs=runs,complete_single_page_scene_hud_pair=not mismatch))
report=dict(result='AUDITED',checks=checks,scope='Original owned scanline OBJ/palette/OAM/register state, noBG3Dimage. Split page ownership must precede whole-frame HUD/live integration; cannot treat publication as complete display boundary.')
(p/'road-bundle-hud-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
