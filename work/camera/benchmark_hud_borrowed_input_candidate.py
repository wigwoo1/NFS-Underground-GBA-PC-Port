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
def run(source_library):
 library="owned-d3d-world-stream-transaction-candidate.dll"
 loads=[];input_ms=[]
 def load(path,*args,**kwargs):
  if Path(path).name.startswith('owned-d3d-'):
   path=str(Path(path).with_name(library));loads.append(path)
  if library=='owned-d3d-world-stream-transaction-candidate.dll' and Path(path).name.startswith('owned-gpu-source-'):
   path=str(Path(path).with_name(source_library))
  return original_cdll(path,*args,**kwargs)
 C.CDLL=load;session=None;hashes=[]
 try:
  session=PrefetchSession() if library=='owned-d3d-world-stream-transaction-candidate.dll' else NativeSourceSession()
  assert len(loads)==1
  if isinstance(session,PrefetchSession):assert session.prefetch_hud(tuple(frames),1,1)['prefetch_count']==2
  initial_stats=(C.c_uint64*3)();assert session.source.nf_hud_input_cache_stats(initial_stats)==1
  for index,item in enumerate(expected*8):
   alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
   owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
   session.draw(owned,1,1,index)
   if library=='owned-d3d-world-stream-transaction-candidate.dll':
    stamps=(C.c_uint64*4)();assert session.source.nf_source_setup_ticks(stamps)==1
    assert list(stamps)==sorted(stamps) and stamps[0]>0
   if library=='owned-d3d-world-stream-transaction-candidate.dll':
    if hasattr(session.source,"nf_hud_borrowed_input_count"):
     session.source.nf_hud_borrowed_input_count.restype=C.c_uint64
     assert session.source.nf_hud_borrowed_input_count()>0
    input_stamps=(C.c_uint64*4)();assert session.source.nf_source_input_ticks(input_stamps)==1
    assert all(input_stamps) and list(input_stamps)==sorted(input_stamps)
    input_ms.append((input_stamps[3]-input_stamps[2])/1e6)
   rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
   hashes.append(hashlib.sha256(rgba.raw).hexdigest())
  world_stats=(C.c_uint64*2)();assert session.consumer.d.nf_d3d_world_upload_stats(world_stats)==0
  assert world_stats[1]==0
  if library=='owned-d3d-world-stream-transaction-candidate.dll':assert 0<world_stats[0]<len(hashes)
  reused=None
  if hasattr(session.consumer.d,'nf_d3d_resource_reuse_count'):
   session.consumer.d.nf_d3d_resource_reuse_count.restype=C.c_uint64;reused=session.consumer.d.nf_d3d_resource_reuse_count();assert reused>0
  stats=(C.c_uint64*3)();assert session.source.nf_hud_input_cache_stats(stats)==1
  return dict(input_cache_copy_ms=input_ms,input_copy_bytes=stats[1]-initial_stats[1],source_library=source_library,hashes=hashes,resource_reuses=reused,world_buffer_creates=world_stats[0],library=loads[0])
 finally:
  if session is not None:
   session.close();assert session.source.nf_owned_gpu_contexts()==0
   owners=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(owners)==1 and list(owners)==[0,0,0]
  C.CDLL=original_cdll
try:
 import statistics
 runs=[]
 for name in ('owned-gpu-source-input-profile-candidate.dll','owned-gpu-hud-borrowed-rows-candidate.dll','owned-gpu-hud-borrowed-rows-candidate.dll','owned-gpu-source-input-profile-candidate.dll'):
  runs.append(run(name))
 assert all(row['hashes']==runs[0]['hashes'] for row in runs)
 baseline=[row for row in runs if 'source-input' in row['source_library']]
 candidate=[row for row in runs if 'borrowed' in row['source_library']]
 assert all(row['input_copy_bytes']>0 for row in baseline)
 assert all(row['input_copy_bytes']==0 for row in candidate)
 medians={name:statistics.median(value for row in group for value in row['input_cache_copy_ms']) for name,group in [('baseline',baseline),('candidate',candidate)]}
 out=dict(result='PASS_MATCHED_HUD_INPUT_COPY_BENCHMARK',runs=runs,median_input_stage_ms=medians,scope='Same segmented saved pair, same D3D backend and prefetch path, four balanced-order sessions with64draws each; exact4K hashes everydraw and nativecopybytecounts. Stageelapsed includes scheduling; onefixture, no fullgame cadence proof.')
 Path('work/camera/prototype-runs/hud-borrowed-matched-benchmark-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'],medians,[row['input_copy_bytes'] for row in runs])
finally:cached.close();prepared.close();history.close()
