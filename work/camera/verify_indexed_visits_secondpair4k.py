from owned_indexed_model_visits import install as install_index
install_index()
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
expected=[dict(alpha=a) for a in (1/1024,1/16,3/16,6/16,10/16,13/16,15/16,1023/1024)]
import owned_hud_prefetch_d3d_profile_install_candidate as prefetch_module
from owned_hud_prefetch_d3d_profile_install_candidate import PrefetchSession
original_cdll=C.CDLL
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_source_segmented_draw_candidate import OwnedSourceDraw
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
assert hasattr(prepared.pair, '_indexed_ordinary_endpoints')
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
 origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
import owned_current_consumer_stage_split_install_candidate
import owned_ordered_tail_profile_install_candidate
import owned_present_batch_trace_install_candidate
import owned_native_transaction_worker_install_candidate
import owned_world_stream_linear_backend_install_candidate
import owned_hud_callback_stage_batch_candidate as callback_batch
callback_batch.install()
def run(library,source_library):
 loads=[]
 def load(path,*args,**kwargs):
  if Path(path).name.startswith('owned-d3d-'):
   path=str(Path(path).with_name(library));loads.append(path)
  if library=='owned-d3d-world-stream-linear-transaction-candidate.dll' and Path(path).name.startswith(('owned-gpu-source-','owned-gpu-hud-')):
   path=str(Path(path).with_name(source_library))
  return original_cdll(path,*args,**kwargs)
 C.CDLL=load;session=None;hashes=[]
 try:
  session=PrefetchSession() if library=='owned-d3d-world-stream-linear-transaction-candidate.dll' else NativeSourceSession()
  assert len(loads)==1
  assert Path(session.source._name).name==source_library
  if isinstance(session,PrefetchSession):assert session.prefetch_hud(tuple(frames),1,1)['prefetch_count']==2
  for index,item in enumerate(expected*2):
   alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
   owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
   draw_result=session.draw(owned,1,1,index)
   if getattr(__import__('owned_hud_borrowed_rows_install_candidate'),'metadata_boundaries_installed',False):
    profile=draw_result['borrowed_metadata_calls'];assert [row['call'] for row in profile]==(['source_setup','source_input']+(['hud_discard'] if hasattr(session.consumer.d,'nf_d3d_hud_discard_stats') else [])+(['hud_cycles'] if hasattr(session.consumer.d,'nf_d3d_hud_phase_cycles') else [])+['borrowed_count']) and all(row['begin_ns']<=row['end_ns'] for row in profile)
   if getattr(owned_present_batch_trace_install_candidate,'post_render_boundaries_installed',False):
    row=next(s for s in session.consumer.stage_profile if s['stage']=='ordered_sky_world_hud');profile=row['post_render_profile'];assert list(profile.values())==sorted(profile.values()) and next(iter(profile.values()))>0
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
  if source_library=='owned-gpu-hud-prepared-native-candidate.dll':
   session.source.nf_hud_prepared_rows_used.restype=C.c_uint64;assert session.source.nf_hud_prepared_rows_used()>0
  world_stats=(C.c_uint64*2)();assert session.consumer.d.nf_d3d_world_upload_stats(world_stats)==0
  assert world_stats[1]==0
  if library=='owned-d3d-world-stream-linear-transaction-candidate.dll':assert 0<world_stats[0]<len(hashes)
  reused=None
  if hasattr(session.consumer.d,'nf_d3d_resource_reuse_count'):
   session.consumer.d.nf_d3d_resource_reuse_count.restype=C.c_uint64;reused=session.consumer.d.nf_d3d_resource_reuse_count();assert reused>0
  return dict(metadata_call_names=[row["call"] for row in draw_result.get("borrowed_metadata_calls",[])],hashes=hashes,resource_reuses=reused,world_buffer_creates=world_stats[0],library=loads[0])
 finally:
  if session is not None:
   session.close();assert session.source.nf_owned_gpu_contexts()==0
   owners=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(owners)==1 and list(owners)==[0,0,0]
   if hasattr(session.source,'nf_hud_owner_prepared_bytes'):
    session.source.nf_hud_owner_prepared_bytes.restype=C.c_uint64;assert session.source.nf_hud_owner_prepared_bytes()==0
  C.CDLL=original_cdll
try:
 import owned_native_draw_boundaries_install_candidate
 import owned_hud_borrowed_rows_install_candidate
 from owned_prepared_hud_live_install import install as install_fused
 install_fused()
 baseline=run('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-gpu-hud-prepared-native-candidate.dll')
 from owned_borrowed_metadata_boundaries import install as install_post_render
 install_post_render()
 # Native prepared HUD owner candidate

 candidate=run('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-gpu-hud-prepared-native-candidate.dll')

 assert baseline['hashes']==candidate['hashes']
 out=dict(result='PASS_INDEXED_MODEL_VISITS_FULL4K_PARITY',frames=len(candidate['hashes']),alphas=[x['alpha'] for x in expected],baseline=baseline,candidate=candidate,scope='Same current linear transaction and borrowed HUD renderer; native prepared HUD snapshot/decoder versus original renderer decode,16 complete4K RGBA hashes across8 bounded fractions including near-endpoint interior positions repeated; exact endpoints excluded by original sampler guard. Saved scene pair; no livecadence proof.')
 Path('work/camera/prototype-runs/indexed-model-visits-secondpair4k-20261010.json').write_text(json.dumps(out,indent=2));print(out['result']);print('frames',out['frames'],'resource_reuses',candidate['resource_reuses'])
finally:cached.close();prepared.close();history.close()
















