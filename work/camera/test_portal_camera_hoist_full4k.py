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
prepared=cached=None
import owned_closed_scene_memory as memory
import owned_portal_camera_hoist_install_candidate as wall_candidate
def reconstruct(enabled):
 wall_candidate.install() if enabled else wall_candidate.restore()
 memory._scene_memory_local.entries=[]
 private_history=history.fork();private_history.assets.clear()
 try:
  inputs=frames
  built=PreparedWorldMotion(*inputs,*scenes,private_history,roads,rom)
  samples=PrecomputedSourceWorldSamples(built,tuple(x['alpha'] for x in expected),trace=True)
  print('PORTAL_CAMERA_HOIST_SELECTED',enabled)
  return built,samples
 finally:private_history.close()
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
 origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
def run(library,source_library,owner_library,authority_library):
 loads=[]
 def load(path,*args,**kwargs):
  if Path(path).name.startswith('owned-d3d-'):
   path=str(Path(path).with_name(library));loads.append(path)
  if library in ('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-d3d-clock-present-transaction-candidate.dll') and Path(path).name.startswith(('owned-gpu-source-','owned-gpu-hud-')):
   path=str(Path(path).with_name(source_library))
  return original_cdll(path,*args,**kwargs)
 C.CDLL=load;session=None;hashes=[]
 owner_d=original_cdll(str((Path(__file__).parent/owner_library).resolve()));authority_d=original_cdll(str((Path(__file__).parent/authority_library).resolve()))
 owner_d.nf_owned_handoff_create_capacity.argtypes=[C.c_uint64,C.c_uint];owner_d.nf_owned_handoff_create_capacity.restype=C.c_void_p;owner_d.nf_owned_handoff_destroy.argtypes=[C.c_void_p]
 owner=owner_d.nf_owned_handoff_create_capacity(1,3);assert owner
 commits=[]
 try:
  session=PrefetchSession() if library in ('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-d3d-clock-present-transaction-candidate.dll') else NativeSourceSession()
  assert len(loads)==1
  assert Path(session.source._name).name==source_library
  if isinstance(session,PrefetchSession):assert session.prefetch_hud(tuple(frames),1,1)['prefetch_count']==2
  for index,item in enumerate(expected*2):
   alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
   owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
   session.prepare(owned,1,1,index)
   native=session.consumer.d.nf_d3d_native_transaction
   native.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_double,C.c_uint64,C.c_void_p,C.c_size_t]
   values=(C.c_uint64*48)()
   older,newer=scenes[0].identity[1],scenes[1].identity[1]
   rc=native(C.cast(authority_d.nf_owned_handoff_draw_wait_commit_sample,C.c_void_p),owner,session.consumer.window,1,1,older,newer,index,alpha,0,values,C.sizeof(values))
   assert rc==1 and list(values[:5])==[1,1,older,newer,index] and values[7]==index+1 and values[46]==1 and values[47]==0
   assert session.pending==(1,1,index);session.pending=None
   commits.append(list(values[:8]))
   if library in ('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-d3d-clock-present-transaction-candidate.dll'):
    stamps=(C.c_uint64*4)();assert session.source.nf_source_setup_ticks(stamps)==1
    assert list(stamps)==sorted(stamps) and stamps[0]>0
   if library in ('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-d3d-clock-present-transaction-candidate.dll'):
    session.source.nf_hud_borrowed_input_count.restype=C.c_uint64
    assert session.source.nf_hud_borrowed_input_count()>0
    input_stamps=(C.c_uint64*4)();assert session.source.nf_source_input_ticks(input_stamps)==1
    assert all(input_stamps) and list(input_stamps)==sorted(input_stamps)
   if source_library=='owned-gpu-source-sky-detail-candidate.dll':
    q=(C.c_uint64*16)();fn=session.source.nf_sky_packet_detail;fn.argtypes=[C.c_void_p,C.c_size_t];assert fn(q,C.sizeof(q))==0 and any(q[:4]) and any(q[8:12])
   rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
   hashes.append(hashlib.sha256(rgba.raw).hexdigest())
  world_stats=(C.c_uint64*2)();assert session.consumer.d.nf_d3d_world_upload_stats(world_stats)==0
  assert world_stats[1]==0
  if library in ('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-d3d-clock-present-transaction-candidate.dll'):assert 0<world_stats[0]<len(hashes)
  reused=None
  if hasattr(session.consumer.d,'nf_d3d_resource_reuse_count'):
   session.consumer.d.nf_d3d_resource_reuse_count.restype=C.c_uint64;reused=session.consumer.d.nf_d3d_resource_reuse_count();assert reused>0
  return dict(owner_library=owner_d._name,authority_library=authority_d._name,native_commits=commits,hashes=hashes,resource_reuses=reused,world_buffer_creates=world_stats[0],library=loads[0])
 finally:
  if session is not None:
   session.close();assert session.source.nf_owned_gpu_contexts()==0
   owners=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(owners)==1 and list(owners)==[0,0,0]
  owner_d.nf_owned_handoff_destroy(owner)
  C.CDLL=original_cdll
try:
 prepared,cached=reconstruct(False)
 baseline=run('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-gpu-hud-borrowed-rows-candidate.dll','owned-handoff-request-authority-candidate.dll','owned-draw-commit-integer-clock-candidate.dll')
 cached.close();prepared.close()
 prepared,cached=reconstruct(True)
 candidate=run('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-gpu-hud-borrowed-rows-candidate.dll','owned-handoff-request-authority-candidate.dll','owned-draw-commit-integer-clock-candidate.dll')
 assert baseline['hashes']==candidate['hashes']
 out=dict(result='PASS_PORTAL_CAMERA_HOIST_FULL4K_PARITY',frames=len(candidate['hashes']),baseline=baseline,candidate=candidate,scope='Two independently reconstructed preparations from same saved sourcepair and forked initial history; exact current linearD3D/borrowedHUD/source/sky/nativecommit.16complete4KRGBA hashes identical, eightalphas repeated. No live cadence, broader scene fidelity or physicalscanout proof.')
 Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/portal-camera-hoist-full4k-parity.json').write_text(json.dumps(out,indent=2));print(out['result']);print('frames',out['frames'])
finally:
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close();wall_candidate.restore()
