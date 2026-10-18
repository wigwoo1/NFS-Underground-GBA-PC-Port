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
from owned_sampled_road_sequence import SampledRoadSequence
from corrected_road_pair_candidate import sample as batch_sample,stats as batch_stats
original_sample=SampledRoadSequence.sample
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
def run(library,source_library,road_sample):
 SampledRoadSequence.sample=original_sample
 if road_sample is batch_sample:
  from owned_consumer_stage_boundaries_candidate import install
  install()
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
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
   session.draw(owned,1,1,index)
   if road_sample is batch_sample:
    rows=session.consumer.stage_profile
    backdrop=next(row for row in rows if row['stage']=='backdrop_geometry')
    assert [q['call'] for q in backdrop['native_calls']]==['clear','backdrop_copy','backdrop_draw']
    assert all(q['caller_begin_ns']<=q['native_begin_ns']<=q['native_end_ns']<=q['caller_end_ns'] for q in backdrop['native_calls'])
    assert all(r['elapsed_ns']==r['completed_ns']-r['started_ns'] for r in rows)
    assert all(b['started_ns']==a['completed_ns'] for a,b in zip(rows,rows[1:]))
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
  return dict(hashes=hashes,resource_reuses=reused,world_buffer_creates=world_stats[0],library=loads[0])
 finally:
  if session is not None:
   session.close();assert session.source.nf_owned_gpu_contexts()==0
   owners=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(owners)==1 and list(owners)==[0,0,0]
   if hasattr(session.source,'nf_hud_owner_prepared_bytes'):
    session.source.nf_hud_owner_prepared_bytes.restype=C.c_uint64;assert session.source.nf_hud_owner_prepared_bytes()==0
  C.CDLL=original_cdll
  cached.close();prepared.close();SampledRoadSequence.sample=original_sample
try:
 baseline=run('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-gpu-hud-prepared-native-candidate.dll',original_sample)
 # Native prepared HUD owner candidate

 candidate=run('owned-d3d-world-stream-linear-transaction-candidate.dll','owned-gpu-hud-prepared-native-candidate.dll',batch_sample)

 assert baseline['hashes']==candidate['hashes']

 assert callback_batch.stats['calls']==32
 out=dict(result='PASS_NATIVE_BACKDROP_PROFILE_FULL4K_PARITY',selection=dict(consumer_stage_boundaries=True),frames=len(candidate['hashes']),alphas=[x['alpha'] for x in expected],baseline=baseline,candidate=candidate,scope='Independent baseline/timestamped consumer stage preparations, original road math in both; both current linear transaction/prepared HUD renderer,16 complete4K RGBA hashes across8 bounded fractions including near-endpoint interior positions repeated; exact endpoints excluded by original sampler guard. Saved scene pair; no livecadence proof.')
 Path('work/camera/prototype-runs/native-backdrop-profile-firstpair4k-20261010.json').write_text(json.dumps(out,indent=2));print(out['result']);print('frames',out['frames'],'resource_reuses',candidate['resource_reuses'])
finally:SampledRoadSequence.sample=original_sample;history.close()














