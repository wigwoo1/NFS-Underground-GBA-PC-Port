from pathlib import Path
import ctypes as C,json,struct,hashlib
from scene_batches import records
p=Path('work/camera');trace=p/'stable-original-source-8775-8779.bin';events=list(records(trace));roads=json.loads((p/'stable-original-road-source.json').read_text())['roads'];rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));prepare=d.nfs_visibility_wall_prepare;prepare.argtypes=[C.c_void_p]*4+[Read,C.c_void_p,C.c_void_p,C.c_void_p];clip=d.nfs_visibility_wall_clip;clip.argtypes=[C.c_void_p]*3+[C.c_int,C.c_uint,C.c_uint,C.c_void_p];emit=d.nfs_visibility_surface_vertices;emit.argtypes=[C.c_void_p]*6+[C.c_size_t,C.c_void_p];checks=[]
for road in roads:
 source=road['source'];before=max((e for e in events if e['id']<road['event'] and e['pc']==0x03001800 and e['blocks'][4][0]==source),key=lambda e:e['id']);after=min((e for e in events if before['id']<e['id']<road['event'] and e['pc']==0x03002964 and e['blocks'][4][0]==source),key=lambda e:e['id']);blocks=before['blocks']
 def fetch(address,size):
  if 0x08000000<=address and address+size<=0x08000000+len(rom):return rom[address-0x08000000:address-0x08000000+size]
  for base,data in list(blocks.values())+[(v['address'],bytes.fromhex(v['hex'])) for v in road['blocks'].values()]:
   if base<=address and address+size<=base+len(data):return data[address-base:address-base+size]
  raise ValueError((hex(address),size))
 @Read
 def read(user,address,target,size):
  C.memmove(target,fetch(address,size),size);return 1
 state=blocks[1][1];desc=blocks[4][1];vertices=blocks[5][1];u32=lambda b,o:struct.unpack_from('<I',b,o)[0];u16=lambda b,o:struct.unpack_from('<H',b,o)[0];proj=fetch(u32(state,0x50),32);matrix=fetch(u32(state,0x54),48);bases=[u32(matrix,0x28)]*2;face=u16(desc,10)
 if face!=65535:
  material=fetch(u32(state,0x1c)+face*20,20);bases[0]+=struct.unpack_from('<h',material,6)[0];bases[1]+=struct.unpack_from('<h',material,4)[0]
 material=fetch(u32(state,0x20)+(u16(desc,8) or u16(desc,4))*32,32);affine=u32(bytes.fromhex(road['blocks']['69']['hex']),0)&1;params=(C.c_uint32*6)(u32(proj,28),struct.unpack_from('<h',proj,8)[0]&0xffffffff,struct.unpack_from('<h',proj,10)[0]&0xffffffff,u16(material,26),u16(material,10),affine);base=(C.c_uint32*2)(*[x&0xffffffff for x in bases]);count=u16(desc,2);ordinal=0;mapping=[]
 for i in range(count):
  j=(i+1)%count;a=vertices[i*68:(i+1)*68];b=vertices[j*68:(j+1)*68];edge=C.create_string_buffer(blocks[6][1][i*52:(i+1)*52]);heights=(C.c_uint32*4)();attrs=(C.c_uint32*4)(u32(a,32),u32(a,36),u32(b,32),u32(b,36));assert prepare(state,a,b,base,read,None,heights,edge);depths=struct.unpack_from('<hh',edge,4);visible=clip(edge,heights,attrs,u32(proj,16),u16(a,46),desc[18],table);assert visible>=0
  if not visible:continue
  out=C.create_string_buffer(before['blocks'][7][1][ordinal*24:ordinal*24+48]);added=C.c_uint();assert emit(edge,heights,attrs,params,table,out,48,C.byref(added));expected=after['blocks'][7][1][ordinal*24:(ordinal+added.value)*24];assert out.raw[:added.value*24]==expected
  flags=u16(edge.raw,48)
  for k in range(added.value):
   endpoint=2-added.value+k;generated=bool(flags&(8 if endpoint==0 else 16));mapping.append(dict(emitted_ordinal=ordinal+k,source_edge=i,endpoint=endpoint,source_vertex=None if generated else (i if endpoint==0 else j),near_generated=generated,source_depths=list(depths),six_words=list(struct.unpack_from('<6i',expected,k*24))))
  ordinal+=added.value
 assert ordinal==u16(after['blocks'][1][1],242)
 checks.append(dict(source=source,draw_event=road['event'],emitted_count=ordinal,mapping=mapping))
report=dict(result='PASS',checks=checks,trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),scope='Every emitted six-word vertex reconstructed by chronological source edge, exact against original post-emission trace. Screen values are diagnostic oracle only, never renderer input.');(p/'stable-road-emission-source-map.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
