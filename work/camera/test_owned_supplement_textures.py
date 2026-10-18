from pathlib import Path
import struct,json,hashlib
from owned_material_resolution import resolve
p=Path('work/camera');geometry=(p/'owned-supplement-geometry.bin').read_bytes();offset=0;expected=[]
while offset<len(geometry):
 h=struct.unpack_from('<8I',geometry,offset);data=geometry[offset+32:offset+32+h[5]]
 for edge in range(h[4]):
  v=data[944+edge*140:944+(edge+1)*140];expected.append((h[1],h[3],edge,struct.unpack_from('<H',v,44)[0],v[100:132],v[132:140],struct.unpack_from('<I',data,176)[0]))
 offset+=32+h[5]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();raw=(p/'owned-supplement-textures.bin').read_bytes();offset=0;checks=[];missing=[]
while offset<len(raw):
 h=struct.unpack_from('<12I',raw,offset);assert h[0]==0x3154534e;source=raw[offset+48:offset+120];texture=raw[offset+120:offset+120+h[10]];e=expected[len(checks)+len(missing)];assert (h[1],h[3],h[4],h[5])==e[:4]
 if not h[11]:missing.append(dict(refresh=h[1],descriptor=h[3],edge=h[4],material=h[5]))
 else:
  assert source[:32]==e[4] and source[32:40]==e[5]
  metadata=resolve(h[5],source[32:40],{h[5]+h[6]:source[40:72]},e[6]);assert (metadata['address'],metadata['bytes'],metadata['shift'],metadata['height'])==(h[9],h[10],h[7],h[8])
  assert 0x08000000<=h[9] and h[9]+h[10]<=0x08000000+len(rom)
  assert texture==rom[h[9]-0x08000000:h[9]-0x08000000+h[10]]
  checks.append(dict(refresh=h[1],descriptor=h[3],edge=h[4],bytes=h[10],sha256=hashlib.sha256(texture).hexdigest()))
 offset+=120+h[10]
assert len(checks)+len(missing)==len(expected)==36
r=dict(result='PASS_SUPPLEMENT_TEXTURE_PAYLOAD_PROVENANCE',owned=len(checks),missing=missing,payload_bytes=sum(x['bytes'] for x in checks),checks=checks,scope='Every supplemental edge attempted; unresolved entries explicit, live transport pending.')
(p/'owned-supplement-textures.json').write_text(json.dumps(r,indent=2));print(r['result'],r['owned'],r['missing'],r['payload_bytes'])
