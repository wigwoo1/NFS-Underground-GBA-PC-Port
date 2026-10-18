import owned_scenery_thread_library_install_candidate
import owned_endpoint_road_planner as road_planner
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
road_planner.endpoint_road_span_candidates=endpoint_road_span_candidates
import owned_viewport_bounds_fixed_types_install_candidate
import owned_visibility_thread_library_install_candidate
import owned_segmented_display_placement_install_candidate
import owned_hud_cache_lease_worker_install_candidate
import owned_renderer_dispatch_trace_install_candidate
import owned_present_stage_trace_install_candidate
import owned_renderer_fixed_types_install_candidate
import owned_hud_prefetch_d3d_profile_install_candidate
import owned_packet_profile_install_candidate
import owned_d3d_call_profile_install_candidate
import owned_ordered_render_tail_install_candidate
import owned_source_packet_phase_profile_install_candidate
"""Actual saved fullscene pixels with unchanged and resource-reuse transaction backends."""
import sys,json,ctypes as C,hashlib
from pathlib import Path
import numpy as np
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
exec(compile(setup,'actual_saved_scene_setup','exec'))
from owned_native_source_hud_cache_lease_session_candidate import NativeSourceSession
expected=[dict(alpha=i/9) for i in range(1,9)]
import owned_hud_prefetch_d3d_profile_install_candidate as prefetch_module
from owned_hud_prefetch_d3d_profile_install_candidate import PrefetchSession
original_cdll=C.CDLL
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_source_segmented_draw_candidate import OwnedSourceDraw
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
 origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
def run(library,source_library):
 loads=[]
 def load(path,*args,**kwargs):
  if Path(path).name.startswith('owned-d3d-'):
   path=str(Path(path).with_name(library));loads.append(path)
  if library=='owned-d3d-world-stream-linear-transaction-candidate.dll' and Path(path).name.startswith(('owned-gpu-source-','owned-gpu-hud-')):
   path=str(Path(path).with_name(source_library))
  return original_cdll(path,*args,**kwargs)
 C.CDLL=load;session=None;hashes=[];pixel_rows=[];pixel_transitions=[];pixel_previous=None
 try:
  session=PrefetchSession() if library=='owned-d3d-world-stream-linear-transaction-candidate.dll' else NativeSourceSession()
  assert len(loads)==1
  assert Path(session.source._name).name==source_library
  if isinstance(session,PrefetchSession):assert session.prefetch_hud(tuple(frames),1,1)['prefetch_count']==2
  for index,item in enumerate(expected*2):
   alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
   owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
   session.draw(owned,1,1,index)
   if library=='owned-d3d-world-stream-linear-transaction-candidate.dll':
    stamps=(C.c_uint64*4)();assert session.source.nf_source_setup_ticks(stamps)==1
    assert list(stamps)==sorted(stamps) and stamps[0]>0
   if library=='owned-d3d-world-stream-linear-transaction-candidate.dll':
    session.source.nf_hud_borrowed_input_count.restype=C.c_uint64
    assert session.source.nf_hud_borrowed_input_count()>0
    input_stamps=(C.c_uint64*4)();assert session.source.nf_source_input_ticks(input_stamps)==1
    assert all(input_stamps) and list(input_stamps)==sorted(input_stamps)
   if source_library=='owned-gpu-source-sky-detail-candidate.dll':
    q=(C.c_uint64*16)();fn=session.source.nf_sky_packet_detail;fn.argtypes=[C.c_void_p,C.c_size_t];assert fn(q,C.sizeof(q))==0 and any(q[:4]) and any(q[8:12])
   rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
   hashes.append(hashlib.sha256(rgba.raw).hexdigest())
   from owned_sky_color import sky_rgba
   import struct
   raw_frame=bytes(frame);magic,refresh,gn,hn,bn=struct.unpack_from('<5I',raw_frame)
   assert magic in (0x3246474e,0x3346474e);header=40 if magic==0x3346474e else 20
   palettes=b''.join(raw_frame[header+gn+y*34944+128+32768:header+gn+y*34944+128+32768+512] for y in range(160))
   sky=asset.sample_continuous(*boundaries,alpha)
   reference=np.frombuffer(sky_rgba(sky,palettes),np.uint8).reshape(-1,4)
   ids=np.arange(15136);ys,xs=np.divmod(10560+ids,240)
   px=(300+(xs+.5)*13.5).astype(int);py=((ys+.5)*13.5).astype(int)
   actual=np.frombuffer(rgba.raw,np.uint8).reshape(2160,3840,4)[py,px,:3].copy()
   matched=(np.max(np.abs(actual.astype(np.int16)-reference[:,:3].astype(np.int16)),axis=1)<=1)&(reference[:,3]>127)
   pixel_rows.append(dict(alpha=alpha,matching_centers=int(matched.sum())));final_refs.append((reference[:,:3].copy(),actual.copy()))
   if pixel_previous is not None:
    old_actual,old_reference,old_matched=pixel_previous
    robust=(np.max(np.abs(reference[:,:3].astype(np.int16)-old_reference.astype(np.int16)),axis=1)>2)&matched&old_matched
    changed=np.any(actual!=old_actual,axis=1)
    pixel_transitions.append(dict(alpha=alpha,robust_changes=int(robust.sum()),missing=int((robust&~changed).sum())))
   pixel_previous=(actual,reference[:,:3].copy(),matched.copy())
  world_stats=(C.c_uint64*2)();assert session.consumer.d.nf_d3d_world_upload_stats(world_stats)==0
  assert world_stats[1]==0
  if library=='owned-d3d-world-stream-linear-transaction-candidate.dll':assert 0<world_stats[0]<len(hashes)
  reused=None
  if hasattr(session.consumer.d,'nf_d3d_resource_reuse_count'):
   session.consumer.d.nf_d3d_resource_reuse_count.restype=C.c_uint64;reused=session.consumer.d.nf_d3d_resource_reuse_count();assert reused>0
  return dict(pixel_rows=pixel_rows,pixel_transitions=pixel_transitions,hashes=hashes,resource_reuses=reused,world_buffer_creates=world_stats[0],library=loads[0])
 finally:
  if session is not None:
   session.close();assert session.source.nf_owned_gpu_contexts()==0
   owners=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(owners)==1 and list(owners)==[0,0,0]
  C.CDLL=original_cdll

import owned_ordered_render_tail_install_candidate as tm
captures=[];final_refs=[]
def capture(self,s,vertices,nv,offsets,ids,states,nd):
 d=self.d;P=C.c_void_p
 assert d.nf_d3d_source_sky_pan_batch(C.cast(s.nf_source_sky_info,P),C.cast(s.nf_source_sky_copy,P))==0
 planes=[];s.nf_source_sky_copy.argtypes=[C.c_uint,P,C.c_size_t]
 for slot in (0,1):
  q=C.create_string_buffer(153600);assert s.nf_source_sky_copy(slot,q,len(q))==0;planes.append(np.frombuffer(q.raw,np.uint8).reshape(160,240,4).copy())
 q=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(q,len(q))==0
 captures.append((planes,np.frombuffer(q.raw,np.uint8).reshape(2160,3840,4).copy()))
 d.nf_d3d_world_batch.argtypes=[P,C.c_uint,C.c_size_t,P,C.c_size_t,P,C.c_size_t,P,C.c_uint,C.c_size_t]
 assert d.nf_d3d_world_batch(vertices.ctypes.data,nv,vertices.nbytes,offsets,(nd+1)*4,ids,nd*4,states,nd,nd*72)==0
 assert d.nf_d3d_source_hud_batch(C.cast(s.nf_source_hud_planes_info,P),C.cast(s.nf_source_hud_plane_copy,P),C.cast(s.nf_source_hud_batches_count,P),C.cast(s.nf_source_hud_batches_copy,P))==0
 self.ordered_tail_completed=True
old=tm.ordered_tail.__code__;tm.ordered_tail.__globals__.update(np=np,captures=captures);tm.ordered_tail.__code__=capture.__code__
try:
 baseline=run('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-gpu-hud-borrowed-rows-candidate.dll')
 prior=json.loads(Path('work/camera/prototype-runs/current-fullscene-sky-center-motion-diagnostic-20261010.json').read_text());assert baseline['hashes']==prior['hashes'];assert len(captures)==16
 ids=np.arange(15136);ys,xs=np.divmod(10560+ids,240);px=(300+(xs+.5)*13.5).astype(int);py=((ys+.5)*13.5).astype(int);rows=[]
 for i,(planes,stage) in enumerate(captures):
  alpha=expected[i%8]['alpha'];sky=asset.sample_continuous(*boundaries,alpha)
  lo=planes[0][ys,xs,:3].astype(float);hi=planes[1][ys,xs,:3].astype(float);ref=lo+(hi-lo)*sky.weight
  err=np.max(np.abs(stage[py,px,:3].astype(float)-ref),axis=1)
  rows.append(dict(alpha=alpha,matching_stage_centers=int((err<=2).sum()),max_error=float(err.max()),opaque_lower=int((planes[0][ys,xs,3]>127).sum()),opaque_upper=int((planes[1][ys,xs,3]>127).sum()),palette_stage_matching=int((np.max(np.abs(stage[py,px,:3].astype(np.int16)-final_refs[i][0].astype(np.int16)),axis=1)<=1).sum()),centers_changed_after_sky=int(np.any(stage[py,px,:3]!=final_refs[i][1],axis=1).sum())))
 assert all(x['matching_stage_centers']==15136 and x['palette_stage_matching']==15136 for x in rows)
 transitions=[]
 for i in range(1,len(captures)):
  if i==8:continue
  old_stage=captures[i-1][1][py,px,:3];new_stage=captures[i][1][py,px,:3]
  old_final=final_refs[i-1][1];new_final=final_refs[i][1]
  preserved=np.all(old_stage==old_final,axis=1)&np.all(new_stage==new_final,axis=1)
  robust=np.max(np.abs(final_refs[i][0].astype(np.int16)-final_refs[i-1][0].astype(np.int16)),axis=1)>2
  selected=preserved&robust;changed=np.any(new_final!=old_final,axis=1)
  transitions.append(dict(index=i,preserved_centers=int(preserved.sum()),robust_visible_changes=int(selected.sum()),missing=int((selected&~changed).sum())))
 assert sum(x['robust_visible_changes'] for x in transitions)>0 and all(x['missing']==0 for x in transitions)
 out=dict(transitions=transitions,result='PASS_CORRECTED_PALETTE_SKY_STAGE_AND_VISIBLE_CENTER_MOTION',final_full4k_hashes_unchanged=True,rows=rows,scope='Saved fullscene sky stage cached input oracle; no live cadence or scanout certification.')
 Path('work/camera/prototype-runs/current-sky-stage-input-reference-20261010.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
finally:
 tm.ordered_tail.__code__=old;cached.close();prepared.close();history.close()


