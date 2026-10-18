import ctypes as C,struct,json
from wall_native_prepared import prepared_edge_owned
from pathlib import Path
p=Path('work/camera');lib=C.CDLL(str((p/'native_model.dll').resolve()));fn=lib.nfs_model_source_rows;fn.argtypes=[C.c_void_p]*4+[C.c_uint,C.c_void_p]
table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());raw=(p/'motion-live-native-model-plans.bin').read_bytes();offset=0;plans=[]
while offset<len(raw):
 magic,refresh,context,ok,count=struct.unpack_from('<5I',raw,offset);offset+=20;assert magic==0x314d504e and ok
 plans.append(raw[offset:offset+count*28]);offset+=count*28
prepared_lib=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));prepared_fn=prepared_lib.nf_wall_owned_prepared;prepared_fn.argtypes=[C.c_void_p]*5+[C.c_uint,C.c_void_p,C.c_void_p]
quad_fn=prepared_lib.nf_wall_owned_quad;quad_fn.argtypes=[C.c_void_p]*4
wall_lib=C.CDLL(str((p/'native_wall.dll').resolve()))
wall_fn=wall_lib.nfs_wall_source_columns
wall_fn.argtypes=[C.c_void_p]*7+[C.c_uint,C.c_void_p]
wall_raw=(p/'motion-live-native-model-plans.bin.wall.bin').read_bytes();wall_offset=0;wall_plans={};wall_order=[]
while wall_offset<len(wall_raw):
 magic,refresh,context,ok,count=struct.unpack_from('<5I',wall_raw,wall_offset);wall_offset+=20
 assert magic==0x3157504e and ok
 payload=wall_raw[wall_offset:wall_offset+count*80];wall_plans.setdefault((refresh,context),[]).append(payload);wall_order.append((refresh,context,payload));wall_offset+=count*80
checks=[];totals={1:0,2:0,3:0};wall_columns=0;wall_used={};packet_walls=[]
for index,refresh in enumerate([8758,8762,8766,8769,8773,8776,8780]):
 raw=(p/f'motion-actual-scanline-assets/{refresh}-model-sources.bin').read_bytes();offset=0;records=[]
 while offset<len(raw):
  magic,kind,context,count=struct.unpack_from('<4I',raw,offset);offset+=16;assert magic==0x3147534e and kind in (1,2,3) and count==12
  blocks=[]
  for i in range(count):
   size=struct.unpack_from('<I',raw,offset)[0];offset+=4;blocks.append(raw[offset:offset+size]);offset+=size
  totals[kind]+=1
  if kind==1:
   vertices,affine,orientation,first,base,framebuffer,u,v=struct.unpack('<8I',blocks[6]);assert 3<=vertices<=32
   assert len(blocks[0])==vertices*68 and len(blocks[1])==vertices*32 and len(blocks[4])==48 and len(blocks[8])==512
   assert len(blocks[7])>0 and len(blocks[5])==8
   continue
  if kind==2:
   assert [len(b) for b in blocks]==[136,64,8,48,48,8,64,32,65536,512,52,260]
   bounds=(C.c_uint*4)(*struct.unpack('<4H',blocks[5]));out=(C.c_uint32*(120*20))();n=C.c_uint()
   quad=(C.c_double*12)();assert quad_fn(blocks[0],blocks[1],blocks[3],quad)
   assert all(__import__('math').isfinite(value) for value in quad)
   edge_out=C.create_string_buffer(52);flags=struct.unpack_from('<I',blocks[11],256)[0]
   assert prepared_fn(blocks[0],blocks[1],blocks[2],blocks[3],blocks[4],flags,table,edge_out)
   edge=edge_out.raw
   assert edge==prepared_edge_owned(blocks,table)
   rejected=C.create_string_buffer(b'X'*52,52);assert not prepared_fn(blocks[0],blocks[1],blocks[2],blocks[3],blocks[4],flags|128,table,rejected);assert rejected.raw==b'X'*52
   assert edge==blocks[10], (refresh,context,[(i,a,b) for i,(a,b) in enumerate(zip(edge,blocks[10])) if a!=b])
   assert wall_fn(edge,table,bounds,blocks[4],blocks[6],blocks[7],out,120,C.byref(n))
   packet_walls.append((context,bytes(out)[:n.value*80]))
   wall_columns+=n.value
   continue
  buffers=[C.create_string_buffer(b) for b in blocks[:10]];ptrs=(C.c_void_p*10)(*[C.cast(b,C.c_void_p).value for b in buffers]);sizes=(C.c_uint*10)(*[len(b) for b in blocks[:10]]);out=(C.c_uint32*(65536*7))();n=C.c_uint()
  assert fn(ptrs,sizes,table,out,65536,C.byref(n));assert bytes(out)[:n.value*28]==plans[index+1]
  shift,height=struct.unpack_from('<2H',blocks[0],56);assert len(blocks[10])==(1<<shift)*height and len(blocks[11])==512
  records.append(n.value)
 assert len(records)==1
 checks.append(dict(refresh=refresh,bytes=len(raw),native_rows=records[0],exact=True))
matches=[start for start in range(len(wall_order)-len(packet_walls)+1) if [(context,payload) for refresh,context,payload in wall_order[start:start+len(packet_walls)]]==packet_walls]
assert len(matches)==1, matches
r=dict(result='PASS_LIVE_OWNED_MODEL_GEOMETRY_SOURCES',checks=checks,source_records_by_kind=totals,exact_wall_columns=wall_columns,wall_sequence_start=matches[0],scope='Coherent owned local vertices/topology/UV/matrix/material/texture/palette reproduce live native model row plans. Owned wall endpoints/offsets/flags/matrix/UV/material reconstruct exact prepared edges and live wall commands; captured edges used only as comparison. Road raw world/material records structurally validated. No GPU4K rendering or motion verification.')
(p/'live-geometry-source-tests.json').write_text(json.dumps(r,indent=2));print(r)

