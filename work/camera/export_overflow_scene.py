"""Export complete sampled queue geometry/material inputs from one owned scene.
Road extraction is diagnostic: it does not establish sampled road eligibility.
"""
from pathlib import Path
import ctypes as C,struct,json,hashlib,collections

def export(d,identity,pose,batch,old_packet,new_packet,trace,invocations,dest):
 dest=Path(dest);dest.mkdir(exist_ok=True)
 def owned(a,n):
  b=C.create_string_buffer(n);assert d.nf_live_completed_snapshot_read(*identity,a,b,n);return b.raw
 args=(C.c_uint32*6)();assert d.nf_live_completed_surface_arguments(*identity,0,args);state=args[0]
 result=C.create_string_buffer(4868);assert d.nf_live_completed_visibility_at(*identity,pose,result)
 count=struct.unpack_from('<H',result.raw,238)[0];assert count==22 and struct.unpack_from('<I',batch.raw)[0]==count
 (dest/'old.bin').write_bytes(old_packet);(dest/'new.bin').write_bytes(new_packet)
 (dest/'pose.bin').write_bytes(pose.raw);(dest/'visibility.bin').write_bytes(result.raw);(dest/'queue-plans.bin').write_bytes(batch.raw)
 model_inputs=d.nf_live_completed_model_inputs;model_inputs.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p]
 inputs=C.create_string_buffer(b'X'*560,560);assert model_inputs(*identity,inputs)
 (dest/'model-inputs.bin').write_bytes(inputs.raw)
 saved=inputs.raw;assert not model_inputs(identity[0],identity[1],identity[2],identity[3]+1,inputs) and inputs.raw==saved
 retained=collections.Counter((c[2],int(bool(w[1]))) for c,w in zip(trace['commands'],trace['wall_passes']) if c[0]==2 and not c[5])
 sections={tag:old_packet[offset:offset+size] for tag,offset,size in (struct.unpack_from('<3I',old_packet,32+i*12) for i in range(5))}
 old_assets={};cursor=8
 for index in range(struct.unpack_from('<I',sections[2],4)[0]):
  v,w,h=struct.unpack_from('<3I',sections[2],cursor);size=12+v*40+w*h*4
  ident=struct.unpack_from('<5I',sections[5],8+index*20)
  if ident[0]==2 and ident[4]==0:
   if ident[2] in old_assets:assert old_assets[ident[2]]==sections[2][cursor:cursor+size]
   old_assets[ident[2]]=sections[2][cursor:cursor+size]
  cursor+=size
 regions=[];occurrences=[];assets={};road_assets={};missing={}
 Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
 view_address=struct.unpack_from('<I',result.raw,84)[0]
 @Read
 def sampled_read(ctx,a,out,size):
  buffer=C.create_string_buffer(size)
  if not d.nf_live_completed_snapshot_read(*identity,a,buffer,size):return 0
  raw=bytearray(buffer.raw);lo=max(a,view_address);hi=min(a+size,view_address+48)
  if lo<hi:raw[lo-a:hi-a]=pose.raw[56+lo-view_address:56+hi-view_address]
  C.memmove(out,bytes(raw),size);return 1
 child_record=d.nfs_visibility_static_child_record;child_record.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,Read,C.c_void_p,C.c_void_p,C.c_void_p]
 reconstruct=d.nfs_visibility_region_reconstruct;reconstruct.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
 reciprocal=C.create_string_buffer(owned(0x08627700,65536)+owned(0x08637700,65536));static_children=[];unsupported_links=[]


 for qi in range(count):
  off=4+qi*2068;record=list(struct.unpack_from('<8H',batch.raw,off+4));n=struct.unpack_from('<I',batch.raw,off)[0]
  assert batch.raw[off+4:off+20]==result.raw[256+qi*16:272+qi*16]
  if record[5]&8:assert n==0;regions.append(dict(index=qi,record=record,merged=True));continue
  geometry=C.create_string_buffer(3472);assert d.nf_live_completed_region_at(*identity,pose,qi,geometry)
  (dest/f'region-{qi}.bin').write_bytes(geometry.raw)
  child=C.create_string_buffer(b'X'*16,16)
  child_status=child_record(geometry,C.create_string_buffer(struct.pack('<8H',*record)),0,sampled_read,None,reciprocal,child)
  if child_status==1:
   child_state=C.create_string_buffer(geometry.raw[:256],256);edges=C.create_string_buffer(1664);stream=C.create_string_buffer(1536)
   reconstructed=reconstruct(child_state,child,sampled_read,None,reciprocal,edges,1664,stream,1536)
   assert reconstructed in (0,1)
   if reconstructed==1:(dest/f'static-child-{qi}.bin').write_bytes(child_state.raw+child.raw+edges.raw+stream.raw)
   child_descriptor=struct.unpack_from('<I',geometry.raw,20)[0]+struct.unpack_from('<H',child.raw)[0]*48
   child_road=C.c_void_p();child_size=C.c_size_t();child_ok=bool(d.nf_live_completed_road_candidate(*identity,state,child_descriptor,C.byref(child_road),C.byref(child_size)))
   if child_ok:
    try:child_raw=C.string_at(child_road,child_size.value)
    finally:d.nf_surface_free(child_road)
    (dest/f'road-{child_descriptor}.bin').write_bytes(child_raw);road_assets[child_descriptor]=dict(bytes=len(child_raw),sha256=hashlib.sha256(child_raw).hexdigest(),origin='static child')
   static_children.append(dict(parent_queue_index=qi,record=list(struct.unpack('<8H',child.raw)),geometry_status=reconstructed,road_descriptor=child_descriptor,road_extracted=child_ok))
  elif child_status==-1:unsupported_links.append(qi);assert child.raw==b'X'*16

  descriptor=struct.unpack_from('<I',geometry.raw,20)[0]+record[0]*48
  desc=owned(descriptor,48);first,vertices=struct.unpack_from('<HH',desc);base=struct.unpack_from('<I',geometry.raw,16)[0]
  for di in range(n):
   draw=list(struct.unpack_from('<8I',batch.raw,off+20+di*32));source,phase=draw[:2]
   assert source>=base+first*68 and source<base+(first+vertices)*68 and (source-base-first*68)%68==0
   ident=[2,state,source,struct.unpack_from('<H',owned(source,68),44)[0],0]
   if source not in assets and source not in missing:
    origin='captured packet' if source in old_assets else 'owned candidate'
    if source in old_assets:raw=old_assets[source]
    else:
     asset=C.c_void_p();size=C.c_size_t();ok=d.nf_live_completed_wall_candidate(*identity,state,source,C.byref(asset),C.byref(size))
     if ok:
      try:raw=C.string_at(asset,size.value)
      finally:d.nf_surface_free(asset)
     else:missing[source]=dict(flags=struct.unpack_from('<H',owned(source,68),46)[0],reason='Restricted candidate extraction rejected');raw=None
    if raw is not None:
     v,w,h=struct.unpack_from('<3I',raw)
     assert v==4 and w>0 and h>0 and len(raw)==12+v*40+w*h*4
     (dest/f'wall-{source}.bin').write_bytes(raw);assets[source]=dict(identity=ident,origin=origin,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
   occurrences.append(dict(queue_index=qi,draw_index=di,source=source,phase=phase,bounds=record[1:5]))
  road=C.c_void_p();road_size=C.c_size_t();road_ok=bool(d.nf_live_completed_road_candidate(*identity,state,descriptor,C.byref(road),C.byref(road_size)))
  if road_ok:
   try:raw=C.string_at(road,road_size.value)
   finally:d.nf_surface_free(road)
   if descriptor in road_assets:assert road_assets[descriptor]['sha256']==hashlib.sha256(raw).hexdigest()
   else:(dest/f'road-{descriptor}.bin').write_bytes(raw);road_assets[descriptor]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
  regions.append(dict(index=qi,record=record,descriptor=descriptor,wall_count=n,road_extracted=road_ok,primary_material=struct.unpack_from('<H',desc,8)[0],alternate_material=struct.unpack_from('<H',desc,4)[0]))
 # Quarter fixture was produced earlier in this same retained-scene pass.
 # Reevaluate its queue against owned storage; never read current emulator RAM.
 adjacent_assets={};adjacent_missing={}
 quarter=dest.parent/'visibility-overflow-171-wide'
 quarter_meta=json.loads((quarter/'sample-0.25.json').read_text())
 assert quarter_meta['identity']==list(identity) and quarter_meta['available']
 quarter_pose=C.create_string_buffer((quarter/'pose-0.25.bin').read_bytes(),104)
 quarter_batch=C.create_string_buffer(66180)
 assert d.nf_live_completed_queue_plans(*identity,quarter_pose,quarter_batch)
 for qi in range(struct.unpack_from('<I',quarter_batch.raw)[0]):
  off=4+qi*2068;n=struct.unpack_from('<I',quarter_batch.raw,off)[0]
  geometry=C.create_string_buffer(3472);assert d.nf_live_completed_region_at(*identity,quarter_pose,qi,geometry)
  region=struct.unpack_from('<H',quarter_batch.raw,off+4)[0]
  desc=owned(struct.unpack_from('<I',geometry.raw,20)[0]+region*48,48)
  first,vertices=struct.unpack_from('<HH',desc);base=struct.unpack_from('<I',geometry.raw,16)[0]
  for di in range(n):
   source=struct.unpack_from('<I',quarter_batch.raw,off+20+di*32)[0]
   assert base+first*68<=source<base+(first+vertices)*68 and (source-base-first*68)%68==0
   if source in assets or source in adjacent_assets or source in adjacent_missing:continue
   asset=C.c_void_p();size=C.c_size_t()
   if not d.nf_live_completed_wall_candidate(*identity,state,source,C.byref(asset),C.byref(size)):
    adjacent_missing[source]=dict(alpha=.25,queue_index=qi,reason='Restricted owned candidate extraction rejected');continue
   try:raw=C.string_at(asset,size.value)
   finally:d.nf_surface_free(asset)
   v,w,h=struct.unpack_from('<3I',raw);assert v==4 and w>0 and h>0 and len(raw)==12+v*40+w*h*4
   ident=[2,state,source,struct.unpack_from('<H',owned(source,68),44)[0],0]
   (dest/f'wall-{source}.bin').write_bytes(raw)
   adjacent_assets[source]=dict(identity=ident,origin='owned quarter queue candidate',alpha=.25,region=region,queue_index=qi,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 sampled=collections.Counter((o['source'],o['phase']) for o in occurrences)
 added=sampled-retained;removed=retained-sampled
 manifest=dict(identity=list(identity),alpha=.5,state=state,regions=regions,occurrences=occurrences,assets=assets,road_assets=road_assets,missing_wall_assets=missing,static_children=static_children,unsupported_links=unsupported_links,added=[dict(source=k[0],phase=k[1],count=v) for k,v in added.items()],removed=[dict(source=k[0],phase=k[1],count=v) for k,v in removed.items()],captured=trace,scope='Queue wall asset availability and complete region geometry; object/model eligibility, sampled road eligibility and composed command order remain unverified.')
 manifest['adjacent_assets']=adjacent_assets;manifest['adjacent_missing']=adjacent_missing
 # Native structural projection is bound to these exact captured commands.
 binder=C.CDLL(str((dest.parent/'sampled-root-binding-test.dll').resolve()))
 assert binder.nf_sampled_root_binding_capacity()==32
 bind=binder.nf_sampled_root_binding;bind.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
 def pack(rows,width):return (C.c_uint32*(len(rows)*width))(*(v for row in rows for v in (row if row is not None else [0]*width)))
 output=(C.c_uint32*770)()
 assert bind(result.raw[256:256+count*16],count,pack(invocations,9),len(invocations),pack(trace['commands'],6),len(trace['commands']),pack(trace['origins'],12),pack(trace['wall_passes'],3),output)
 binding_calls=[list(output[2+i*8:10+i*8]) for i in range(output[0])]
 manifest['root_bindings']=dict(calls=binding_calls,removed=list(output[514:514+output[1]]),status_counts=dict(collections.Counter(call[-1] for call in binding_calls)),scope='Unique direct roots may supply captured segment templates; ambiguous and complex calls remain unresolved. No draw eligibility inferred.')
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
 return dict(result='PASS',static_children=len(static_children),unsupported_links=len(unsupported_links),root_binding_status_counts=manifest['root_bindings']['status_counts'],queue_records=count,wall_occurrences=len(occurrences),unique_wall_assets=len(assets),road_assets=len(road_assets),missing_wall_assets=len(missing),added_wall_occurrences=sum(added.values()),removed_wall_occurrences=sum(removed.values()),scope=manifest['scope'])
