from pathlib import Path
import sys,json,threading,hashlib,time
sys.path.insert(0,str(Path('work/camera').resolve()))
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples
setup=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace('1791308040881565000','1791576492416199100').replace('from owned_prepared_world_motion import PreparedWorldMotion','from owned_prepared_world_segmented_candidate import PreparedWorldMotion')
env={};exec(setup,env);env['prepared'].close();env['history'].close()
alphas=(.01,.2,.4,.6,.8,.99)
def prepare():
 history=EndpointRoadPlanner(env['rom'],env['table']);roads,_=history.plan(env['scenes'][0].graph)
 return history,PreparedWorldMotion(*env['frames'],*env['scenes'],history,roads,env['rom'])
def fingerprint(packet):
 return hashlib.sha256(bytes(packet[1])+b''.join(packet[2:7])+str(packet[7]).encode()+packet[8]+packet[9]+repr(packet[10]).encode()).hexdigest()
import owned_source_presentation_batch_candidate as source_module
import owned_progressive_source_samples_candidate as progressive_module
import owned_precomputed_decode_release_candidate as precomputed_module
optimized=source_module.prepare_source_models
namespace=dict(source_module.__dict__)
exec(Path('work/camera/owned_source_setup_clocks_baseline_candidate.txt').read_text(),namespace)
baseline=namespace['prepare_source_models']
source_module.prepare_source_models=baseline
# Imported helpers must be explicit for the independent baseline.
import owned_precomputed_source_cached_library_candidate as original_samples
original_samples.prepare_source_models=baseline
history,prepared=prepare();batch=PrecomputedSourceWorldSamples(prepared,alphas);expected=[]
for a in alphas:
 frame,camera,models,bounds,detail=batch.sample(a);packed=batch.source_masks[a]
 expected.append(fingerprint((a,frame,bytes(camera),bytes(models),bytes(bounds),bytes(packed[0]),bytes(packed[1]),packed[2],json.dumps(detail,sort_keys=True).encode(),json.dumps(packed[3],sort_keys=True).encode(),batch.source_cameras)))
batch.close();history.close()
source_module.prepare_source_models=optimized
original_samples.prepare_source_models=optimized
progressive_module.prepare_source_models=optimized
first=threading.Event();release=threading.Event();done=threading.Event();packets=[];errors=[];timings=[]
def ready(packet):
 packets.append(packet);timings.append(time.perf_counter_ns())
 if len(packets)==1:
  first.set()
  if not release.wait(15):raise TimeoutError('Test consumer did not release first sample')
def worker():
 history,prepared=prepare();samples=None
 try:samples=ProgressiveSourceWorldSamples(prepared,alphas,on_sample=ready)
 except BaseException as e:errors.append(repr(e))
 finally:
  if samples:samples.close()
  history.close();done.set()
t=threading.Thread(target=worker);t.start()
try:
 assert first.wait(15) and len(packets)==1 and not done.is_set()
 first_hash=fingerprint(packets[0]);assert first_hash==expected[0]
finally:release.set();t.join(15)
assert not t.is_alive() and not errors and done.is_set()
assert [p[0] for p in packets]==list(alphas) and [fingerprint(p) for p in packets]==expected
assert fingerprint(packets[0])==first_hash
# Failure leaves already delivered immutable sample usable and closes producer/history.
history,prepared=prepare();delivered=[]
def fail(packet):
 delivered.append(packet)
 if len(delivered)==2:raise RuntimeError('Injected publication failure')
try:
 try:ProgressiveSourceWorldSamples(prepared,alphas,on_sample=fail)
 except RuntimeError as e:assert str(e)=='Injected publication failure'
 else:raise AssertionError('Publication error swallowed')
 assert prepared.history is None and [fingerprint(p) for p in delivered]==expected[:2]
finally:history.close()
# Explicit tracing still retains all ordered setup stages and exact samples.
history,prepared=prepare();traced_packets=[]
try:
 traced=ProgressiveSourceWorldSamples(prepared,alphas,trace=True,on_sample=traced_packets.append)
 assert [fingerprint(p) for p in traced_packets]==expected
 stages=traced.source_setup_stages
 assert [x['name'] for x in stages]==['endpoint_sampling_and_decode','model_source_ownership','scenery_source_rows','rigid_model_anchors','source_classifiers']
 assert all(x['completed_ns']>=x['started_ns'] and x['thread_cycles']>=0 for x in stages)
 assert all(a['completed_ns']==b['started_ns'] for a,b in zip(stages,stages[1:]))
 traced.close()
finally:history.close()
out=dict(trace_enabled_exact_samples=True,trace_setup_stages=5,independent_preserved_baseline=True,result='PASS_PROGRESSIVE_COMPLETE_SAMPLE_PUBLICATION',samples=6,first_sample_before_batch_completion=True,exact_frame_arrays_masks_details=True,immutable_owners_survive_close=True,injected_failure_cleanup=True,scope='Threaded component only; consumer deliberately gates first sample. No process IPC/reset/GPU/live timing integration or smooth60 claim.')
Path('outputs/nfsug-native-renderer/camera-research/source-setup-clock-guard-20261009.json').write_text(json.dumps(out,indent=2));print(out)
