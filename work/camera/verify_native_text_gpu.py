"""Verify owned text composition against independent original RGB and no-text GPU frame."""
from pathlib import Path
from PIL import Image
import json, math, sys
p=Path('work/camera/prototype-runs')
new=p/'threaded-prepared-88919ce6c97e43149ed1d12385024975-dense-01'
old=p/'threaded-prepared-0da89dace5e447afa3eef1d10f4c279a-dense-01'
assert Path(str(new)+'-native-scene.bin').read_bytes()==Path(str(old)+'-native-scene.bin').read_bytes()
assert Path(str(new)+'-owned-hud.bin').read_bytes()==Path(str(old)+'-owned-hud.bin').read_bytes()
a=Image.open(str(new)+'-native.ppm');b=Image.open(str(old)+'-native.ppm');assert a.size==b.size==(3840,2160)
text=Path(str(new)+'-owned-text.bin').read_bytes();original=max(p.glob('*-original-pixels-3620.bin'),key=lambda q:q.stat().st_mtime).read_bytes()
assert len(text)==76800 and len(original)==153600
ap=a.load();bp=b.load();covered=changed=checked=outside=0
for y in range(2160):
 cell_y=int((y+.5)//13.5)
 for x in range(3840):
  cell_x=math.floor((x+.5-300)/13.5)
  active=0<=cell_x<240 and bool(text[cell_y*480+240+cell_x])
  if active:
   checked+=1;i=(cell_y*240+cell_x)*4;assert ap[x,y]==tuple(original[i:i+3]),(x,y,ap[x,y],tuple(original[i:i+3]))
  if ap[x,y]!=bp[x,y]:
   changed+=1
   if not active:outside+=1
assert changed>0 and outside==0
report=dict(result='PASS',owned_text_cells=sum(text[y*480+240+x] for y in range(160) for x in range(240)),checked_4k_text_pixels=checked,changed_gpu_pixels=changed,changed_outside_owned_text=outside,scene_packet_and_hud_equal=True,scope='Single held selection refresh3620; original final RGB over every owned text pixel at4K. No fullscene timing or moving text proof.')
Path('work/camera/native-text-gpu-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
