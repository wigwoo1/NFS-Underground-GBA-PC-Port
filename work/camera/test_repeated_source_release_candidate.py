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

mode=sys.argv[2];assert mode in ('private','transactional')
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
exec(compile(setup,'captured_private_setup','exec'))
import struct,hashlib
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_source_segmented_draw_candidate import OwnedSourceDraw
from owned_native_source_segmented_release_worker_candidate import NativeSourceWorker
if mode=='transactional':
 reference_frames=[]
 for frame in frames:
  refresh=struct.unpack_from('<I',frame,4)[0]
  reference=(Path('work/camera/prototype-runs/prepared-reference-pair-20261009')/(str(refresh)+'.transactional.frame.bin')).read_bytes()
  assert frame==reference
  reference_frames.append(reference)
 frames=reference_frames
expected=[dict(alpha=0.001)]+expected+[dict(alpha=0.999)]
import gc,tracemalloc,collections,types,time
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_precomputed_source_cached_library_candidate import projection_table_owner,source_library_owner
projection_table_owner();source_library_owner()

import time
rows=[];closed_refs=[];baseline_count=len(gc.get_objects());tracemalloc.start(3)
for index in range(12):
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);closed_refs.append(weakref.ref(prepared));closed_refs.append(weakref.ref(prepared.pair))
 alpha=.1+index*.06;begun=time.perf_counter_ns();cached=PrecomputedSourceWorldSamples(prepared,(alpha,));elapsed=time.perf_counter_ns()-begun
 frame_bytes=cached.bytes;cached.close();prepared.close();del cached,prepared
 current,peak=tracemalloc.get_traced_memory();rows.append(dict(index=index,alpha=alpha,elapsed_ns=elapsed,sample_owned_bytes=frame_bytes,current_bytes=current,peak_bytes=peak,tracked=len(gc.get_objects()),closed_scene_owners_alive=sum(ref() is not None for ref in closed_refs)))
assert all(ref() is None for ref in closed_refs)
history.close();del history
collected=gc.collect();current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
out=dict(result='PASS_REPEATED_CAPTURED_SOURCE_RELEASE',precompute_class=PrecomputedSourceWorldSamples.__module__,baseline_tracked=baseline_count,rows=rows,final_tracked=len(gc.get_objects()),post_collection_bytes=current,peak_bytes=peak,offline_collected=collected,closed_owner_weakrefs=len(closed_refs),scope='12 preparations of one captured endpoint pair with changing sampled alpha .1 through .76; one persistent owned endpoint history reused and closed after all intervals. Actual live precompute class and segmented world path. Offline tracemalloc/GC inventories perturb costs; not 12 different source scenes, live timing, fidelity or exclusive GC cause.')
Path('work/camera/prototype-runs/repeated-source-release-20261009.json').write_text(json.dumps(out,indent=2));print(out['result']);print([(x['index'],x['tracked'],x['current_bytes'],x['closed_scene_owners_alive']) for x in rows]);print('POST',current,out['final_tracked'],collected)
