from pathlib import Path
import struct,json,collections
p=Path('work/camera');raw=(p/'owned-portal-graphs.bin').read_bytes();offset=0;expected={}
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);data=raw[offset+32:offset+32+h[5]];cursor=0;indices=set()
 for n in range(h[4]):
  _,vertices,_,_=struct.unpack_from('<4I',data,cursor);cursor+=16;desc=data[cursor:cursor+48];cursor+=48;indices.update([struct.unpack_from('<H',desc,4)[0],struct.unpack_from('<H',desc,8)[0]])
  for j in range(vertices):indices.add(struct.unpack_from('<H',data,cursor+j*68+44)[0])
  cursor+=vertices*68
 expected[h[1]]=indices-{65535};offset+=32+h[5]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();raw=(p/'owned-graph-materials.bin').read_bytes();offset=0;seen=collections.defaultdict(set);textures={};refresh=None;counts=collections.Counter();missing=[];payload_bytes=0
while offset<len(raw):
 h=struct.unpack_from('<12I',raw,offset);assert h[0]==0x314d474e;source=raw[offset+48:offset+120];mode=h[9]
 if refresh!=h[1]:textures={};refresh=h[1]
 assert h[3] not in seen[refresh];seen[refresh].add(h[3]);counts[mode]+=1
 if mode==0:missing.append((refresh,h[3],h[5],h[6],h[8]))
 else:
  assert struct.unpack_from('<H',source,34)[0]==h[4]
  assert struct.unpack_from('<H',source,66)[0]==h[5] and struct.unpack_from('<H',source,50)[0]==h[6]
  assert (h[11]+struct.unpack_from('<I',source,44)[0])&0xffffffff==h[7]
  if mode==1:
   texture=raw[offset+120:offset+120+h[8]];assert len(texture)==h[8];assert texture==rom[h[7]-0x08000000:h[7]-0x08000000+h[8]];textures[h[10]]=(h[7],h[8],texture);payload_bytes+=h[8]
  elif mode==2:assert textures[h[10]][:2]==(h[7],h[8])
  else:assert mode==3 and h[8]==0
 offset+=120+(h[8] if mode==1 else 0)
assert dict(seen)==expected
assert not missing,missing
r=dict(result='PASS_GRAPH_MATERIAL_SOURCE_COVERAGE',scenes=len(expected),materials=sum(map(len,seen.values())),modes=dict(counts),missing=missing,payload_bytes=payload_bytes,scope='All requested graph edge/floor/ceiling material indices covered; zero unresolved in sampled scenes; live transport pending.')
(p/'owned-graph-materials.json').write_text(json.dumps(r,indent=2));print(r)
