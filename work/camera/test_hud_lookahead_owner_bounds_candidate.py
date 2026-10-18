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
import struct
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
exec(compile(setup,'actual_saved_scene_setup','exec'))
from owned_native_source_hud_cache_lease_session_candidate import NativeSourceSession
expected=[dict(alpha=i/9) for i in range(1,9)]
import owned_hud_prefetch_d3d_profile_install_candidate as prefetch_module
from owned_hud_prefetch_d3d_profile_install_candidate import PrefetchSession
original_cdll=C.CDLL
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
 origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])

from owned_native_source_segmented_session_candidate import NativeFrameIdentityError
session=PrefetchSession();records=[];peak=0
try:
 endpoints=[]
 for i in range(13):
  value=bytearray(frames[i%2]);h=struct.unpack_from('<6I2Q',value);refresh=h[1]+i
  struct.pack_into('<I',value,4,refresh);struct.pack_into('<Q',value,32,refresh*280896)
  for y in range(160):struct.pack_into('<I',value,40+h[2]+y*34944,refresh)
  endpoints.append(bytes(value))
 for i in range(12):
  generation=1 if i<6 else 2
  result=session.prefetch_hud(tuple(endpoints[i:i+2]),1,generation);assert result['prefetch_count']<=2
  for base,future in session.hud_prefetch:future.result(20)
  stats=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(stats)==1
  peak=max(peak,stats[0]);assert stats[0]<=4 and stats[1]<=4*5591040
  if len(session.hud_snapshots)>=2:session.hud_snapshots.pop(0).close()
  snapshot=session._take_hud(endpoints[i]);assert snapshot._base is endpoints[i];session.hud_snapshots.append(snapshot)
  records.append(dict(index=i,generation=generation,pending=len(session.hud_prefetch),snapshots=len(session.hud_snapshots),owners=list(stats)))
 try:session.prefetch_hud((endpoints[0],),1,1)
 except NativeFrameIdentityError:pass
 else:raise AssertionError('Stale generation accepted')
finally:
 session.close();cached.close();prepared.close();history.close()
stats=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(stats)==1 and list(stats)==[0,0,0]
assert not session.hud_service.thread.is_alive()
out=dict(result='PASS_HUD_LOOKAHEAD_ENDPOINT_OWNER_BOUNDS',transitions=12,peak_native_owners=peak,records=records,stale_generation_rejected=True,final_native_owners=list(stats),scope='Actual native HUD snapshots with saved payloads and synthetic advancing refresh metadata; exact base transfer, two pending/two snapshots, generation retirement and cleanup. No rendered moving scene or live cadence proof.')
Path('work/camera/prototype-runs/hud-lookahead-owner-bounds-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'],peak)
