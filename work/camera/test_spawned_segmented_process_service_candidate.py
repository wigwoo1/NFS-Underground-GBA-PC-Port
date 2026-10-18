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


import runpy,hashlib
from owned_segmented_process_service_candidate import ProcessPreparationService
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_prepared_world_segmented_candidate import PreparedWorldMotion

def fingerprint(owner,alpha):
 v=owner.sample(alpha);m=owner.source_masks[alpha]
 return (bytes(v[0]),*(None if x is None else bytes(x) for x in v[1:4]),v[4],bytes(m[0]),bytes(m[1]),m[2],m[3],owner.source_cameras)
if __name__=='__main__':
 report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
 source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
 ns={};exec(compile(source,'captured_process_setup','exec'),ns);ns['prepared'].close();ns['history'].close()
 frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
 from owned_endpoint_road_planner import EndpointRoadPlanner
 history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 alphas=(.1,.35,.9);direct=PrecomputedSourceWorldSamples(prepared,alphas);expected={a:fingerprint(direct,a) for a in alphas};service=ProcessPreparationService(rom,2)
 rows=[]
 try:
  for iteration in range(2):
   if iteration:service.invalidate()
   received=service.take(service.submit(*list(zip(frames,scenes)),alphas,timeout=5))
   try:
    assert all(fingerprint(received,a)==expected[a] for a in alphas)
    rows.append(dict(iteration=iteration,alphas=list(alphas),exact_source_samples=True))
   finally:received.close();assert not received.samples and not received.source_masks and not received.source_cameras
 finally:direct.close();service.close();history.close()
 assert not service.process.is_alive()
 out=dict(result='PASS_SPAWNED_SEGMENTED_SOURCE_SERVICE',rows=rows,child_pid=service.process.pid,clean_shutdown=True,scope='Actual spawned current segmented child versus direct current thread reconstruction from same captured cold endpoint history; exact frames/arrays/details/masks/cameras, generation reset and close. Parent decoder materializes contiguous frames. No live timing, native4K or scanout claim.')
 Path('work/camera/prototype-runs/spawned-segmented-process-parity-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
