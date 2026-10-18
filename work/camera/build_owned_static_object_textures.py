from pathlib import Path
import struct,json,zlib
from owned_object_texture_reference import reference
p=Path('work/camera');raw=(p/'owned-graph-models.bin').read_bytes();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
def read(address,n):
 o=address-0x08000000
 if o<0 or o+n>len(rom):raise ValueError('Unowned static texture source')
 return bytes(rom[o:o+n])
seen=set();checks=[];target=p/'object-texture-assets';target.mkdir(exist_ok=True)
for pos in range(0,len(raw),580):
 h=struct.unpack_from('<8I',raw,pos);source=raw[pos+32:pos+196];state=raw[pos+196:pos+452];flags=struct.unpack_from('<H',source,10)[0]
 if flags&8:continue
 for depth in (256,2048):
  sprite,address,shift,height=reference(source,state,depth,read);key=(h[3],sprite,address)
  if key in seen:continue
  seen.add(key);size=(1<<shift)*height;texture=read(address,size);material=read(sprite,32)
  payload=material+texture;encoded=struct.pack('<9I',0x31544d4e,h[3],sprite,address,shift,height,size,flags,zlib.crc32(payload))+payload
  file=target/f'{h[3]}-{sprite:08x}.nta';file.write_bytes(encoded)
  checks.append(dict(model=h[3],billboard_forced=bool(flags&2),sprite=sprite,bytes=size,file=str(file)))
r=dict(result='PASS_OWNED_STATIC_OBJECT_TEXTURES',assets=len(checks),checks=checks,scope='ROM-exact eligible static sprite payloads including forced billboard path; live pose/dispatch integration pending.')
(p/'owned-static-object-textures.json').write_text(json.dumps(r,indent=2));print(r)
