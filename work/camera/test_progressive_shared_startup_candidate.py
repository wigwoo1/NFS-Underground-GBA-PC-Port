from pathlib import Path
import json,multiprocessing as mp,hashlib
from owned_scene_process_transport import pack
from owned_progressive_process_service_candidate import worker
from owned_progressive_frame_codec_candidate import FrameDecoder
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
def fingerprint(p):return hashlib.sha256(bytes(p[1])+b''.join(p[2:7])+str(p[7]).encode()+p[8]+p[9]+repr(p[10]).encode()).hexdigest()
if __name__=='__main__':
 manifest=json.loads(Path('outputs/nfsug-native-renderer/camera-research/captured-pair-adjacency-20261009.json').read_text());chosen=manifest['exact_shared_source_matches'][0];envs=[]
 setup=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace('from owned_prepared_world_motion import PreparedWorldMotion','from owned_prepared_world_segmented_candidate import PreparedWorldMotion')
 for which in ('first','second'):
  folder=chosen[which]['folder'];source=setup.replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(folder)+')');ns={};exec(source,ns);ns['prepared'].close();ns['history'].close();envs.append(ns)
 alphas=(.01,.2,.4,.6,.8,.99);rom=envs[0]['rom'];history=EndpointRoadPlanner(rom,envs[0]['table']);roads,_=history.plan(envs[0]['scenes'][0].graph);expected=[]
 try:
  for ns in envs:
   prepared=PreparedWorldMotion(*ns['frames'],*ns['scenes'],history,roads,rom);advanced=prepared.take_next_history();history.close();history=advanced;roads=prepared.endpoint_roads[1];samples=PrecomputedSourceWorldSamples(prepared,alphas);hashes=[]
   for a in alphas:
    f,c,m,b,d=samples.sample(a);o,mask,total,diag=samples.source_masks[a];hashes.append(fingerprint((a,f,bytes(c),bytes(m),bytes(b),bytes(o),bytes(mask),total,json.dumps(d,sort_keys=True).encode(),json.dumps(diag,sort_keys=True).encode(),samples.source_cameras)))
   expected.append(hashes);samples.close()
 finally:history.close()
 from owned_progressive_preparation_adapter_candidate import ProgressivePreparationAdapter
 from concurrent.futures import CancelledError
 service=ProgressivePreparationAdapter(rom,shared_output=True);rows=[]
 try:
  evidence=service.warm_start(envs[0]['frames'][0],envs[0]['scenes'][0])
  assert (evidence['epoch'],evidence['refresh'])==tuple(envs[0]['scenes'][0].identity[:2])
  ns=envs[0];future=service.submit(*list(zip(ns['frames'],ns['scenes'])),(),timeout=5);pair=service.take(future)
  assert pair.history_only
  try:pair.sample(.5)
  except ValueError:pass
  else:raise AssertionError('History-only display sample accepted')
  pair.close()
  for i,ns in enumerate(envs[1:],1):
   future=service.submit(*list(zip(ns['frames'],ns['scenes'])),alphas,timeout=5);pair=service.take(future);received=[]
   for a in alphas:
    f,c,m,b,d=pair.sample(a);o,mask,total,diag=pair.source_masks[a]
    p=(a,f,bytes(c),bytes(m),bytes(b),bytes(o),bytes(mask),total,json.dumps(d,sort_keys=True).encode(),json.dumps(diag,sort_keys=True).encode(),pair.source_cameras);received.append(fingerprint(p))
   assert received==expected[i];rows.append(dict(pair=i,samples=6));pair.close()
  # Retire an admitted queued/running request, then start fresh without restarting child.
  future=service.submit(*list(zip(envs[0]['frames'],envs[0]['scenes'])),alphas,timeout=5);service.invalidate()
  try:service.take(future)
  except CancelledError:pass
  else:raise AssertionError('Retired future accepted')
  future=service.submit(*list(zip(envs[0]['frames'],envs[0]['scenes'])),alphas,timeout=5);pair=service.take(future)
  for a in alphas:pair.sample(a)
  pair.close()
 finally:service.close()
 assert not service.thread.is_alive() and not service.service.process.is_alive() and not service.errors,service.errors
 out=dict(result='PASS_PROGRESSIVE_ADAPTER_STARTUP_HISTORY',rows=rows,joined=True,scope='First-ready future adapter and chronological fullscene samples; no live renderer timing integration.')
 Path('outputs/nfsug-native-renderer/camera-research/progressive-shared-startup-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
