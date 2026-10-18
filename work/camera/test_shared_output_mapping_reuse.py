import runpy,json,time
from pathlib import Path
from test_scene_process_transport import digest
from owned_process_preparation_service import ProcessPreparationService
if __name__=='__main__':
 v={};setup=Path('work/camera/test_sky_native_present_callback.py').read_text().split('class Context')[0];exec(compile(setup,'complete-scene-fixture','exec'),v)
 service=ProcessPreparationService(v['rom'],2,shared_output=True);pairs=list(zip(v['frames'],v['scenes']));expected=[digest(v['prepared'].sample(a)) for a in (0,.35,1)];v['prepared'].close();v['history'].close();started=time.perf_counter_ns()
 try:
  ready=service.warm_start(*pairs[0]);assert ready["epoch"]==pairs[0][1].graph.epoch and ready["refresh"]==pairs[0][1].graph.refresh
  for iteration in range(3):
   if iteration:service.invalidate()
   future=service.submit(*pairs,(0,.35,1),timeout=5);samples=service.take(future)
   try:assert [digest(samples.sample(a)) for a in (0,.35,1)]==expected
   finally:samples.close()
  result=dict(startup_readiness=ready,exact_samples=9,child_pid=service.process.pid,generation_resets=2,stage_samples=service.stage_samples,total_elapsed_ms=(time.perf_counter_ns()-started)/1e6,scope='persistent process component; live integration pending')
 finally:service.close()
 assert not service.process.is_alive()
 result['clean_shutdown']=True;Path('outputs/nfsug-native-renderer/camera-research/checkpoints/shared-output-mapping-reuse-20261006/component-tests.json').write_text(json.dumps(result,indent=2));print(result)
