from pathlib import Path
import ctypes as C,json,struct,hashlib
from scene_batches import records
p=Path('work/camera');trace=p/'stable-original-source-8775-8779.bin';events=list(records(trace));roads=json.loads((p/'stable-original-road-source.json').read_text())['roads'];rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nfs_visibility_region_geometry;fn.argtypes=[C.c_void_p]*3+[C.c_uint,C.c_uint,Read,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t];checks=[]
for road in roads:
 source=road['source'];before=max((e for e in events if e['id']<road['event'] and e['pc']==0x03001800 and e['blocks'][4][0]==source),key=lambda e:e['id']);after=min((e for e in events if e['id']>before['id'] and e['pc']==0x03002964 and e['blocks'][4][0]==source),key=lambda e:e['id']);assert after['id']<road['event'];blocks=before['blocks']
 @Read
 def read(user,address,target,size):
  if 0x08000000<=address and address+size<=0x08000000+len(rom):C.memmove(target,rom[address-0x08000000:address-0x08000000+size],size);return 1
  for base,data in list(blocks.values())+[(v['address'],bytes.fromhex(v['hex'])) for v in road['blocks'].values()]:
   if data and base<=address and address+size<=base+len(data):C.memmove(target,data[address-base:address-base+size],size);return 1
  print("missing",hex(address),size);return 0
 state=C.create_string_buffer(blocks[1][1]);scratch=C.create_string_buffer(blocks[6][1]);stream=C.create_string_buffer(blocks[7][1]);n=struct.unpack_from('<H',blocks[4][1],2)[0];affine=struct.unpack_from('<I',bytes.fromhex(road['blocks']['69']['hex']))[0]&1
 assert fn(state,blocks[4][1],blocks[5][1],n,affine,read,None,table,scratch,len(blocks[6][1]),stream,len(blocks[7][1]))
 emitted=struct.unpack_from('<H',state.raw,242)[0];expected=after['blocks'][7][1];assert stream.raw[:emitted*24]==expected[:emitted*24],(road['event'],'UVstream');assert scratch.raw[:n*52]==after['blocks'][6][1],(road['event'],'scratch')
 checks.append(dict(source=source,before_event=before['id'],after_event=after['id'],draw_event=road['event'],affine=affine,emitted_vertices=emitted,complete_six_word_stream_exact=True,scratch_exact=True))
report=dict(result='PASS',checks=checks,trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),scope='Exact original source pipeline before/after event joins by descriptor identity and chronology. Recovered native region_geometry reproduces original near/projectedUV six-word stream and wall scratch. Oracle only, not native continuousGPU agreement or polygon matching.')
(p/'stable-original-uv-emission-parity.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
