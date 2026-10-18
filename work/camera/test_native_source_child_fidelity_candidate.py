"""Compare actual spawned source preparation with independent direct history."""
import sys,json,runpy
from pathlib import Path

def main():
 sys.argv=[sys.argv[0],sys.argv[1]]
 v=runpy.run_path('work/camera/test_native_source_process_serialization_candidate.py')
 from owned_endpoint_road_planner import EndpointRoadPlanner
 from owned_prepared_world_motion import PreparedWorldMotion
 from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
 from owned_native_source_process_preparation_candidate import ProcessPreparationService
 from test_scene_process_transport import digest
 frames,scenes,rom=v['frames'],v['scenes'],v['rom']
 alphas=tuple(x['alpha'] for x in v['expected'])
 history=EndpointRoadPlanner(rom,v['table']);service=None;direct=None;actual=None
 checks=[]
 try:
  roads,_=history.plan(scenes[0].graph)
  prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
  direct=PrecomputedSourceWorldSamples(prepared,alphas,trace=True)
  service=ProcessPreparationService(rom,2)
  warm=service.warm_start(frames[0],scenes[0])
  actual=service.take(service.submit((frames[0],scenes[0]),(frames[1],scenes[1]),alphas,timeout=30))
  assert actual.source_cameras==direct.source_cameras
  for alpha in alphas:
   assert digest(actual.sample(alpha))==digest(direct.sample(alpha)),alpha
   x=actual.source_masks[alpha];y=direct.source_masks[alpha]
   assert bytes(x[0])==bytes(y[0]) and bytes(x[1])==bytes(y[1]) and x[2:]==y[2:],alpha
   checks.append(dict(alpha=alpha,digest=digest(actual.sample(alpha))))
  actual.close();actual=None
  service.invalidate()
  actual=service.take(service.submit((frames[0],scenes[0]),(frames[1],scenes[1]),alphas,timeout=30))
  for alpha in alphas:
   assert digest(actual.sample(alpha))==digest(direct.sample(alpha)),('reset',alpha)
   x=actual.source_masks[alpha];y=direct.source_masks[alpha]
   assert bytes(x[0])==bytes(y[0]) and bytes(x[1])==bytes(y[1]) and x[2:]==y[2:]
  assert actual.source_cameras==direct.source_cameras
  assert len(service.stage_samples)==2
  assert all(not x['input_reused'] for x in service.stage_samples)
 finally:
  if actual is not None:actual.close()
  if direct is not None:direct.close()
  history.close()
  if service is not None:service.close()
 assert service.shutdown_evidence['child_exitcode']==0
 assert not service.shutdown_evidence['forced_termination']
 result=dict(result='PASS_SPAWNED_NATIVE_SOURCE_FIDELITY',checks=checks,warm_start=warm,generation_reset_exact_samples=len(alphas),shutdown=service.shutdown_evidence,scope='One captured scene pair, independently initialized road histories, actual spawned production candidate service with warm startup and invalidation/reset; full route and cadence remain unverified.')
 Path('work/camera/prototype-runs/native-source-child-fidelity.json').write_text(json.dumps(result,indent=2));print(result['result'])
if __name__=='__main__':main()
