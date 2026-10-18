from pathlib import Path
import struct,json,collections
from owned_motion_pairs import records
p=Path('work/camera');raw=(p/'owned-portal-graphs.bin').read_bytes();offset=0;graphs={}
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);offset+=32;assert h[0]==0x3147504e and h[6]==1;data=raw[offset:offset+h[5]];offset+=h[5];cursor=0;nodes={}
 for i in range(h[4]):
  index,n,desc,points=struct.unpack_from('<4I',data,cursor);cursor+=16;descriptor=bytes(data[cursor:cursor+48]);cursor+=48;ring=bytes(data[cursor:cursor+n*68]);cursor+=n*68;nodes[index]=(descriptor,ring)
 graphs[h[1]]=nodes
# Relate graph capture and closed scene by exact owned raw camera, not label arithmetic.
tr=(p/'owned-traversals.bin').read_bytes();offset=0;cameras={}
while offset<len(tr):
 h=struct.unpack_from('<12I',tr,offset);offset+=48
 if h[1]==1:
  data=tr[offset:offset+432+h[9]*68];offset+=len(data);cameras[h[2]]=bytes(data[304:352])
 else:offset+=h[5]
checks=[]
for f in sorted((p/'motion-actual-scanline-assets').glob('*-native-complete-frame.bin')):
 scene=records(f.read_bytes());camera=next(bytes(r['blocks'][4 if r['kind']==1 else 3]) for r in scene['records'] if r['kind'] in (1,2));source=next(k for k,v in cameras.items() if v==camera);graph=graphs[source]
 for i,r in enumerate(scene['records']):
  if r['kind']==3:continue
  geometry=bytes(r['blocks'][0]);matches=[]
  for index,(descriptor,ring) in graph.items():
   if r['kind']==1:
    if geometry==ring:matches.append(index)
   else:
    n=len(ring)//68
    for j in range(n):
     pair=ring[j*68:(j+1)*68]+ring[((j+1)%n)*68:((j+1)%n)*68+68]
     if pair==geometry:matches.append(index);break
  checks.append(dict(refresh=scene['refresh'],source_refresh=source,draw=i,kind=r['kind'],regions=matches))
r=dict(result='RAW_DRAW_REGION_PROVENANCE_AUDIT',draws=len(checks),counts=dict(collections.Counter('unique' if len(x['regions'])==1 else 'missing' if not x['regions'] else 'ambiguous' for x in checks)),checks=checks,scope='Exact raw vertex ring/edge identity only; no screen matching. Ambiguous sources require additional descriptor provenance.')
(p/'owned-draw-region-audit.json').write_text(json.dumps(r,indent=2));print(r['counts'])
