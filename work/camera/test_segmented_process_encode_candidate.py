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
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected))

import pickle
from owned_source_process_service_candidate import encode_samples as original_encode
from owned_segmented_process_encode_candidate import encode_samples
try:
 contiguous={a:(bytes(v[0]),*v[1:]) for a,v in cached.samples.items()}
 expected_payload=original_encode(contiguous);actual=encode_samples(cached.samples)
 assert actual==expected_payload
 assert pickle.loads(pickle.dumps(actual))==expected_payload
 assert all(type(t) is bytes for t in actual['tails'])
 assert len(actual['samples'])==5
 try:encode_samples(cached.samples,borrow_tails=True)
 except ValueError:pass
 else:raise AssertionError('Borrowed transport accepted')
 out=dict(result='PASS_ACTUAL_SEGMENTED_PROCESS_ENCODE_PARITY',samples=len(actual['samples']),tails=len(actual['tails']),original_bytes=actual['original_bytes'],transferred_bytes=actual['transferred_bytes'],scope='Current captured five precomputed segmented samples encoded without full-frame materialization; exact schema/bytes equal existing contiguous encoder and pickle roundtrip. No spawned child, decoded 4K parity, live timing or scanout claim.')
 Path('work/camera/prototype-runs/segmented-process-encode-parity-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:cached.close();prepared.close();history.close()
