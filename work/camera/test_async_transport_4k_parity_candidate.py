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
import sys,json,ctypes as C,weakref
from pathlib import Path
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0];exec(compile(setup,'captured_setup','exec'))
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_source_segmented_draw_candidate import OwnedSourceDraw
from owned_native_source_segmented_release_worker_candidate import NativeSourceWorker
from owned_native_source_segmented_session_candidate import NativeFrameIdentityError
reference=json.loads(Path('work/camera/prototype-runs/source-segmented-parity-20261008.json').read_text())['samples']
# Pass both actual immutable source frames through the background native transport.
import struct
from owned_handoff_copy_service_candidate import HandoffCopyService
transport=C.CDLL(str(Path('work/camera/owned-handoff-request-authority-candidate.dll').resolve()))
transport.nf_owned_handoff_create_capacity.argtypes=[C.c_uint64,C.c_uint];transport.nf_owned_handoff_create_capacity.restype=C.c_void_p
transport.nf_owned_handoff_pop_token.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p];transport.nf_owned_handoff_pop_token.restype=C.c_void_p
transport.nf_owned_frame_free.argtypes=[C.c_void_p];transport.nf_owned_handoff_destroy.argtypes=[C.c_void_p]
transport_epoch=struct.unpack_from('<Q',frames[0],24)[0];transport_owner=transport.nf_owned_handoff_create_capacity(transport_epoch,2);assert transport_owner
service=HandoffCopyService(transport,transport_owner,2)
try:
 jobs=[service.submit(frame) for frame in frames]
 assert all(job.result(5)['published'] for job in jobs) and service.wait_idle(5)
 transferred=[]
 for frame in frames:
  size=C.c_size_t();generation=C.c_uint64();pointer=transport.nf_owned_handoff_pop_token(transport_owner,C.byref(size),C.byref(generation));assert pointer
  try:
   copied=C.string_at(pointer,size.value);assert copied==frame;transferred.append(copied)
  finally:transport.nf_owned_frame_free(pointer)
 frames=tuple(transferred)
finally:service.close();transport.nf_owned_handoff_destroy(transport_owner)
assert not service.thread.is_alive() and service.pending==0
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected))
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity);origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);worker=NativeSourceWorker();results=[]
try:
 assert worker.prefetch_hud(tuple(frames)).result(20)['prefetch_count']==2
 assert worker.prefetch_hud(tuple(frames),1,2).result(20)['prefetch_count']==2
 try:worker.prefetch_hud(tuple(frames),1,1).result(20)
 except NativeFrameIdentityError:pass
 else:raise AssertionError('Retired prefetch accepted')
 for index,item in enumerate(expected):
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  try:worker.prepare(owned,1,1,index*2).result(20)
  except NativeFrameIdentityError:pass
  else:raise AssertionError('Retired prepare accepted')
  row=worker.prepare(owned,1,2,index*2,True).result(20);assert row['hud_prefetch_taken']>=1;assert len(row['d3d_call_profiles'])==3;assert all(x['caller_begin_ns']<=x['native_begin_ns']<=x['native_end_ns']<=x['caller_end_ns'] for x in row['d3d_call_profiles']);prof=row['bundle_transfer_profile'];assert prof['caller_begin_ns']<=prof['native_begin_ns']<=prof['native_end_ns']<=prof['caller_end_ns'] and prof['native_cycles']>=0;assert row['native_rgb_sha256']==reference[index]['rgb_sha256']
  profile=row['hud_lease_stages'];assert profile['snapshot_begin_ns']<=profile['snapshot_end_ns']<=profile['bind_begin_ns']<=profile['callback_begin_ns']<=profile['callback_end_ns']<=profile['release_end_ns']
  stamps=row['renderer_dispatch'];assert stamps['submitted_ns']<=stamps['started_ns']<=stamps['completed_ns'] and stamps['thread']==worker.thread.ident
  for future in (worker.prefetch_hud(tuple(frames),1,3),worker.prepare(owned,1,2,index*2),worker.present(1,2,index*2+1),worker.abort(1,3,index*2)):
   try:future.result(20)
   except NativeFrameIdentityError:pass
   else:raise AssertionError('Wrong pending identity accepted')
  worker.abort(1,2,index*2).result(20)
  worker.prepare(owned,1,2,index*2+1).result(20);worker.present(1,2,index*2+1).result(20)
  # Verify the selected display consumer actually emitted the new stage record.
  shown=worker.prepare(owned,1,2,index*2+2).result(20);shown=worker.present(1,2,index*2+2).result(20)
  stamps=shown['present_stage_ns'];assert stamps['begin']<=stamps['pumped']<=stamps['presented']<=stamps['queried']
  results.append(dict(alpha=alpha,rgb_sha256=row['native_rgb_sha256']))
 assert row['hud_prefetch_taken']==1,row
finally:worker.close();cached.close();history.close()
assert not worker.thread.is_alive() and worker.error is None
library=C.CDLL(str((Path('work/camera')/'owned-gpu-source-packet-profile-candidate.dll').resolve()))
stats=(C.c_uint64*3)();assert library.nf_hud_owner_stats(stats)==1
assert list(stats)==[0,0,0],list(stats)
assert owned_segmented_display_placement_install_candidate.diagnostic_stats()["raw_total"]==10
out=dict(result='PASS_HUD_CACHE_LEASE_QUEUE_4K_IDENTITY_LIFECYCLE',samples=results,identity_rejections=26,pending_reset_rejected=True,retired_generation_rejected=True,generation_transition_cleanup=True,prepare_abort_present_recovery=True,prefetched_owners_consumed=1,unused_prefetched_owner_closed=True,renderer_thread_joined=True,scope='Two actual source frames passed through bounded background native copying, then five queued3840x2160 images exact with identity/recovery checks. Exercises transport+consumer composition; not live async swap/pause pixel parity or60fps proof.')
Path('work/camera/prototype-runs/async-transport-4k-parity-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])


