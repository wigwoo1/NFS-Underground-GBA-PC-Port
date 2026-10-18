from pathlib import Path
import struct,json
from owned_object_dispatch import select
from owned_motion_pairs import records
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();references=[]
for file in (p/'motion-actual-scanline-assets').glob('*-native-complete-frame.bin'):
 frame=records(file.read_bytes());camera=next(bytes(r['blocks'][4 if r['kind']==1 else 3]) for r in frame['records'] if r['kind'] in (1,2))
 for r in frame['records']:
  if r['kind']==3:references.append((frame['refresh'],camera,bytes(r['blocks'][1]),bytes(r['blocks'][10])))
raw=(p/'owned-object-textures.bin').read_bytes();offset=0;checks=[]
while offset<len(raw):
 h=struct.unpack_from('<12I',raw,offset);source=raw[offset+48:offset+212];state=raw[offset+212:offset+468];camera=raw[offset+500:offset+548];texture=raw[offset+548:offset+548+h[9]]
 dispatch=select(source,state,h[6]);assert dispatch['kind']=='model'
 descriptor=rom[dispatch['descriptor']-0x08000000:dispatch['descriptor']-0x08000000+40]
 matches=[refresh for refresh,ca,desc,t in references if ca==camera and desc==descriptor and t==texture];assert len(matches)==1
 checks.append(dict(capture_refresh=h[1],closed_frame=matches[0],variant=dispatch['variant']));offset+=548+h[9]
# Raw graph contains two currently forced billboard objects; they must not become mesh draws.
raw=(p/'owned-graph-models.bin').read_bytes();billboards=0
for pos in range(0,len(raw),580):
 h=struct.unpack_from('<8I',raw,pos)
 if h[3] in (5,9):
  for depth in (256,2048):assert select(raw[pos+32:pos+196],raw[pos+196:pos+452],depth)['kind']=='billboard'
  billboards+=1
assert len(checks)==7 and billboards==16
r=dict(result='PASS_OWNED_OBJECT_DRAW_SELECTION',model_draws_exact=7,forced_billboard_references=billboards,checks=checks,scope='Original path/model variant identity verified; billboard geometry and full native pose binding pending.')
(p/'owned-object-dispatch.json').write_text(json.dumps(r,indent=2));print(r)
