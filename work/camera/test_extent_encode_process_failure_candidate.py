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
from owned_extent_encode_process_service_candidate import ProcessPreparationService
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
 rows=[];checks=[]
 try:
  ready=service.warm_start(frames[0],scenes[0]);assert ready["refresh"]==scenes[0].graph.refresh;checks.append("warm_start")
  for iteration in range(2):
   if iteration:service.invalidate()
   received=service.take(service.submit(*list(zip(frames,scenes)),alphas,timeout=5))
   try:
    assert all(fingerprint(received,a)==expected[a] for a in alphas)
    assert received.endpoint_base_reuses==len(alphas)
    rows.append(dict(iteration=iteration,alphas=list(alphas),exact_source_samples=True))
   finally:received.close();assert not received.samples and not received.source_masks and not received.source_cameras
  service.invalidate()
  try:service.take(service.submit(*list(zip(frames,scenes)),(float('nan'),),timeout=5))
  except RuntimeError as error:assert 'Invalid source sample identity' in str(error),str(error);checks.append('invalid_alpha_child_rejected')
  else:raise AssertionError('Malformed alpha accepted')
  service.invalidate()
  recovered=service.take(service.submit(*list(zip(frames,scenes)),alphas,timeout=5))
  try:assert all(fingerprint(recovered,a)==expected[a] for a in alphas);checks.append('recovered_after_failure')
  finally:recovered.close()
  service.invalidate()
  empty=service.take(service.submit(*list(zip(frames,scenes)),(),timeout=5));assert empty.history_only and not empty.samples;empty.close();checks.append('history_only')
  service.invalidate()
  future=service.submit(*list(zip(frames,scenes)),alphas,timeout=5);retired=future.result(30);service.invalidate()
  assert not retired.samples and not retired.source_masks and not retired.source_cameras
  from concurrent.futures import CancelledError
  try:service.take(future)
  except CancelledError:checks.append('retired_result_rejected_and_cleared')
  else:raise AssertionError('Retired result delivered')
 finally:direct.close();service.close();history.close()
 assert service.request_owner.closed and service.shutdown_evidence['request_mapping_closed'] is True
 assert service.shared_owner.closed and service.shutdown_evidence['shared_mapping_closed'] is True
 assert not service.process.is_alive()
 assert service.shutdown_evidence['child_exitcode']==0 and not service.shutdown_evidence['forced_termination'] and service.connection.closed and not service.pipeline.thread.is_alive()
 out=dict(result='PASS_SPAWNED_SEGMENTED_FAILURE_LIFECYCLE',checks=checks,shutdown=service.shutdown_evidence,rows=rows,child_pid=service.process.pid,clean_shutdown=True,scope='Actual spawned current segmented child versus direct current thread reconstruction from same captured cold endpoint history; exact frames/arrays/details/masks/cameras, generation reset and close. Parent retains segmented immutable bytes copied before acknowledgement. No live timing, native4K or scanout claim.')
 Path('work/camera/prototype-runs/extent-encode-process-failure-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
