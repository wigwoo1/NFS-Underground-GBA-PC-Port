import runpy,sys,json
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
 prepared=PreparedWorldMotion(*v['frames'],*v['scenes'],history,roads,v['rom']);alphas=(.1,.35,.9);direct=PrecomputedSourceWorldSamples(prepared,alphas);service=ProcessPreparationService(v['rom'],2)
 try:
  expected={a:fingerprint(direct,a) for a in alphas};direct.close()
  for iteration in range(2):
   if iteration:service.invalidate()
   future=service.submit(*list(zip(v['frames'],v['scenes'])),alphas,timeout=5);received=service.take(future)
   try:assert all(fingerprint(received,a)==expected[a] for a in alphas)
   finally:received.close();assert not received.samples and not received.source_masks and not received.source_cameras
 finally:direct.close();service.close();history.close()
 assert not service.process.is_alive()
 cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-process-service-20261007');cp.mkdir(exist_ok=True)
 (cp/'result.json').write_text(json.dumps(dict(result='PASS',exact_source_samples=6,generation_resets=1,clean_shutdown=True,scope='Actual captured scene source-anchored frame/camera/models/bounds/mask/cameras bytes equal acrossprocess; no live cadence or shared-memory certification.'),indent=2))
 for name in ('owned_source_process_service_candidate.py','test_source_process_service.py'):(cp/name).write_bytes(Path('work/camera',name).read_bytes())
 print('PASS six full source samples including masks, generation reset and shutdown')
