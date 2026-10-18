import runpy,sys,json,os
os.environ['NF_SHARED_DEDUP_BYTES']='1'
from pathlib import Path
from owned_source_process_service_candidate import ProcessPreparationService
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner

def fingerprint(owner,a):
 v=owner.sample(a);m=owner.source_masks[a]
 return (v[0],*(bytes(x) for x in v[1:4]),bytes(m[0]),bytes(m[1]),m[2],m[3],owner.source_cameras)
if __name__=='__main__':
 v=runpy.run_path('work/camera/capture_fullscene_sample_oracle.py');history=EndpointRoadPlanner(v['rom'],v['table']);roads,_=history.plan(v['scenes'][0].graph)
 prepared=PreparedWorldMotion(*v['frames'],*v['scenes'],history,roads,v['rom']);alphas=(.1,.35,.9);direct=PrecomputedSourceWorldSamples(prepared,alphas);service=ProcessPreparationService(v['rom'],2,shared_output=True)
 try:
  expected={a:fingerprint(direct,a) for a in alphas};direct.close()
  ready=service.warm_start(v['frames'][0],v['scenes'][0]);assert ready['refresh']==v['scenes'][0].graph.refresh
  for iteration in range(2):
   if iteration:service.invalidate()
   future=service.submit(*list(zip(v['frames'],v['scenes'])),alphas,timeout=5);received=service.take(future)
   try:assert all(fingerprint(received,a)==expected[a] for a in alphas)
   finally:received.close();assert not received.samples and not received.source_masks and not received.source_cameras
  service.invalidate()
  future=service.submit(*list(zip(v['frames'],v['scenes'])),(),timeout=5);empty=service.take(future)
  assert empty.history_only and not empty.samples and not empty.source_masks and not empty.source_cameras;empty.close()
  service.invalidate()
  future=service.submit(*list(zip(v['frames'],v['scenes'])),alphas,timeout=5);retired=future.result(timeout=30)
  service.invalidate();assert not retired.samples and not retired.source_masks and not retired.source_cameras
  from concurrent.futures import CancelledError
  try:service.take(future)
  except CancelledError:pass
  else:raise AssertionError('Retired source result delivered')
 finally:direct.close();service.close();history.close()
 assert service.stage_samples and all(x['child_stages']['shared_write']['deduplication_enabled'] for x in service.stage_samples)
 assert not service.process.is_alive() and service.shared_owner.closed
 assert service.shutdown_evidence['shared_mapping_closed'] and not service.shutdown_evidence['forced_termination']
 cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-shared-dedup-lifecycle-20261007');cp.mkdir(exist_ok=True)
 (cp/'result.json').write_text(json.dumps(dict(result='PASS',startup_warm=True,history_only_empty=True,retired_result_cleared=True,retired_take_rejected=True,exact_source_samples=6,generation_resets=4,clean_shutdown=True,scope='Actual captured scene source-anchored frame/camera/models/bounds/mask/cameras bytes equal acrossprocess; no live cadence or shared-memory certification.'),indent=2))
 for name in ('owned_source_process_service_candidate.py','test_source_shared_dedup_lifecycle.py'):(cp/name).write_bytes(Path('work/camera',name).read_bytes())
 print('PASS source startup/history-only/retirement and six exact source samples')
