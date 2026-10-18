import json
from pathlib import Path
import owned_source_presentation_batch_candidate as batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_child_road_wrapper_reuse_process_candidate import ProcessPreparationService
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
batch.SourceFaceDeterminants=SourceFaceDeterminants
def fingerprint(owner,alpha):
 v=owner.sample(alpha);m=owner.source_masks[alpha]
 return (bytes(v[0]),*(None if x is None else bytes(x) for x in v[1:4]),v[4],bytes(m[0]),bytes(m[1]),m[2],m[3],owner.source_cameras)
if __name__=='__main__':
 source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')","folder=Path('work/camera/prototype-runs/fullscene-failure-1791566912183939000')")
 ns={};exec(compile(source,'failure_setup','exec'),ns);ns['prepared'].close();ns['history'].close()
 from owned_endpoint_road_planner import EndpointRoadPlanner
 frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
 history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph)
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);alphas=(.2,.4,.6,.8)
 direct=PrecomputedSourceWorldSamples(prepared,alphas);service=ProcessPreparationService(rom,2);received=None
 try:
  received=service.take(service.submit(*list(zip(frames,scenes)),alphas,timeout=5))
  assert all(fingerprint(direct,a)==fingerprint(received,a) for a in alphas)
 finally:
  if received:received.close()
  direct.close();service.close();history.close()
 assert not service.process.is_alive() and service.request_owner.closed and service.shared_owner.closed
 out=dict(result='PASS_FAILED_PAIR_ACTUAL_CHILD_SOURCE_PARITY',alphas=list(alphas),child_pid=service.process.pid,clean_shutdown=True,scope='Actual spawned fixed-types child with asserted existing depth-transition classifier vs direct captured failed-pair reconstruction: exact frame/model/camera/bounds/details/masks and source cameras. Fractional original visibility/fidelity and actual failed-pair4K not verified.')
 Path('work/camera/prototype-runs/child-road-wrapper-failed-pair-20261009.json').write_text(json.dumps(out,indent=2));print(out)
