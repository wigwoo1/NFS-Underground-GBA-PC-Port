from pathlib import Path
import struct,json,hashlib
from owned_object_texture_reference import reference
p=Path('work/camera');raw=(p/'owned-object-textures.bin').read_bytes();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();offset=0;checks=[];missing=[]
def read(a,n):
 o=a-0x08000000
 if o<0 or o+n>len(rom):raise ValueError('Missing material source')
 return rom[o:o+n]
while offset<len(raw):
 h=struct.unpack_from('<12I',raw,offset);assert h[0]==0x31544f4e;data=raw[offset+48:offset+548];source=data[:164];state=data[164:420]
 assert reference(source,state,h[6],read)==(h[4],h[5],h[7],h[8])
 if not h[10]:missing.append(h[11])
 else:
  texture=raw[offset+548:offset+548+h[9]];assert len(texture)==h[9]
  if h[5]>=0x08000000:assert texture==read(h[5],h[9])
 checks.append(dict(refresh=h[1],model=struct.unpack_from('<h',source,54)[0],bytes=h[9],sha256=hashlib.sha256(raw[offset+548:offset+548+h[9]]).hexdigest(),dynamic=bool(struct.unpack_from('<H',source,10)[0]&8)));offset+=548+h[9]
assert checks and not missing
r=dict(result='PASS_OWNED_OBJECT_TEXTURE_SELECTION',records=len(checks),dynamic=sum(x['dynamic'] for x in checks),checks=checks,unique_payloads=len({x['sha256'] for x in checks}),scope='Executed raw object texture selection/payload capture; independent dynamic pixel parity pending; invisible variant ownership and model pose binding pending.')
(p/'owned-object-textures.json').write_text(json.dumps(r,indent=2));print(r['result'],r['records'],r['dynamic'])
