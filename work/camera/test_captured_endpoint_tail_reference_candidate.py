import sys,json
from pathlib import Path
import owned_scenery_thread_library_install_candidate,owned_visibility_thread_library_install_candidate,owned_viewport_bounds_fixed_types_install_candidate
import owned_endpoint_road_planner as planner
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
planner.endpoint_road_span_candidates=endpoint_road_span_candidates
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_endpoint_tail_reference_candidate import encode_samples,resolve_frame,TAG
from owned_segmented_borrowed_tail_encode_candidate import encode_samples as old_encode
from owned_shared_payload import write_payload,read_payload
from owned_shared_blob import SharedBlobOwner
report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(source,'captured_setup','exec'),ns);ns['prepared'].close();ns['history'].close()
frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')];history=planner.EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);samples=PrecomputedSourceWorldSamples(prepared,(.1,.35,.9));owner=SharedBlobOwner(64*1024*1024)
try:
 original=old_encode(samples.samples,borrow_tails=True);reference=encode_samples(samples.samples,tuple(frames));assert reference['referenced_tail_bytes']>0
 a=write_payload(owner.memory,original,1,1);expected=read_payload(a,1,owner.memory)
 b=write_payload(owner.memory,reference,1,2);received=read_payload(b,1,owner.memory);checks=0
 for (alpha,value),(expected_alpha,expected_value) in zip(received['samples'],expected['samples']):
  assert alpha==expected_alpha and value[2:]==expected_value[2:]
  tail=received['tails'][value[1]]
  if isinstance(tail,tuple):frame=resolve_frame(value[0],tail,tuple(frames));assert frame.base in frames;assert bytes(frame)==expected_value[0]+expected['tails'][expected_value[1]]
  else:assert value[0]+tail==expected_value[0]+expected['tails'][expected_value[1]]
  checks+=1
 out=dict(result='PASS_CAPTURED_ENDPOINT_REFERENCE_PARITY',samples=checks,original_shared_bytes=a[3],reference_shared_bytes=b[3],referenced_tail_bytes=reference['referenced_tail_bytes'],scope='Actual captured3intermediate frame/array/detail/shared read parity; source sidecar and spawned/native integration remain required.')
finally:samples.close();history.close();owner.close()
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
