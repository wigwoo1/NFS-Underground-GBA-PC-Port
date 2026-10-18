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
 from owned_progressive_parent_service_candidate import ProgressiveService
 service=ProgressiveService(rom);rows=[]
 try:
  ns=envs[0];service.start(*list(zip(ns['frames'],ns['scenes'])),())
  try:service.take(0)
  except ValueError:pass
  else:raise AssertionError('History-only request exposed a sample')
  terminal=service.finish();assert terminal[2:5]==('complete',0,None)
  assert terminal[5]['history_identity']==tuple(ns['scenes'][1].identity[:2])
  ns=envs[1];service.start(*list(zip(ns['frames'],ns['scenes'])),alphas);received=[]
  for _ in alphas:
   token,p=service.take();received.append(fingerprint(p));service.acknowledge(token)
  terminal=service.finish();assert received==expected[1] and terminal[5]['input_reused']
  service.invalidate();ns=envs[0];service.start(*list(zip(ns['frames'],ns['scenes'])),());service.invalidate()
  service.start(*list(zip(ns['frames'],ns['scenes'])),alphas);received=[]
  for _ in alphas:
   token,p=service.take();received.append(fingerprint(p));service.acknowledge(token)
  service.finish();assert received==expected[0]
 finally:service.close()
 assert service.closed and not service.process.is_alive()
 out=dict(result='PASS_PROGRESSIVE_HISTORY_ONLY',history_only_samples=0,following_samples_exact=6,retained_input_reused=True,reset_samples_exact=6,joined=True,scope='History advancement for intervals without display slots; no required display samples omitted. Not live gameplay or cadence verification.')
 Path('outputs/nfsug-native-renderer/camera-research/progressive-history-only-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
