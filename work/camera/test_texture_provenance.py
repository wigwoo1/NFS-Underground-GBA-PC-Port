"""Owned texture provenance, scene boundaries and atomic failure checks."""
from pathlib import Path
import ctypes as C,struct,hashlib,json,collections,time,os
from clip_metadata import build as build_clips
from region_block import region_block
root=Path('work').resolve();wide=os.getenv('NF_VISIBILITY_WIDE')=='1';d=C.CDLL(str(root/('camera/visibility-probe-wide.dll' if wide else 'camera/visibility-probe.dll')))
queue_capacity=d.nfs_visibility_queue_capacity() if wide else 20
assert queue_capacity==(32 if wide else 20)
result_bytes=256+queue_capacity*16+4096+4;batch_bytes=4+queue_capacity*2068
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
sig=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint,C.c_void_p]
d.nf_live_completed_texture_provenance.argtypes=sig
d.nf_live_completed_surface_identity.argtypes=sig
d.nf_live_completed_surface_bounds.argtypes=sig
d.nf_live_completed_surface_origin.argtypes=sig
d.nf_live_completed_wall_pass.argtypes=sig
d.nf_live_completed_object_region.argtypes=sig
d.nf_live_completed_object_invocations.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_uint,C.c_void_p]
d.nf_live_completed_dispatch.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_uint,C.c_void_p]
d.nf_live_completed_ordered_dispatch.argtypes=d.nf_live_completed_dispatch.argtypes
d.nf_live_completed_reconstructed_order.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p]
d.nf_live_completed_sampled_bounds.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
d.nf_live_completed_ordered_packet.argtypes=[C.c_uint64,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p]
d.nf_scene_packet_free.argtypes=[C.c_void_p]
class Timeline(C.Structure):
 _fields_=[('epoch',C.c_uint64),('older',C.c_uint64),('newer',C.c_uint64),('alpha',C.c_double),('target',C.c_double)]
class Pair(C.Structure):
 _fields_=[('time',Timeline),('older',C.c_void_p),('older_size',C.c_size_t),('newer',C.c_void_p),('newer_size',C.c_size_t)]
d.nf_snapshot_create.argtypes=[C.c_size_t];d.nf_snapshot_create.restype=C.c_void_p
d.nf_snapshot_acquire.argtypes=[C.c_void_p,C.c_double,C.c_double,C.c_void_p]
d.nf_snapshot_release.argtypes=[C.c_void_p];d.nf_snapshot_destroy.argtypes=[C.c_void_p]
d.nf_live_completed_publish_ordered.argtypes=[C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t]
ordered_store=d.nf_snapshot_create(64*1024*1024);assert ordered_store
d.nf_live_completed_wall_animation.argtypes=sig
d.nf_live_completed_snapshot_read.argtypes=sig+[C.c_size_t]
candidate_sources=[];candidate_palettes=[];candidate_extractions=[];earlier_identity=None;scene_palette_bytes={};kept_candidate=None;enumeration=[];candidate_gates=[]
d.nf_live_palette_draw.argtypes=sig+[C.c_void_p]
d.nf_live_completed_surface_arguments.argtypes=sig
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
d.nfs_visibility_wall_draw_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint32,Read,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
d.nf_candidate_palette.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_void_p]
d.nf_live_visibility_evaluate.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p]
d.nf_live_completed_queue_plans.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_void_p]
d.nf_live_completed_wall_plan.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_uint,C.c_void_p]
d.nf_live_completed_object_wall_plan.argtypes=d.nf_live_completed_wall_plan.argtypes
d.nf_live_completed_region_at.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_uint,C.c_void_p]
d.nf_live_completed_object_invocation_slot.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_uint,C.c_void_p]
d.nf_live_completed_object_candidate.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
d.nf_live_completed_object_invocation_palette.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_uint,C.c_void_p]
d.nf_live_completed_region_invocations.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_uint,C.c_void_p]
region_invocation_samples=[]
d.nf_wall_insertions.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
d.nf_root_region_anchors.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
d.nf_root_region_schedule.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
d.nf_live_completed_road_material_plan.argtypes=[C.c_uint64]+[C.c_uint32]*5+[C.c_void_p]
d.nf_live_completed_road_candidate.argtypes=[C.c_uint64]+[C.c_uint32]*5+[C.c_void_p,C.c_void_p]
invocation_frames=[];sampled_queue_transitions=[];invocation_transitions=[];invocation_palette_comparisons=[]
d.nf_live_completed_object_invocation_plan.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_uint,C.c_void_p]
d.nf_visibility_pose_sample.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p]
d.nf_live_completed_visibility_pose.argtypes=d.nf_live_visibility_evaluate.argtypes
d.nf_live_completed_visibility_at.argtypes=d.nf_live_visibility_evaluate.argtypes+[C.c_void_p]
pose_samples=[];pose_relations=[];portal_samples=[];draw_bounds=[];missing_wall_trace=[];object_records=[];kept_plans=[];dispatch_samples=[]
d.nfs_visibility_region_reconstruct.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
d.nf_extract_wall_candidate.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
d.nf_wall_owner.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32)]
d.nf_extract_wall.argtypes=[Read,C.c_void_p]+[C.c_uint32]*6+[C.c_void_p]*4
d.nf_surface_free.argtypes=[C.c_void_p]
d.nf_live_completed_wall_candidate.argtypes=[C.c_uint64]+[C.c_uint32]*5+[C.c_void_p,C.c_void_p]
d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
previous={};counts=collections.Counter();updates=[];errors=[];animation_samples=[]
@Sink
def receive(ctx,epoch,ptr,size):
 global previous,last,earlier_identity,kept_candidate
 try:
  b=C.string_at(ptr,size);h=struct.unpack_from('<8I',b);sections={t:b[o:o+n] for t,o,n in [struct.unpack_from('<3I',b,32+i*12) for i in range(5)]}
  world=sections[2];n=struct.unpack_from('<I',world,4)[0];pos=8;textures=[]
  for i in range(n):
   v,w,ht=struct.unpack_from('<3I',world,pos);start=pos+12+v*40;end=start+w*ht*4
   textures.append(hashlib.sha256(world[start:end]).hexdigest());pos=end
  order=struct.unpack_from('<'+'I'*struct.unpack_from('<I',sections[3],4)[0],sections[3],8)
  retained=C.create_string_buffer(104)
  assert d.nf_live_completed_visibility_pose(epoch,h[4],h[5],h[6],retained)
  inputs=struct.unpack('<26i',retained.raw);base=inputs[:2];query=inputs[2:14];view=inputs[14:]
  camera=struct.unpack_from('<7d',sections[1],48);x,y,z,w=camera[3:]
  rotation=(1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y))
  pose_relations.append(dict(serial=h[4],query_transpose=all(query[i*3+j]==view[j*3+i] for i in range(3) for j in range(3)),query_zero_translation=query[9:]==(0,0,0),base_translation=(view[9]==-(base[0]>>8) and view[11]==-(base[1]>>8)),camera_translation=list(camera[:3])==[-v for v in view[9:]],rotation_error=max(abs(rotation[i*3+j]-view[j*3+i]/16384) for i in range(3) for j in range(3))))
  dispatch=(C.c_uint32*(257*6))();dispatch_count=C.c_uint(999)
  assert d.nf_live_completed_dispatch(epoch,h[4],h[5],h[6],dispatch,257,C.byref(dispatch_count))
  commands=[list(dispatch[i*6:i*6+6]) for i in range(dispatch_count.value)]
  assert len(commands)==len(order)
  model_position=order.index(0xffffffff)
  for command,index in zip(commands,order):
   if index==0xffffffff:assert command[:2]==[3,0xffffffff]
   else:
    identity=struct.unpack_from('<5I',sections[5],8+index*20);assert command[0]==identity[0] and command[2]==identity[2]
  saved=bytes(dispatch);saved_count=dispatch_count.value
  assert not d.nf_live_completed_dispatch(epoch,h[4],h[5],h[6],dispatch,len(order)-1,C.byref(dispatch_count)) and bytes(dispatch)==saved and dispatch_count.value==saved_count
  objects=[dict(command_index=i,draw_ordinal=c[1],source=c[2],object=c[3],descriptor=c[4],before_model=i<model_position) for i,c in enumerate(commands) if c[5]]
  region_rows=(C.c_uint32*(256*9))();region_count=C.c_uint()
  assert d.nf_live_completed_region_invocations(epoch,h[4],h[5],h[6],region_rows,256,C.byref(region_count)),('region capture',h[4])
  region_records=[list(region_rows[i*9:i*9+9]) for i in range(region_count.value)]
  assert all(row[6]<=row[7]<=len(commands) for row in region_records)
  counts['region_invocations']+=region_count.value
  counts['region_invocations_empty']+=sum(row[6]==row[7] for row in region_records)
  region_invocation_samples.append(dict(scene=h[4],records=region_records))
  invocations=(C.c_ubyte*(448*64))();inv_count=C.c_uint(999)
  assert d.nf_live_completed_object_invocations(epoch,h[4],h[5],h[6],invocations,64,C.byref(inv_count))
  counts['owned_object_invocations']+=inv_count.value
  empty_invocations=[]
  for invocation in range(inv_count.value):
   slot=C.c_uint(0xdeadbeef)
   assert d.nf_live_completed_object_invocation_slot(epoch,h[4],h[5],h[6],invocation,C.byref(slot)) and slot.value<=len(commands)
   address=struct.unpack_from('<I',bytes(invocations),invocation*448)[0]
   matching=[obj['command_index'] for obj in objects if obj['object']==address]
   if matching:assert slot.value==min(matching);counts['invocation_slot_emitted_exact']+=1
   invocation_palette=C.create_string_buffer(512)
   assert d.nf_live_completed_object_invocation_palette(epoch,h[4],h[5],h[6],invocation,invocation_palette)
   if matching:
    key=(C.c_uint32*3)();draw_palette=C.create_string_buffer(512)
    ordinal=commands[min(matching)][1]
    assert d.nf_live_palette_draw(epoch,h[4],h[5],h[6],ordinal,key,draw_palette)
    counts['invocation_palette_draw_exact' if invocation_palette.raw==draw_palette.raw else 'invocation_palette_draw_different']+=1
    provenance=(C.c_uint64*5)()
    assert d.nf_live_completed_texture_provenance(epoch,h[4],h[5],h[6],ordinal,provenance)
    indices=C.create_string_buffer(provenance[1]*provenance[2])
    assert d.nf_live_completed_snapshot_read(epoch,h[4],h[5],h[6],provenance[0],indices,len(indices))
    index_hash=14695981039346656037
    for value in indices.raw:index_hash=((index_hash^value)*1099511628211)&0xffffffffffffffff
    assert index_hash==provenance[3]
    used=sorted(set(indices.raw))
    changed=[i for i in used if invocation_palette.raw[i*2:i*2+2]!=draw_palette.raw[i*2:i*2+2]]
    counts['invocation_used_palette_different' if changed else 'invocation_used_palette_exact']+=1
    counts['invocation_visible_palette_different' if any(changed_index!=0 for changed_index in changed) else 'invocation_visible_palette_exact']+=1
    if changed:invocation_palette_comparisons.append(dict(scene=h[4],invocation=invocation,ordinal=ordinal,source=commands[min(matching)][2],texture=provenance[0],used=len(used),changed_indices=changed))
   before_palette=invocation_palette.raw
   assert not d.nf_live_completed_object_invocation_palette(epoch,h[4],h[5],h[6],inv_count.value,invocation_palette) and invocation_palette.raw==before_palette
   previous_slot=slot.value
   assert not d.nf_live_completed_object_invocation_slot(epoch,h[4],h[5],h[6],inv_count.value,C.byref(slot)) and slot.value==previous_slot
   plan=C.create_string_buffer(2068)
   assert d.nf_live_completed_object_invocation_plan(epoch,h[4],h[5],h[6],retained,invocation,plan)
   planned_sources=[struct.unpack_from('<I',plan.raw,20+j*32)[0] for j in range(struct.unpack_from('<I',plan.raw)[0])]
   captured_sources=[commands[j][2] for j in matching]
   assert collections.Counter(planned_sources)==collections.Counter(captured_sources),('invocation source coverage',h[4],invocation,planned_sources,captured_sources)
   counts['invocation_plan_sources_exact']+=1
   counts['invocation_plan_retained']+=1
   if struct.unpack_from('<I',plan.raw)[0]==0:counts['invocation_plan_retained_empty']+=1;empty_invocations.append(invocation)
  sentinel=C.create_string_buffer(b'X'*2068,2068);before=sentinel.raw
  assert not d.nf_live_completed_object_invocation_plan(epoch,h[4],h[5],h[6],retained,inv_count.value,sentinel) and sentinel.raw==before
  if invocation_frames:
   old_id,old_pose,old_count,old_empty,old_packet,old_invocations=invocation_frames[-1]
   old_trace=next(trace for trace in dispatch_samples if trace['serial']==old_id[1])
   old_queue=collections.Counter((c[2],int(bool(wp[1]))) for c,wp in zip(old_trace['commands'],old_trace['wall_passes']) if c[0]==2 and not c[5])
   old_regions={o[2]&65535 for c,o in zip(old_trace['commands'],old_trace['origins']) if c[0]==2 and not c[5]}
   for fraction in (.25,.5,.75):
    probe_pose=C.create_string_buffer(104);probe_batch=C.create_string_buffer(batch_bytes)
    assert d.nf_visibility_pose_sample(C.create_string_buffer(old_pose),retained,fraction,probe_pose)
    if old_id[1]==171:
     # Private, scene-owned fixture: no current emulator RAM or future assets.
     fixture=root/('camera/visibility-overflow-171-wide' if wide else 'camera/visibility-overflow-171');fixture.mkdir(exist_ok=True)
     for address,amount,name in ((0x02000000,0x40000,'ewram.bin'),(0x03000000,0x8000,'iwram.bin')):
      memory=C.create_string_buffer(amount)
      for offset in range(0,amount,65536):
       assert d.nf_live_completed_snapshot_read(*old_id,address+offset,C.byref(memory,offset),min(65536,amount-offset))
      target=fixture/name
      if target.exists():assert target.read_bytes()==memory.raw
      else:target.write_bytes(memory.raw)
     (fixture/('pose-'+str(fraction)+'.bin')).write_bytes(probe_pose.raw)
     control=C.create_string_buffer(b'R'*result_bytes,result_bytes);saved=control.raw
     available=bool(d.nf_live_completed_visibility_at(*old_id,probe_pose,control))
     stage=d.nfs_visibility_failure_stage()
     if available:(fixture/('result-'+str(fraction)+'.bin')).write_bytes(control.raw)
     else:assert control.raw==saved
     fixture_args=(C.c_uint32*6)()
     assert d.nf_live_completed_surface_arguments(*old_id,0,fixture_args)
     state_address=fixture_args[0]
     assert 0x02000000<=state_address<0x02040000 or 0x03000000<=state_address<0x03008000
     metadata=dict(identity=list(old_id),alpha=fraction,state_address=state_address,available=available,stage=stage,
       ram_sha256={name:hashlib.sha256((fixture/name).read_bytes()).hexdigest() for name in ('ewram.bin','iwram.bin')},
       scope='Owned earlier scene RAM and coherent sampled pose; private diagnostic inputs, not a save or full render scene.')
     (fixture/('sample-'+str(fraction)+'.json')).write_text(json.dumps(metadata,indent=2))
    if not d.nf_live_completed_queue_plans(*old_id,probe_pose,probe_batch):
     counts['sampled_queue_transition_unavailable']+=1
     evaluated=C.create_string_buffer(result_bytes);evaluation_ok=d.nf_live_completed_visibility_at(*old_id,probe_pose,evaluated);failures=[]
     if evaluation_ok:
      for qi in range(struct.unpack_from('<H',evaluated.raw,238)[0]):
       region=C.create_string_buffer(3472);wall=C.create_string_buffer(2068)
       geometry_ok=d.nf_live_completed_region_at(*old_id,probe_pose,qi,region)
       wall_ok=d.nf_live_completed_wall_plan(*old_id,probe_pose,qi,wall)
       if not geometry_ok or not wall_ok:failures.append(dict(queue_index=qi,record=list(struct.unpack_from('<8H',evaluated.raw,256+qi*16)),geometry_ok=bool(geometry_ok),wall_ok=bool(wall_ok)))
     sampled_queue_transitions.append(dict(scene=old_id[1],alpha=fraction,unavailable=True,evaluation_ok=bool(evaluation_ok),native_stage=d.nfs_visibility_failure_stage(),failures=failures));continue
    if wide and old_id[1]==171 and fraction==.5:
     from export_overflow_scene import export
     fixture_rows=next(x['records'] for x in region_invocation_samples if x['scene']==old_id[1])
     fixture_report=export(d,old_id,probe_pose,probe_batch,old_packet,b,old_trace,fixture_rows,root/'camera/overflow-scene-171')
     (root/'camera/overflow-scene-export-tests.json').write_text(json.dumps(fixture_report,indent=2))
    sampled_queue=collections.Counter();source_regions={}
    for qi in range(struct.unpack_from('<I',probe_batch.raw)[0]):
     off=4+qi*2068;region=struct.unpack_from('<H',probe_batch.raw,off+4)[0]
     for di in range(struct.unpack_from('<I',probe_batch.raw,off)[0]):
      key=struct.unpack_from('<2I',probe_batch.raw,off+20+di*32)
      sampled_queue[key]+=1;source_regions[key]=region
    added=sampled_queue-old_queue;removed=old_queue-sampled_queue
    counts['sampled_queue_transition_probes']+=1
    counts['sampled_queue_added_occurrences']+=sum(added.values());counts['sampled_queue_removed_occurrences']+=sum(removed.values())
    if added or removed:
     sampled_queue_transitions.append(dict(scene=old_id[1],alpha=fraction,added=[dict(source=k[0],pass_id=k[1],count=v,region=source_regions[k],retained_region=source_regions[k] in old_regions) for k,v in added.items()],removed=[dict(source=k[0],pass_id=k[1],count=v) for k,v in removed.items()]))
   sampled=C.create_string_buffer(104)
   assert d.nf_visibility_pose_sample(C.create_string_buffer(old_pose),retained,.5,sampled)
   for invocation in range(old_count):
    plan=C.create_string_buffer(2068)
    assert d.nf_live_completed_object_invocation_plan(*old_id,sampled,invocation,plan)
    if old_id[1] in (143,144):
     sampled_sources=[struct.unpack_from('<I',plan.raw,20+j*32)[0] for j in range(struct.unpack_from('<I',plan.raw)[0])]
     invocation_transitions.append(dict(scene=old_id[1],index=invocation,alpha=.5,sampled_sources=sampled_sources,record=list(struct.unpack_from('<8H',plan.raw,4))))
    counts['invocation_plan_midpoint']+=1
    if invocation in old_empty:
     slot=C.c_uint();assert d.nf_live_completed_object_invocation_slot(*old_id,invocation,C.byref(slot))
     draw_count=struct.unpack_from('<I',plan.raw)[0]
     candidate=C.c_void_p();candidate_size=C.c_size_t()
     extracted=d.nf_live_completed_object_candidate(*old_id,sampled,invocation,C.byref(candidate),C.byref(candidate_size))
     if extracted:
      (root/f'camera/object-candidate-{old_id[1]}.bin').write_bytes(C.string_at(candidate,candidate_size.value));d.nf_surface_free(candidate)
     if extracted:
      stem=root/f'camera/object-replay-{old_id[1]}'
      Path(str(stem)+'-old.bin').write_bytes(old_packet);Path(str(stem)+'-new.bin').write_bytes(b)
      source=struct.unpack_from('<I',plan.raw,20)[0];base=C.c_uint16()
      assert d.nf_live_completed_snapshot_read(*old_id,source+44,C.byref(base),2)
      state=struct.unpack_from('<I',old_invocations,invocation*448+4)[0]
      bounds=(C.c_uint16*(256*4))();extra=C.c_uint()
      assert d.nf_live_completed_sampled_bounds(*old_id,sampled,bounds,256,C.byref(extra))
      batch=C.create_string_buffer(batch_bytes);assert d.nf_live_completed_queue_plans(*old_id,sampled,batch)
      Path(str(stem)+'-sampled-queue.bin').write_bytes(batch.raw)
      captured_batch=C.create_string_buffer(batch_bytes);assert d.nf_live_completed_queue_plans(*old_id,C.create_string_buffer(old_pose),captured_batch)
      Path(str(stem)+'-captured-queue.bin').write_bytes(captured_batch.raw)
      old_trace=next(trace for trace in dispatch_samples if trace['serial']==old_id[1])
      existing={(command[2],int(bool(wp[1]))) for command,wp in zip(old_trace['commands'],old_trace['wall_passes']) if command[0]==2 and not command[5]}
      queue_candidates=[]
      for qi in range(struct.unpack_from('<I',batch.raw)[0]):
       offset=4+qi*2068;record=list(struct.unpack_from('<8H',batch.raw,offset+4))
       for di in range(struct.unpack_from('<I',batch.raw,offset)[0]):
        draw=list(struct.unpack_from('<8I',batch.raw,offset+20+di*32))
        if tuple(draw[:2]) in existing:continue
        asset=C.c_void_p();asset_size=C.c_size_t()
        ok=d.nf_live_completed_wall_candidate(*old_id,state,draw[0],C.byref(asset),C.byref(asset_size))
        if ok:
         (root/f'camera/queue-candidate-{old_id[1]}-{draw[0]}.bin').write_bytes(C.string_at(asset,asset_size.value));d.nf_surface_free(asset)
        candidate_base=C.c_uint16();assert d.nf_live_completed_snapshot_read(*old_id,draw[0]+44,C.byref(candidate_base),2)
        queue_candidates.append(dict(identity=[2,state,draw[0],candidate_base.value,0],queue_index=qi,record=record,draw=draw,extracted=bool(ok),bytes=asset_size.value))
      assert len(queue_candidates)==extra.value
      road_regions=[]
      for qi in sorted({item['queue_index'] for item in queue_candidates}):
       geometry=C.create_string_buffer(3472)
       assert d.nf_live_completed_region_at(*old_id,sampled,qi,geometry)
       region=struct.unpack_from('<H',geometry.raw,256)[0]
       table=struct.unpack_from('<I',geometry.raw,20)[0];descriptor=table+region*48
       desc=C.create_string_buffer(48);assert d.nf_live_completed_snapshot_read(*old_id,descriptor,desc,48)
       material=(C.c_uint32*5)()
       selected=d.nf_live_completed_road_material_plan(*old_id,state,descriptor,material)
       road_asset=C.c_void_p();road_size=C.c_size_t()
       road_ok=d.nf_live_completed_road_candidate(*old_id,state,descriptor,C.byref(road_asset),C.byref(road_size))
       if road_ok:
        (root/f'camera/road-candidate-{old_id[1]}-{region}.bin').write_bytes(C.string_at(road_asset,road_size.value));d.nf_surface_free(road_asset)
       road_regions.append(dict(identity=[1,state,descriptor,8,0],extracted=bool(road_ok),bytes=road_size.value,queue_index=qi,region=region,descriptor=descriptor,geometry_vertices=struct.unpack_from('<H',geometry.raw,242)[0],primary_material=struct.unpack_from('<H',desc.raw,8)[0],alternate_material=struct.unpack_from('<H',desc.raw,4)[0],material_selected=bool(selected),material_plan=list(material)))
      Path(str(stem)+'-roads.json').write_text(json.dumps(road_regions,indent=2))
      Path(str(stem)+'-queue.json').write_text(json.dumps(queue_candidates,indent=2))
      Path(str(stem)+'.json').write_text(json.dumps(dict(identity=[2,state,source,base.value,0],slot=slot.value,alpha=.5,candidate_bounds=list(struct.unpack_from('<4H',plan.raw,6)),bounds=list(bounds),queue_entrants=extra.value)))
     invocation_transitions.append(dict(scene=old_id[1],index=invocation,slot=slot.value,alpha=.5,draws=draw_count,draw=list(struct.unpack_from('<8I',plan.raw,20)) if draw_count else None,extracted=bool(extracted),bytes=candidate_size.value,rejection_stage=d.nf_live_object_candidate_stage()))
    if struct.unpack_from('<I',plan.raw)[0]==0:counts['invocation_plan_midpoint_empty']+=1
  invocation_frames.append(((epoch,h[4],h[5],h[6]),bytes(retained),inv_count.value,empty_invocations,b,bytes(invocations)))
  for inv_index in range(inv_count.value):
   record=(C.c_ubyte*16)()
   assert d.nfs_visibility_object_region(C.byref(invocations,inv_index*448+12),C.byref(invocations,inv_index*448+268),record)==1
   assert bytes(record)==bytes(invocations)[inv_index*448+432:inv_index*448+448]
   counts['owned_invocation_region_exact']+=1
  invocation_addresses=[struct.unpack_from('<I',bytes(invocations),i*448)[0] for i in range(inv_count.value)]
  assert all(obj['object'] in invocation_addresses for obj in objects)
  counts['object_invocations_without_emitted_address']+=sum(address not in [obj['object'] for obj in objects] for address in invocation_addresses)
  saved_inv=bytes(invocations);saved_n=inv_count.value
  assert not d.nf_live_completed_object_invocations(epoch,h[4],h[5],h[6]+1,invocations,64,C.byref(inv_count))
  assert bytes(invocations)==saved_inv and inv_count.value==saved_n
  if saved_n:
   assert not d.nf_live_completed_object_invocations(epoch,h[4],h[5],h[6],invocations,saved_n-1,C.byref(inv_count))
   assert bytes(invocations)==saved_inv and inv_count.value==saved_n
  origins=[];wall_passes=[]
  for command in commands:
   if command[0]==3:origins.append(None);wall_passes.append(None);continue
   origin=(C.c_uint32*12)()
   assert d.nf_live_completed_surface_origin(epoch,h[4],h[5],h[6],command[1],origin)
   origins.append(list(origin))
   wall_pass=(C.c_uint32*3)(123,456,789)
   if command[0]==2:
    assert d.nf_live_completed_wall_pass(epoch,h[4],h[5],h[6],command[1],wall_pass)
    wall_passes.append(list(wall_pass));saved=list(wall_pass)
    assert not d.nf_live_completed_wall_pass(epoch,h[4],h[5],h[6]+1,command[1],wall_pass) and list(wall_pass)==saved
   else:
    assert not d.nf_live_completed_wall_pass(epoch,h[4],h[5],h[6],command[1],wall_pass) and list(wall_pass)==[123,456,789]
    wall_passes.append(None)
  dispatch_samples.append(dict(serial=h[4],model_position=model_position,object_regions=objects,commands=commands,origins=origins,wall_passes=wall_passes))
  selected=[(i,c[2],int(bool(wp[1])),c[5]) for i,(c,wp) in enumerate(zip(commands,wall_passes)) if c[0]==2]
  selection=(C.c_uint32*(len(selected)*4))(*(v for row in selected for v in row));ordered=(C.c_uint32*258)()
  assert d.nf_live_completed_ordered_dispatch(epoch,h[4],h[5],h[6],selection,len(selected),ordered)
  assert ordered[0]==len(commands) and list(ordered[1:ordered[0]+1])==list(range(len(commands)))
  saved_order=bytes(ordered)
  for bad_id in ((epoch+1,h[4],h[5],h[6]),(epoch,h[4]+10000,h[5],h[6]),(epoch,h[4],h[5]+1,h[6]),(epoch,h[4],h[5],h[6]+1)):
   assert not d.nf_live_completed_ordered_dispatch(*bad_id,selection,len(selected),ordered) and bytes(ordered)==saved_order
  counts['owned_order_exact']+=1;counts['owned_order_identity_atomic']+=4
  reconstructed_order=(C.c_uint32*258)()
  assert d.nf_live_completed_reconstructed_order(epoch,h[4],h[5],h[6],reconstructed_order)
  assert bytes(reconstructed_order)==bytes(ordered)
  for bad_id in ((epoch+1,h[4],h[5],h[6]),(epoch,h[4]+10000,h[5],h[6]),(epoch,h[4],h[5]+1,h[6]),(epoch,h[4],h[5],h[6]+1)):
   assert not d.nf_live_completed_reconstructed_order(*bad_id,reconstructed_order) and bytes(reconstructed_order)==saved_order
  counts['all_native_reconstructed_order']+=1;counts['all_native_order_identity_atomic']+=4
  owned_packet=C.c_void_p();owned_size=C.c_size_t()
  assert d.nf_live_completed_ordered_packet(epoch,ptr,h[2],C.byref(owned_packet),C.byref(owned_size))
  owned_bytes=C.string_at(owned_packet,owned_size.value)
  assert owned_bytes==C.string_at(ptr,h[2])
  d.nf_scene_packet_free(owned_packet)
  if h[4] in (140,141):(root/'camera'/f'owned-order-scene-{h[4]}.bin').write_bytes(owned_bytes)
  rejected=C.c_void_p(123);rejected_size=C.c_size_t(456)
  assert not d.nf_live_completed_ordered_packet(epoch+1,ptr,h[2],C.byref(rejected),C.byref(rejected_size)) and rejected.value==123 and rejected_size.value==456
  counts['owned_order_packet_exact']+=1
  publication_start=time.perf_counter_ns()
  assert d.nf_live_completed_publish_ordered(ordered_store,epoch,ptr,h[2])
  publication_ms=(time.perf_counter_ns()-publication_start)/1000000
  dispatch_samples[-1]['ordered_publication_ms']=publication_ms
  pair=Pair();assert d.nf_snapshot_acquire(ordered_store,h[6],0,C.byref(pair))==2
  try:
   assert pair.time.epoch==epoch and pair.time.older==pair.time.newer==h[4]
   assert C.string_at(pair.older,pair.older_size)==owned_bytes
   assert not d.nf_live_completed_publish_ordered(ordered_store,epoch,ptr,h[2])
   assert C.string_at(pair.older,pair.older_size)==owned_bytes
  finally:d.nf_snapshot_release(ordered_store)
  counts['ordered_publication_exact']+=1;counts['ordered_publication_pinned_rejection']+=1
  if h[4] in (140,141):
   (root/'camera'/f'native-order-{h[4]}.bin').write_bytes(struct.pack('<5I',0x314f444e,h[4],h[5],h[6],reconstructed_order[0])+bytes(reconstructed_order)[4:4+reconstructed_order[0]*4])
  counts['dispatch_order_exact']+=1
  if True: # Independently reconstruct every captured queue at its retained pose.
   batch=C.create_string_buffer(batch_bytes)
   assert d.nf_live_completed_queue_plans(epoch,h[4],h[5],h[6],retained,batch)
   queue_records=[struct.unpack_from('<4I',batch.raw,8+qi*2068) for qi in range(struct.unpack_from('<I',batch.raw)[0])]
   traversal=[(record,pass_id,lr) for pass_id,lr in ((0,0x03004da4),(1,0x03004de8)) for record in reversed(queue_records) if not (struct.unpack('<8H',struct.pack('<4I',*record))[5]&8)]
   captured_traversal=[(tuple(row[:4]),row[5],row[4]) for row in region_records if row[8]==0]
   assert traversal==captured_traversal,('root traversal',h[4])
   counts['root_region_traversal_exact']+=1
   packed=b''.join(struct.pack('<4I',*record) for record in queue_records)
   schedule=C.create_string_buffer(4+queue_capacity*48)
   assert d.nf_root_region_schedule(packed,len(queue_records),schedule)
   native_count=struct.unpack_from('<I',schedule.raw)[0]
   native=[struct.unpack_from('<6I',schedule.raw,4+i*24) for i in range(native_count)]
   assert [(tuple(row[2:]),row[1],0x03004de8 if row[1] else 0x03004da4) for row in native]==captured_traversal
   assert all(tuple(row[2:])==queue_records[row[0]] for row in native)
   counts['native_root_schedule_exact']+=1
   for pass_id in (0,1):
    roots=[row for row in region_records if row[8]==0 and row[5]==pass_id]
    ids=[row[0]&65535 for row in roots]
    sampled_ids=(C.c_uint32*len(ids))(*ids)
    intervals=(C.c_uint32*(len(roots)*3))(*(v for row in roots for v in (row[0]&65535,row[6],row[7])))
    anchors=(C.c_uint32*(queue_capacity+1))(*[0xdeadbeef]*(queue_capacity+1));before=bytes(anchors)
    ok=d.nf_root_region_anchors(sampled_ids,len(ids),intervals,len(roots),anchors)
    if ids and len(set(ids))==len(ids):
     assert ok and anchors[0]==len(ids) and list(anchors)[1:len(ids)+1]==[row[6] for row in roots]
     counts['native_root_anchors_exact']+=1
    else:
     assert not ok and bytes(anchors)==before
     counts['native_root_anchors_conservative_rejection']+=1
   saved=schedule.raw
   assert not d.nf_root_region_schedule(packed,queue_capacity+1,schedule) and schedule.raw==saved
   assert not d.nf_root_region_schedule(None,1,schedule) and schedule.raw==saved
   counts['native_root_schedule_atomic']+=2
   reconstructed=[]
   for qi in range(struct.unpack_from('<I',batch.raw)[0]):
    offset=4+qi*2068;number=struct.unpack_from('<I',batch.raw,offset)[0]
    record=list(struct.unpack_from('<8H',batch.raw,offset+4))
    for di in range(number):
     draw=struct.unpack_from('<8I',batch.raw,offset+20+di*32)
     reconstructed.append(dict(queue_index=qi,record=record,source=draw[0],pass_id=draw[1],draw=list(draw[2:])))
   if h[4]==53:(root/'camera/repeated-scene-plans.json').write_text(json.dumps(dict(serial=53,commands=commands,origins=origins,wall_passes=wall_passes,reconstructed=reconstructed),indent=2))
   expected_queue=collections.Counter((c[2],int(bool(wp[1])),tuple(struct.unpack('<8H',struct.pack('<4I',*o[2:6])))) for c,o,wp in zip(commands,origins,wall_passes) if c[0]==2 and not c[5])
   native_queue=collections.Counter((x['source'],x['pass_id'],tuple(x['record'])) for x in reconstructed)
   dispatch_samples[-1]['native_queue_coverage']=dict(draws=len(reconstructed),missing=list((expected_queue-native_queue).elements()),extra=list((native_queue-expected_queue).elements()))
   assert native_queue==expected_queue,('native queue coverage',h[4],dispatch_samples[-1]['native_queue_coverage'])
   block_shapes=[]
   for row in region_records:
    if row[8]!=0:continue
    try:block=region_block(row,commands,origins,wall_passes)
    except ValueError as error:
     counts['region_block_complex']+=1
     block_shapes.append(dict(region=row[0]&65535,pass_id=row[5],supported=False,reason=str(error)))
     continue
    counts['region_block_simple']+=1
    counts['region_block_empty' if row[6]==row[7] else 'region_block_nonempty']+=1
    block_shapes.append(dict(region=row[0]&65535,pass_id=row[5],supported=True,**block))
   dispatch_samples[-1]['block_shapes']=block_shapes
   deferred=[]
   for j,(command,origin,wallpass) in enumerate(zip(commands,origins,wall_passes)):
    if command[0]!=2 or command[5] or not wallpass[1]:continue
    owners=[row for row in region_records if row[6]<=j<row[7] and tuple(row[:4])==tuple(origin[2:6])]
    assert owners,('deferred owner missing',h[4],j)
    deepest=max(row[8] for row in owners);owners=[row for row in owners if row[8]==deepest]
    assert len(owners)==1,('deferred owner ambiguous',h[4],j,owners)
    owner=owners[0]
    deferred_positions=[k for k in range(owner[6],owner[7]) if commands[k][0]==2 and not commands[k][5] and tuple(origins[k][2:6])==tuple(owner[:4]) and wall_passes[k][1]]
    assert deferred_positions==list(range(owner[7]-len(deferred_positions),owner[7])),('deferred suffix',h[4],owner)
    queue_matches=[qi for qi,r in enumerate(queue_records) if tuple(r)==tuple(owner[:4])];assert len(queue_matches)==1
    planned_suffix=[x['source'] for x in reconstructed if x['queue_index']==queue_matches[0] and x['pass_id']==1]
    assert planned_suffix==[commands[k][2] for k in deferred_positions]
    array=(C.c_uint32*len(planned_suffix))(*planned_suffix);out=(C.c_uint32*129)()
    kept=[(commands[k][2],k) for k in deferred_positions if k!=j]
    retained_array=(C.c_uint32*(2*len(kept)))(*(v for pair in kept for v in pair))
    assert d.nf_wall_insertions(array,len(planned_suffix),retained_array,len(kept),owner[7],out)
    assert out[0]==1 and out[1]==command[2] and out[65]==next((k for k in deferred_positions if k>j),owner[7])
    counts['deferred_suffix_insertion_exact']+=1
    counts['deferred_owner_exact']+=1
    counts['deferred_owner_root_pass_'+str(owner[5])]+=1
    deferred.append(dict(command=j,source=command[2],region=owner[0]&65535,caller=owner[4],root_pass=owner[5],depth=owner[8],range=owner[6:8],wall_dispatch=wallpass[0]))
   if deferred:dispatch_samples[-1]['deferred_owners']=deferred
   for row in region_records:
    if row[8]!=0:continue
    if row[5]!=0:counts['wall_insertion_deferred_root_skipped']+=1;continue
    packed_record=tuple(row[:4]);pass_id=row[5]
    candidates=[qi for qi,r in enumerate(queue_records) if tuple(r)==packed_record]
    if len(candidates)!=1:counts['wall_insertion_ambiguous_region_skipped']+=1;continue
    planned=[x['source'] for x in reconstructed if x['queue_index']==candidates[0] and x['pass_id']==pass_id]
    positions=[j for j in range(row[6],row[7]) if commands[j][0]==2 and not commands[j][5] and tuple(origins[j][2:6])==packed_record and int(bool(wall_passes[j][1]))==pass_id]
    assert planned==[commands[j][2] for j in positions],('region wall order',h[4],row,planned,positions)
    if not positions:continue
    if positions!=list(range(row[6],row[6]+len(positions))):counts['wall_insertion_nonprefix_region_skipped']+=1;continue
    tail=positions[-1]+1
    sampled_sources=(C.c_uint32*len(planned))(*planned)
    for omitted in [None]+list(range(len(planned))):
     kept=[(source,position) for i,(source,position) in enumerate(zip(planned,positions)) if i!=omitted]
     retained_walls=(C.c_uint32*(len(kept)*2))(*(v for pair in kept for v in pair));insertions=(C.c_uint32*129)()
     assert d.nf_wall_insertions(sampled_sources,len(planned),retained_walls,len(kept),tail,insertions)
     if omitted is None:assert insertions[0]==0;counts['wall_insertion_captured_blocks_exact']+=1
     else:
      expected=positions[omitted+1] if omitted+1<len(positions) else tail
      assert insertions[0]==1 and insertions[1]==planned[omitted] and insertions[65]==expected
      counts['wall_insertion_captured_omission_exact']+=1
   available=list(reconstructed);native_selections=[]
   object_keys=[(c[3],c[4],tuple(o[2:6])) for c,o in zip(commands,origins) if c[0]==2 and c[5]]
   # Each emitted object/descriptor/record group in this fixture has one draw.
   # More complex or repeated invocations require explicit invocation identity.
   assert len(object_keys)==len(set(object_keys)),('object invocation grouping required',h[4])
   for command_index,(command,origin,wp) in enumerate(zip(commands,origins,wall_passes)):
    if command[0]!=2:continue
    record=list(struct.unpack('<8H',struct.pack('<4I',*origin[2:6])))
    pool=available
    if command[5]:
     object_plan=C.create_string_buffer(2068)
     assert d.nf_live_completed_object_wall_plan(epoch,h[4],h[5],h[6],retained,command[1],object_plan)
     object_record=list(struct.unpack_from('<8H',object_plan.raw,4));pool=[]
     for di in range(struct.unpack_from('<I',object_plan.raw)[0]):
      draw=struct.unpack_from('<8I',object_plan.raw,20+di*32)
      pool.append(dict(source=draw[0],pass_id=draw[1],record=object_record,draw=list(draw[2:])))
    matches=[x for x in pool if x['source']==command[2] and x['pass_id']==int(bool(wp[1])) and x['record']==record]
    assert len(matches)==1,('queue occurrence ambiguity',h[4],command)
    plan=matches[0];pool.remove(plan)
    native_selections.append((command_index,plan['source'],plan['pass_id'],command[5]))
    if command[5]:
     assert not pool,('extra object plan draws',h[4],pool)
     counts['native_object_plan_complete']+=1
    arguments=(C.c_uint32*6)();provenance=(C.c_uint64*5)()
    assert d.nf_live_completed_surface_arguments(epoch,h[4],h[5],h[6],command[1],arguments)
    assert d.nf_live_completed_texture_provenance(epoch,h[4],h[5],h[6],command[1],provenance)
    edge,material,texture,shift,height,flags=plan['draw']
    assert (material,flags)==(arguments[4],arguments[5]),('queue material',h[4],command)
    assert (texture,1<<shift,height)==tuple(provenance[:3]),('queue texture',h[4],command)
    counts['native_object_material_exact' if command[5] else 'native_queue_material_exact']+=1
   assert not available
   native_selection=(C.c_uint32*(len(native_selections)*4))(*(v for row in native_selections for v in row))
   native_order=(C.c_uint32*258)()
   assert d.nf_live_completed_ordered_dispatch(epoch,h[4],h[5],h[6],native_selection,len(native_selections),native_order)
   assert native_order[0]==len(commands) and list(native_order[1:len(commands)+1])==list(range(len(commands)))
   counts['reconstructed_native_order_exact']+=1
   dispatch_samples[-1]['reconstructed_native_order']=list(native_order[1:native_order[0]+1])
   # A selected wall may disappear while roads/model retain their exact slots.
   subset=native_selections[1:];subset_data=(C.c_uint32*(len(subset)*4))(*(v for row in subset for v in row))
   assert d.nf_live_completed_ordered_dispatch(epoch,h[4],h[5],h[6],subset_data,len(subset),native_order)
   assert list(native_order[1:native_order[0]+1])==[i for i in range(len(commands)) if i!=native_selections[0][0]]
   counts['reconstructed_native_order_omission']+=1
  if h[4] in (140,141):
   def read_owned(address,size):
    out=C.create_string_buffer(size);assert d.nf_live_completed_snapshot_read(epoch,h[4],h[5],h[6],address,out,size),(hex(address),size);return out.raw
   identity=(epoch,h[4],h[5],h[6]);pose=C.create_string_buffer(104);expected=C.create_string_buffer(result_bytes);actual=C.create_string_buffer(result_bytes)
   assert d.nf_live_completed_visibility_pose(*identity,pose)
   assert d.nf_live_visibility_evaluate(*identity,expected)
   assert d.nf_live_completed_visibility_at(*identity,pose,actual) and actual.raw==expected.raw
   counts['retained_pose_exact']+=1
   for bad_identity in ((epoch+1,h[4],h[5],h[6]),(epoch,h[4]+10000,h[5],h[6]),(epoch,h[4],h[5]+1,h[6]),(epoch,h[4],h[5],h[6]+1)):
    before=pose.raw;before_result=actual.raw
    assert not d.nf_live_completed_visibility_pose(*bad_identity,pose) and pose.raw==before
    assert not d.nf_live_completed_visibility_at(*bad_identity,pose,actual) and actual.raw==before_result
    counts['pose_identity_atomic']+=1
   pose_samples.append(dict(serial=h[4],inputs=list(struct.unpack('<26i',pose.raw))))
   if h[4]==141:
    a=struct.pack('<26i',*pose_samples[0]['inputs']);b=pose.raw;sample=C.create_string_buffer(104)
    for alpha in [0,.25,.5,.671377,.75,.76,.78,.8,.82,.84,.86,.88,.9,.95,.99,.999999,1]:
     assert d.nf_visibility_pose_sample(a,b,alpha,sample)
     if alpha==0:assert sample.raw==a
     if alpha==1:assert sample.raw==b
     evaluated=C.create_string_buffer(result_bytes)
     assert d.nf_live_completed_visibility_at(*earlier_identity,sample,evaluated)
     count=struct.unpack_from('<H',evaluated.raw,238)[0];assert count<=queue_capacity
     batch=C.create_string_buffer(batch_bytes);assert d.nf_live_completed_queue_plans(*earlier_identity,sample,batch)
     assert struct.unpack_from('<I',batch.raw)[0]==count
     for bi in range(count):
      single=C.create_string_buffer(2068);assert d.nf_live_completed_wall_plan(*earlier_identity,sample,bi,single)
      assert batch.raw[4+bi*2068:4+(bi+1)*2068]==single.raw
     assert batch.raw[4+count*2068:]==bytes((queue_capacity-count)*2068)
     saved_batch=batch.raw;assert not d.nf_live_completed_queue_plans(earlier_identity[0]+1,*earlier_identity[1:],sample,batch) and batch.raw==saved_batch
     counts['queue_batch_exact']+=1

     records=[list(struct.unpack_from('<5H',evaluated.raw,256+i*16)) for i in range(count)]
     def old_read(address,amount):
      buf=C.create_string_buffer(amount);assert d.nf_live_completed_snapshot_read(*earlier_identity,address,buf,amount);return buf.raw
     matrix_address=struct.unpack_from('<I',evaluated.raw,0x54)[0];matrix=sample.raw[56:104];matrix_reads=[0]
     @Read
     def sampled_reader(ctx,address,out,amount):
      if matrix_address<=address and address+amount<=matrix_address+48:
       C.memmove(out,matrix[address-matrix_address:address-matrix_address+amount],amount);matrix_reads[0]+=1;return 1
      return d.nf_live_completed_snapshot_read(*earlier_identity,address,out,amount)
     reciprocal=old_read(0x08627700,65536)+old_read(0x08637700,65536)
     suppressed_records=[];all_wall_plans=[];draw_plans=[];gates=[];wanted={v['source'] for v in candidate_gates}
     inputs=[(qi,evaluated.raw[256+qi*16:256+(qi+1)*16],None) for qi in range(count)]+[(count+i,x['record'],x) for i,x in enumerate(object_records)]
     for qi,record,object_event in inputs:
      region=struct.unpack_from('<H',record)[0]
      if struct.unpack_from('<H',record,10)[0]&8:
       merged_plan=C.create_string_buffer(b'X'*2068,2068)
       assert d.nf_live_completed_wall_plan(*earlier_identity,sample,qi,merged_plan)
       assert merged_plan.raw[:4]==bytes(4) and merged_plan.raw[4:20]==record and merged_plan.raw[20:]==bytes(2048)
       counts['merged_wall_plan_empty']+=1
       suppressed_records.append(dict(queue_index=qi,region=region,flags=struct.unpack_from('<H',record,10)[0]));continue
      desc=old_read(struct.unpack_from('<I',evaluated.raw,20)[0]+region*48,48);first,vertices=struct.unpack_from('<HH',desc);start=struct.unpack_from('<I',evaluated.raw,16)[0]+first*68
      state_copy=C.create_string_buffer(evaluated.raw[:256],256);edges=C.create_string_buffer(32*52);stream=C.create_string_buffer(64*24)
      status=d.nfs_visibility_region_reconstruct(state_copy,record,sampled_reader,None,reciprocal,edges,len(edges),stream,len(stream));assert status==1
      native_region=C.create_string_buffer(3472)
      if object_event is None:
       assert d.nf_live_completed_region_at(*earlier_identity,sample,qi,native_region)
       assert native_region.raw==state_copy.raw+record+edges.raw+stream.raw
       counts['sampled_region_exact']+=1
      else:counts['sampled_object_region_reconstructed']+=1
      vertices_data=old_read(start,vertices*68);plan=C.create_string_buffer(32*24);plan_count=C.c_uint();deferred=C.c_uint32()
      assert d.nfs_visibility_wall_draw_plan(state_copy,vertices_data,vertices,edges,0,sampled_reader,None,plan,32,C.byref(plan_count),C.byref(deferred))
      passes=[(0,plan.raw,plan_count.value)];mask=deferred.value
      if mask:
       assert d.nfs_visibility_wall_draw_plan(state_copy,vertices_data,vertices,edges,mask,sampled_reader,None,plan,32,C.byref(plan_count),C.byref(deferred))
       passes.append((1,plan.raw,plan_count.value))
      if True:
       plan_fn=d.nf_live_completed_wall_plan if object_event is None else d.nf_live_completed_object_wall_plan
       plan_ordinal=qi if object_event is None else object_event['ordinal']
       owned_plan=C.create_string_buffer(2068);assert plan_fn(*earlier_identity,sample,plan_ordinal,owned_plan)
       expected=[]
       for pass_id,raw,number in passes:
        for di in range(number):
         draw=struct.unpack_from('<6I',raw,di*24);expected.append((start+draw[0]*68,pass_id,*draw))
       assert struct.unpack_from('<I',owned_plan.raw)[0]==len(expected) and owned_plan.raw[4:20]==record
       assert [struct.unpack_from('<8I',owned_plan.raw,20+i*32) for i in range(len(expected))]==expected
       before_plan=owned_plan.raw;assert not plan_fn(*earlier_identity,sample,999,owned_plan) and owned_plan.raw==before_plan
       for bad_identity in [(earlier_identity[0]+1,*earlier_identity[1:]),(earlier_identity[0],earlier_identity[1]+10000,*earlier_identity[2:]),(*earlier_identity[:2],earlier_identity[2]+1,earlier_identity[3]),(*earlier_identity[:3],earlier_identity[3]+1)]:
        assert not plan_fn(*bad_identity,sample,plan_ordinal,owned_plan) and owned_plan.raw==before_plan
        counts['wall_plan_identity_atomic']+=1
       assert not plan_fn(*earlier_identity,None,plan_ordinal,owned_plan) and owned_plan.raw==before_plan
       kept_plans.append((owned_plan,hashlib.sha256(owned_plan.raw).hexdigest()))
       counts['native_wall_plan_exact' if object_event is None else 'native_object_wall_plan_exact']+=1
      for pass_id,raw,number in passes:
       for di in range(number):
        edge,material,texture,shift,height,flags=struct.unpack_from('<6I',raw,di*24);source=start+edge*68
        item=dict(object_dispatch=object_event['ordinal'] if object_event else None,source=source,region=region,queue_index=qi,pass_id=pass_id,material=material,texture=texture,width=1<<shift,height=height,flags=flags,viewport=list(struct.unpack_from('<4H',record,2)))
        all_wall_plans.append(item)
        if source in wanted:draw_plans.append(item)

      before=native_region.raw
      for bad_id,bad_index in [(earlier_identity,queue_capacity),(earlier_identity,count),((earlier_identity[0],earlier_identity[1],earlier_identity[2],earlier_identity[3]+1),qi)]:
       assert not d.nf_live_completed_region_at(*bad_id,sample,bad_index,native_region) and native_region.raw==before
       counts['sampled_region_atomic']+=1
      for vi in range(vertices):
       source=start+vi*68
       if source in wanted:gates.append(dict(source=source,region=region,queue_index=qi,flags=struct.unpack_from('<H',edges.raw,vi*52+48)[0],viewport=list(struct.unpack_from('<4H',record,2))))
     assert matrix_reads[0]>0
     portal_samples.append(dict(alpha=alpha,records=records,suppressed_records=suppressed_records,all_wall_plans=all_wall_plans,gates=gates,draw_plans=draw_plans,matrix_reads=matrix_reads[0]))
     clipped=(C.c_uint16*(256*4))();extra=C.c_uint(999)
     assert d.nf_live_completed_sampled_bounds(*earlier_identity,sample,clipped,256,C.byref(extra))
     original=next(x['commands'] for x in dispatch_samples if x['serial']==140)
     selected_sources={x['source'] for x in all_wall_plans}
     for command in original:
      if command[0]!=2:continue
      expected=next((x['viewport'] for x in all_wall_plans if x['source']==command[2]),[0,0,0,0])
      assert list(clipped[command[1]*4:command[1]*4+4])==expected
     assert extra.value==len(selected_sources-{c[2] for c in original if c[0]==2})
     saved=bytes(clipped);saved_extra=extra.value
     assert not d.nf_live_completed_sampled_bounds(earlier_identity[0]+1,*earlier_identity[1:],sample,clipped,256,C.byref(extra)) and bytes(clipped)==saved and extra.value==saved_extra
     counts['sampled_bounds_exact']+=1
    for alpha in [-1,2,float('nan'),float('inf')]:
     before=sample.raw;assert not d.nf_visibility_pose_sample(a,b,alpha,sample) and sample.raw==before
    malformed=bytearray(a);struct.pack_into('<i',malformed,8,0)
    before=sample.raw;assert not d.nf_visibility_pose_sample(bytes(malformed),b,.5,sample) and sample.raw==before
    counts['pose_adapter_invalid_atomic']+=5

   state=read_owned(50331840,256);source=read_owned(139937176,68)
   base=struct.unpack_from('<H',source,44)[0];materials=struct.unpack_from('<I',state,32)[0]
   material=read_owned(materials+base*32,32);anim=struct.unpack_from('<H',material)[0]
   animation=read_owned(struct.unpack_from('<I',state,72)[0]+anim*8,8)
   frame=struct.unpack_from('<H',animation,2)[0];resolved=read_owned(materials+(base+frame)*32,32)
   texture=(struct.unpack_from('<I',state)[0]+struct.unpack_from('<I',resolved,4)[0])&0xffffffff
   width=1<<struct.unpack_from('<H',resolved,26)[0];height=struct.unpack_from('<H',resolved,10)[0]
   indices=read_owned(texture,width*height);palette=C.create_string_buffer(512);palette_available=bool(d.nf_live_completed_snapshot_read(epoch,h[4],h[5],h[6],0x05000000,palette,512))
   used=sorted(set(indices));palettes=[];palette_bytes=[]
   for draw in range(256):
    key=(C.c_uint32*3)();colors=C.create_string_buffer(512)
    if not d.nf_live_palette_draw(epoch,h[4],h[5],h[6],draw,key,colors):break
    palette_bytes.append(colors.raw)
    selected=b''.join(colors.raw[index*2:index*2+2] for index in used)
    palettes.append(dict(draw=draw,key=list(key),all_hash=hashlib.sha256(colors.raw).hexdigest(),used_hash=hashlib.sha256(selected).hexdigest()))
    if key[0]==2 and key[1]==139937176 or h[4]==140 and draw==0:
     (root/'camera'/f'candidate-palette-{h[4]}.bin').write_bytes(colors.raw)
   assert palettes
   agreed=C.create_string_buffer(512);assert d.nf_candidate_palette(indices,len(indices),b''.join(palette_bytes),len(palette_bytes),agreed)
   assert agreed.raw==palette_bytes[0]
   scene_palette_bytes[h[4]]=b"".join(palette_bytes)
   candidate_palettes.append(dict(serial=h[4],used_indices=len(used),distinct_all=len(set(x['all_hash'] for x in palettes)),distinct_used=len(set(x['used_hash'] for x in palettes)),draws=palettes))
   candidate_sources.append(dict(serial=h[4],base=base,animation=anim,frame=frame,texture=texture,width=width,height=height,source_hash=hashlib.sha256(source).hexdigest(),index_hash=hashlib.sha256(indices).hexdigest(),palette_available=palette_available))
   bad=C.create_string_buffer(b'X'*68);saved=bad.raw
   assert not d.nf_live_completed_snapshot_read(epoch,h[4],h[5],h[6]+1,139937176,bad,68) and bad.raw==saved
   assert not d.nf_live_completed_snapshot_read(epoch,h[4],h[5],h[6],0xffffffff,bad,68) and bad.raw==saved
  if h[4]==140:
   earlier_identity=(epoch,h[4],h[5],h[6])
   early=C.c_void_p();early_size=C.c_size_t()
   assert d.nf_live_completed_wall_candidate(*earlier_identity,50331840,139937176,C.byref(early),C.byref(early_size))
   (root/'camera/candidate-at-publication-140.bin').write_bytes(C.string_at(early,early_size.value));d.nf_surface_free(early)
   counts['candidate_before_future_scene']+=1
   # Discover only wall sources belonging to already captured road regions.
   ids=[struct.unpack_from('<5I',sections[5],8+i*20) for i in range(n)]
   existing={item[2] for item in ids if item[0]==2};seen=set();accepted=[];rejected=[]
   for road in ids:
    if road[0]!=1:continue
    owned_state=read_owned(road[1],256);desc=read_owned(road[2],48);first,vertex_count=struct.unpack_from('<HH',desc)
    assert 0<vertex_count<=32
    vertex_base=struct.unpack_from('<I',owned_state,16)[0]+first*68
    for vi in range(vertex_count):
     source_address=vertex_base+vi*68
     if source_address in seen or source_address in existing:continue
     seen.add(source_address);candidate=C.c_void_p();candidate_size=C.c_size_t()
     if d.nf_live_completed_wall_candidate(*earlier_identity,road[1],source_address,C.byref(candidate),C.byref(candidate_size)):
      record=C.string_at(candidate,candidate_size.value);d.nf_surface_free(candidate)
      accepted.append(dict(source=source_address,region=road[2],bytes=len(record),sha256=hashlib.sha256(record).hexdigest()))
      (root/'camera'/f'enumerated-140-{source_address}.bin').write_bytes(record)
     else:rejected.append(source_address)
   enumeration.append(dict(serial=140,road_regions=sum(i[0]==1 for i in ids),attempts=len(seen),accepted=accepted,rejected=rejected))
   assert any(i['source']==139937176 for i in accepted) # Expected result, not selection input.
   result=C.create_string_buffer(result_bytes);assert d.nf_live_visibility_evaluate(*earlier_identity,result)
   evaluated=result.raw;queue_count=struct.unpack_from('<H',evaluated,238)[0];assert queue_count<=queue_capacity
   reciprocal=read_owned(0x08627700,65536)+read_owned(0x08637700,65536)
   @Read
   def gate_reader(ctx,address,out,amount):return d.nf_live_completed_snapshot_read(*earlier_identity,address,out,amount)
   wanted={i['source'] for i in accepted}
   for qi in range(queue_count):
    record=evaluated[256+qi*16:256+(qi+1)*16];region=struct.unpack_from('<H',record)[0]
    desc=read_owned(struct.unpack_from('<I',evaluated,20)[0]+region*48,48);first,vertex_count=struct.unpack_from('<HH',desc)
    start=struct.unpack_from('<I',evaluated,16)[0]+first*68
    if not any(start+i*68 in wanted for i in range(vertex_count)):continue
    state_copy=C.create_string_buffer(evaluated[:256],256);edges=C.create_string_buffer(32*52);stream=C.create_string_buffer(64*24)
    status=d.nfs_visibility_region_reconstruct(state_copy,record,gate_reader,None,reciprocal,edges,len(edges),stream,len(stream))
    for vi in range(vertex_count):
     address=start+vi*68
     if address in wanted:candidate_gates.append(dict(source=address,region=region,queue_index=qi,viewport=list(struct.unpack_from('<4H',record,2)),reconstruct_status=status,edge_flags=struct.unpack_from('<H',edges.raw,vi*52+48)[0] if status==1 else None))
  current={};ordinal=0;scene_bounds=[]
  for index in order:
   if index==0xffffffff:continue
   ident=(C.c_uint32*5)();p=(C.c_uint64*5)();args=(epoch,h[4],h[5],h[6],ordinal)
   assert d.nf_live_completed_surface_identity(*args,ident)
   bounds=(C.c_uint16*4)();assert d.nf_live_completed_surface_bounds(*args,bounds)
   if h[4] in (140,141) and ident[2]==139970292:
    arguments=(C.c_uint32*6)();assert d.nf_live_completed_surface_arguments(*args,arguments)
    owner=C.c_uint32();state_buffer=C.create_string_buffer(256)
    assert d.nf_live_completed_snapshot_read(epoch,h[4],h[5],h[6],arguments[0],state_buffer,256)
    @Read
    def trace_reader(ctx,address,out,amount):return d.nf_live_completed_snapshot_read(epoch,h[4],h[5],h[6],address,out,amount)
    found=d.nf_wall_owner(trace_reader,None,arguments[0],arguments[2],C.byref(owner))
    descriptor_base=struct.unpack_from('<I',state_buffer.raw,20)[0]
    origin=(C.c_uint32*12)();assert d.nf_live_completed_surface_origin(*args,origin)
    payload=C.create_string_buffer(184);assert d.nf_live_completed_object_region(*args,payload)
    assert payload.raw[168:]==struct.pack('<4I',*list(origin)[2:6])
    assert struct.unpack_from('<H',payload.raw,4+54)[0]==181
    saved=payload.raw;assert not d.nf_live_completed_object_region(epoch,h[4],h[5],h[6]+1,ordinal,payload) and payload.raw==saved
    counts['owned_object_region_exact']+=1
    if h[4]==140:object_records.append(dict(ordinal=ordinal,record=payload.raw[168:],address=struct.unpack_from('<I',payload.raw)[0]))

    missing_wall_trace.append(dict(origin=list(origin),serial=h[4],args=list(arguments),identity=list(ident),bounds=list(bounds),owner_found=bool(found),owner=owner.value,region=(owner.value-descriptor_base)//48 if found else None))

   scene_bounds.append(dict(serial=h[4],ordinal=ordinal,identity=list(ident),bounds=list(bounds)))
   if h[4] in (140,141):draw_bounds.append(scene_bounds[-1])
   saved=list(bounds)
   assert not d.nf_live_completed_surface_bounds(epoch,h[4],h[5],h[6]+1,ordinal,bounds) and list(bounds)==saved
   counts['draw_bounds_atomic']+=1

   assert d.nf_live_completed_texture_provenance(*args,p)
   if ident[0]==1:
    road_args=(C.c_uint32*6)();assert d.nf_live_completed_surface_arguments(*args,road_args)
    material_plan=(C.c_uint32*5)()
    assert d.nf_live_completed_road_material_plan(epoch,h[4],h[5],h[6],road_args[0],road_args[1],material_plan)
    assert material_plan[1]==road_args[4] and (material_plan[2],1<<material_plan[3],material_plan[4])==tuple(p[:3])
    counts['road_material_plan_exact']+=1
   if h[4]==141 and tuple(ident)==(2,50331840,139937176,37,0):
    captured=(C.c_uint32*6)();assert d.nf_live_completed_surface_arguments(*args,captured)
    def earlier_read(address,size):
     data=C.create_string_buffer(size);assert d.nf_live_completed_snapshot_read(*earlier_identity,address,data,size);return data.raw
    state_address=ident[1];source_address=ident[2];st=earlier_read(state_address,256);src=earlier_read(source_address,68);base=struct.unpack_from('<H',src,44)[0];mb=struct.unpack_from('<I',st,32)[0]
    mat=earlier_read(mb+base*32,32);an=earlier_read(struct.unpack_from('<I',st,72)[0]+struct.unpack_from('<H',mat)[0]*8,8)
    resolved_address=mb+(base+struct.unpack_from('<H',an,2)[0])*32;mat=earlier_read(resolved_address,32)
    # Enumerate the bounded 512-entry region table from the earlier state.
    descriptors=struct.unpack_from('<I',st,20)[0];vertices_base=struct.unpack_from('<I',st,16)[0]
    table=earlier_read(descriptors,512*48);owners=[]
    for ri in range(512):
     first,count=struct.unpack_from('<HH',table,ri*48)
     start=vertices_base+first*68
     if 0<count<=32 and start<=source_address<start+count*68 and (source_address-start)%68==0:owners.append(descriptors+ri*48)
    assert len(owners)==1,owners
    descriptor_address=owners[0];flags=struct.unpack_from('<H',src,46)[0]
    assert descriptor_address==captured[1] and flags==captured[5]
    assert flags&256
    synthetic=bytearray(48);struct.pack_into('<HHI',synthetic,36,struct.unpack_from('<H',mat,26)[0],struct.unpack_from('<H',mat,10)[0],(struct.unpack_from('<I',st)[0]+struct.unpack_from('<I',mat,4)[0])&0xffffffff)
    pal=(root/'camera/candidate-palette-140.bin').read_bytes();scratch=0x0f000000
    @Read
    def reader(ctx,address,out,size):
     if address==scratch and size==48:data=synthetic
     elif address==0x05000000 and size==512:data=pal
     else:
      return d.nf_live_completed_snapshot_read(*earlier_identity,address,out,size)
     C.memmove(out,bytes(data),size);return 1
    native_owner=C.c_uint32();assert d.nf_wall_owner(reader,None,state_address,source_address,C.byref(native_owner)) and native_owner.value==descriptor_address
    surface=C.c_void_p();size=C.c_size_t();light=C.c_void_p();ls=C.c_size_t()
    assert d.nf_extract_wall(reader,None,state_address,descriptor_address,source_address,scratch,resolved_address,flags,C.byref(surface),C.byref(size),C.byref(light),C.byref(ls))
    data=C.string_at(surface,size.value);assert hashlib.sha256(data[172:]).hexdigest()==textures[index]
    # Compare the complete record, including cyclic endpoint geometry and UV.
    cursor=8
    for wi in range(index):
     vn,ww,hh=struct.unpack_from('<3I',world,cursor);cursor+=12+vn*40+ww*hh*4
    assert data==world[cursor:cursor+size.value]
    @Read
    def plain_reader(ctx,address,out,amount):return d.nf_live_completed_snapshot_read(*earlier_identity,address,out,amount)
    native=C.c_void_p();native_size=C.c_size_t();bank=scene_palette_bytes[140]
    assert d.nf_extract_wall_candidate(plain_reader,None,state_address,source_address,bank,len(bank)//512,C.byref(native),C.byref(native_size))
    assert C.string_at(native,native_size.value)==data
    bridge=C.c_void_p();bridge_size=C.c_size_t()
    assert d.nf_live_completed_wall_candidate(*earlier_identity,state_address,source_address,C.byref(bridge),C.byref(bridge_size))
    assert C.string_at(bridge,bridge_size.value)==data
    kept_candidate=(bridge,bridge_size.value,hashlib.sha256(data).hexdigest())
    counts['candidate_bridge_exact']+=1
    for wrong in [(earlier_identity[0],140,earlier_identity[2],earlier_identity[3]+1,state_address,source_address),(*earlier_identity,state_address+4,source_address),(*earlier_identity,state_address,source_address+1)]:
     rejected=C.c_void_p(123);rejected_size=C.c_size_t(456)
     assert not d.nf_live_completed_wall_candidate(*wrong,C.byref(rejected),C.byref(rejected_size)) and rejected.value==123 and rejected_size.value==456
     counts['candidate_atomic_rejections']+=1
    d.nf_surface_free(native)
    for address,palettes_to_test,palette_count in [(source_address,bank,0),(source_address+1,bank,len(bank)//512)]:
     rejected=C.c_void_p(123);rejected_size=C.c_size_t(456)
     assert not d.nf_extract_wall_candidate(plain_reader,None,state_address,address,palettes_to_test,palette_count,C.byref(rejected),C.byref(rejected_size)) and rejected.value==123 and rejected_size.value==456
    (root/'camera/candidate-owned-140-surface.bin').write_bytes(data)
    candidate_extractions.append(dict(source_scene=140,reference_scene=141,descriptor=descriptor_address,flags=flags,owner_count=len(owners),bytes=size.value,exact=True,limitation='Target source identity is still supplied by the research case; owning descriptor and flags recovered independently from earlier state. Bounded table scan requires unique valid owner.'))
    d.nf_surface_free(surface);d.nf_surface_free(light)
   animation=(C.c_uint32*6)(*([123]*6))
   if ident[0]==2:
    assert d.nf_live_completed_wall_animation(*args,animation)
    assert animation[4]==animation[5]==p[0]
    counts['wall_selection_matches']+=1
    animation_samples.append(dict(serial=h[4],begin=h[5],end=h[6],identity=list(ident),selection=list(animation)))
    saved=bytes(animation)
    assert not d.nf_live_completed_wall_animation(epoch,h[4],h[5],h[6]+1,ordinal,animation) and bytes(animation)==saved
   else:
    assert not d.nf_live_completed_wall_animation(*args,animation) and list(animation)==[123]*6
    counts['road_rejections']+=1
   current.setdefault(tuple(ident),[]).append((tuple(p),textures[index]));ordinal+=1;counts['reads']+=1
  bad=(C.c_uint64*5)(*([0xcccccccccccccccc]*5));before=bytes(bad)
  assert not d.nf_live_completed_texture_provenance(epoch,h[4],h[5],h[6]+1,0,bad) and bytes(bad)==before
  counts['wrong_boundary_atomic']+=1
  for ident in current.keys()&previous.keys():
   if len(current[ident])!=len(previous[ident]):continue
   for (a,old),(z,new) in zip(previous[ident],current[ident]):
    if old!=new:
     changes=[name for i,name in enumerate(['pointer','width','height','indices','palette']) if a[i]!=z[i]]
     counts['rgba_updates']+=1
     for name in changes:counts[name+'_changes']+=1
     updates.append(dict(serial=h[4],identity=ident,changes=changes,old_pointer=a[0],new_pointer=z[0]))
  captured_packet=C.string_at(ptr,h[2]);clip_metadata=build_clips(captured_packet,epoch,scene_bounds);counts['clip_sidecar_validated']+=1
  if h[4] in (140,141):
   (root/'camera'/f'clip-scene-{h[4]}.json').write_text(json.dumps(clip_metadata,indent=2))
   (root/'camera'/f'clip-scene-{h[4]}.bin').write_bytes(captured_packet)
  previous=current;last=(epoch,h[4],h[5],h[6],0);counts['scenes']+=1;return 1
 except Exception as e:
  import traceback
  errors.append(traceback.format_exc());return 0
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
try:
 assert d.nf_native_scene_sink(receive,None)
 data=rom.read_bytes();buf=C.create_string_buffer(data)
 assert d.nf_live_visibility_enable(buf,len(data),16*1024*1024)
 d.nf_live_surface_audit_enable(1)
 assert d.nf_native_scene_sink(receive,None)
 for frame in range(850):d.nf_frame(1|(32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
 assert not errors,errors
 object_region_stats=(C.c_uint32*7)();d.nf_live_object_region_stats(object_region_stats)
 assert object_region_stats[0]>0 and object_region_stats[2]==0
 assert all(x['origin'][6]==0x03002364 for x in missing_wall_trace)
 rejected=C.c_void_p(123);rejected_size=C.c_size_t(456)
 assert not d.nf_live_completed_wall_candidate(*earlier_identity,50331840,139937176,C.byref(rejected),C.byref(rejected_size)) and rejected.value==123 and rejected_size.value==456
 counts['candidate_eviction_atomic']+=1
 expired_pose=C.create_string_buffer(b'P'*104);expired_result=C.create_string_buffer(b'R'*result_bytes)
 assert not d.nf_live_completed_visibility_pose(*earlier_identity,expired_pose) and expired_pose.raw==b'P'*104+b'\0'
 assert not d.nf_live_completed_visibility_at(*earlier_identity,expired_pose,expired_result) and expired_result.raw==b'R'*result_bytes+b'\0'
 counts['pose_eviction_atomic']+=1
 rejected_plan=C.create_string_buffer(b'K'*2068,2068)
 assert not d.nf_live_completed_wall_plan(*earlier_identity,expired_pose,0,rejected_plan) and rejected_plan.raw==b'K'*2068
 assert all(hashlib.sha256(buf.raw).hexdigest()==digest for buf,digest in kept_plans)
 counts['wall_plan_eviction_atomic']+=1


 assert kept_candidate and hashlib.sha256(C.string_at(kept_candidate[0],kept_candidate[1])).hexdigest()==kept_candidate[2]
 assert d.nf_state(str(root/'driving.state').encode(),0)
 bad=(C.c_uint64*5)(*([123]*5));assert not d.nf_live_completed_texture_provenance(*last,bad) and list(bad)==[123]*5
 counts['reset_atomic']+=1
 assert not d.nf_live_completed_visibility_pose(*last[:4],expired_pose) and expired_pose.raw==b'P'*104+b'\0'
 assert not d.nf_live_completed_visibility_at(*last[:4],expired_pose,expired_result) and expired_result.raw==b'R'*result_bytes+b'\0'
 counts['pose_reset_atomic']+=1
 assert not d.nf_live_completed_wall_plan(*last[:4],expired_pose,0,rejected_plan) and rejected_plan.raw==b'K'*2068
 assert all(hashlib.sha256(buf.raw).hexdigest()==digest for buf,digest in kept_plans)
 counts['wall_plan_reset_atomic']+=1


 assert not d.nf_live_completed_wall_candidate(*earlier_identity,50331840,139937176,C.byref(rejected),C.byref(rejected_size)) and rejected.value==123 and rejected_size.value==456
 assert hashlib.sha256(C.string_at(kept_candidate[0],kept_candidate[1])).hexdigest()==kept_candidate[2]
 d.nf_surface_free(kept_candidate[0]);kept_candidate=None
 counts['candidate_reset_copy_survival']+=1
finally:
 d.nf_close()
 assert d.nf_snapshot_destroy(ordered_store)
assert [v['bounds'] for v in draw_bounds if v['serial']==141 and v['identity'][2]==139937176]==[[2,60,0,158]]
assert len(portal_samples)==17
for sample in portal_samples:
 admitted={g['source'] for g in sample['gates'] if not g['flags']&4}
 assert admitted <= {139937176}
 if sample['alpha']<=.75:assert not admitted
 if sample['alpha']>=.9:assert admitted=={139937176}
 assert {v['source'] for v in sample['draw_plans']}==admitted
 for draw in sample['draw_plans']:
  assert draw['pass_id']==0 and draw['width']==128 and draw['height']==64
  assert draw['texture']==candidate_sources[0]['texture'] and draw['flags']==4352

# Original audit read the query-time RAM matrix; compare only rejection, not its stale auxiliary flags.
assert [(g['source'],g['flags']&4) for g in portal_samples[0]['gates']]==[(g['source'],g['edge_flags']&4) for g in candidate_gates]
assert len(pose_relations)==206
assert all(all(row[k] for k in ('query_transpose','query_zero_translation','base_translation','camera_translation')) and row['rotation_error']<0.00007 for row in pose_relations)
report=dict(result='PASS',sampled_queue_transitions=sampled_queue_transitions,region_invocation_samples=region_invocation_samples,invocation_palette_comparisons=invocation_palette_comparisons,invocation_transitions=invocation_transitions,dispatch_samples=dispatch_samples,object_region_stats=list(object_region_stats),missing_wall_trace=missing_wall_trace,draw_bounds=draw_bounds,portal_samples=portal_samples,pose_relations=pose_relations,pose_samples=pose_samples,counts=dict(counts),updates=updates,animation_samples=animation_samples,candidate_sources=candidate_sources,candidate_palettes=candidate_palettes,candidate_extractions=candidate_extractions,enumeration=enumeration,candidate_gates=candidate_gates,scope='Owned captured source provenance and wall frame-selection reconstruction; source refresh bounds are scene intervals, not exact animation update instants. No independent animation scheduling or visual smoothness proof.')
(root/'camera'/('texture-provenance-wide-tests.json' if wide else 'texture-provenance-tests.json')).write_text(json.dumps(report,indent=2));print(dict(counts))




















