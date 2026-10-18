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
baseline_ids={id(x) for x in gc.get_objects()}
tracemalloc.start(5);baseline=tracemalloc.take_snapshot()
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected))

peak=tracemalloc.get_traced_memory();after=tracemalloc.take_snapshot();objects=gc.get_objects();counts=collections.Counter();watched=[]
for obj in objects:
 if id(obj) in baseline_ids:continue
 typ=type(obj);counts[typ.__module__+'.'+typ.__qualname__]+=1
 if isinstance(obj,(types.FunctionType,C.Array,C._CFuncPtr,type)) and len(watched)<4096:
  try:
   label=typ.__module__+'.'+typ.__qualname__
   if isinstance(obj,type):label+=':'+obj.__module__+'.'+obj.__qualname__
   watched.append((label,weakref.ref(obj)))
  except TypeError:pass
del obj,objects
cached.close();prepared.close();history.close();del cached,prepared
before_collect=collections.Counter(name for name,ref in watched if ref() is not None)
# Offline replay only: collection identifies unreachable cycles; never applied to live game.
collected=gc.collect()
after_collect=collections.Counter(name for name,ref in watched if ref() is not None)
rows=[]
for entry in after.compare_to(baseline,'traceback')[:30]:rows.append(dict(bytes=entry.size_diff,count=entry.count_diff,traceback=[str(x) for x in entry.traceback]))
tracemalloc.stop()
out=dict(precompute_class=PrecomputedSourceWorldSamples.__module__,result='OFFLINE_SOURCE_ALLOCATION_CENSUS',peak_bytes=peak[1],current_bytes_at_precompute=peak[0],new_tracked_types=counts.most_common(30),weakrefs_count=len(watched),alive_after_close=before_collect.most_common(30),alive_after_offline_collection=after_collect.most_common(30),collected=collected,allocation_sites=rows,scope='One actual captured source interval precomputed with existing ownership chain, five samples; offline tracemalloc and one explicit post-close collection only. Weak refs bounded4096, imports/caches contribute. No live timing or exclusive GC cause claim.')
Path('work/camera/prototype-runs/source-interval-actual-allocation-census-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:out[k] for k in ['peak_bytes','weakrefs_count','alive_after_close','alive_after_offline_collection','collected']},indent=2))
