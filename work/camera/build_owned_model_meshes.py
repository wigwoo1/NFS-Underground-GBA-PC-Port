from pathlib import Path
import struct,json,zlib
from owned_object_model_reference import descriptors
p=Path('work/camera');raw=(p/'owned-graph-models.bin').read_bytes();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
def read(address,n):
 offset=address-0x08000000
 if n<0 or offset<0 or offset+n>len(rom):raise ValueError('Missing mesh source')
 return bytes(rom[offset:offset+n])
target=p/'model-assets';target.mkdir(exist_ok=True);checks=[];seen=set();hidden=0
for pos in range(0,len(raw),580):
 h=struct.unpack_from('<8I',raw,pos);source=raw[pos+32:pos+196];state=raw[pos+196:pos+452];reference=descriptors(source,state)
 if reference is None:hidden+=1;continue
 for variant in range(2):
  key=(h[3],variant)
  if key in seen:continue
  seen.add(key);desc=raw[pos+500+variant*40:pos+540+variant*40]
  n=struct.unpack_from('<H',desc,36)[0];nf=struct.unpack_from('<H',desc,34)[0];assert 0<n<=2048 and 0<nf<=512
  word=lambda data,o:struct.unpack_from('<I',data,o)[0]
  vertices=read(word(state,128)+word(desc,0)*6,n*6);faces=read(word(state,156)+word(desc,28),nf);assert all(3<=x<=32 for x in faces);corners=sum(faces)
  vi=read(word(state,132)+word(desc,4)*2,corners*2);ui=read(word(state,136)+word(desc,24)*2,corners*2)
  indices=struct.unpack('<'+'H'*corners,vi);uv_indices=struct.unpack('<'+'H'*corners,ui);assert max(indices)<n
  uv_count=max(uv_indices)+1;assert uv_count<=4096
  uv_address=word(state,144)+(word(desc,8)*4 if struct.unpack_from('<H',desc,32)[0]&1 else 0);uv=read(uv_address,uv_count*4)
  blocks=(desc,vertices,faces,vi,ui,uv);payload=struct.pack('<6I',*map(len,blocks))+b''.join(blocks)
  encoded=struct.pack('<9I',0x31414d4e,h[3],variant,n,nf,corners,uv_count,len(payload),zlib.crc32(payload))+payload
  (target/f'{h[3]}-{variant}.nma').write_bytes(encoded);checks.append(dict(model=h[3],variant=variant,vertices=n,faces=nf,corners=corners,bytes=len(encoded)))
r=dict(result='PASS_OWNED_MODEL_MESH_TOPOLOGY',assets=len(checks),hidden_references_excluded=hidden,checks=checks,scope='Raw eligible model descriptor/vertices/faces/indices/UV ownership; texture and pose binding/live transport pending.')
(p/'owned-model-meshes.json').write_text(json.dumps(r,indent=2));print(r)
