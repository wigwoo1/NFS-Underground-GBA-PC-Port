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
history,prepared=prepare();batch=PrecomputedSourceWorldSamples(prepared,alphas);expected=[]
for a in alphas:
 frame,camera,models,bounds,detail=batch.sample(a);packed=batch.source_masks[a]
 expected.append(fingerprint((a,frame,bytes(camera),bytes(models),bytes(bounds),bytes(packed[0]),bytes(packed[1]),packed[2],json.dumps(detail,sort_keys=True).encode(),json.dumps(packed[3],sort_keys=True).encode(),batch.source_cameras)))
batch.close();history.close()
import owned_portal_traversal as portal_module
from owned_portal_helper_hoist_candidate import traverse as candidate_traverse
portal_module.traverse.__code__=candidate_traverse.__code__
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
out=dict(result='PASS_PROGRESSIVE_COMPLETE_SAMPLE_PUBLICATION',samples=6,first_sample_before_batch_completion=True,exact_frame_arrays_masks_details=True,immutable_owners_survive_close=True,injected_failure_cleanup=True,scope='Threaded component only; consumer deliberately gates first sample. No process IPC/reset/GPU/live timing integration or smooth60 claim.')
Path('outputs/nfsug-native-renderer/camera-research/portal-helper-hoist-source-parity-20261009.json').write_text(json.dumps(out,indent=2));print(out)
