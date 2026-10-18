from pathlib import Path
import os,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json,multiprocessing as mp,hashlib
from owned_scene_process_transport import pack
from owned_progressive_process_service_candidate import worker
from owned_progressive_frame_codec_candidate import FrameDecoder
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
def fingerprint(p):return hashlib.sha256(bytes(p[1])+b''.join(p[2:7])+str(p[7]).encode()+p[8]+p[9]+repr(p[10]).encode()).hexdigest()
if __name__=='__main__':
 os.environ['NFSUG_NARROW_SAMPLE_MODEL_METADATA']='0'
 os.environ['NFSUG_CAMERA_CLIP_TRANSACTION']='1'
 os.environ['NFSUG_NATIVE_PORTAL_PARENT_BATCH']='0'
 os.environ['NFSUG_CORRECTED_ROAD_PAIR']='1'
 os.environ['NFSUG_SCENE_MEMORY_TWO_ENTRY']='1'
 os.environ['NFSUG_ROAD_CONSTRUCTOR_TRACE']='0'
 os.environ['NFSUG_PROGRESSIVE_FINE_TRACE']='1'
 os.environ['NFSUG_MODEL_SMALL_BLOCK_BYTES']='0'
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
 service=ProgressiveService(rom,shared_output=True);rows=[]
 try:
  for i,ns in enumerate(envs):
   service.start(*list(zip(ns['frames'],ns['scenes'])),alphas);received=[]
   for _ in alphas:
    token,p=service.take();received.append(fingerprint(p));service.acknowledge(token)
   terminal=service.finish();assert terminal[5]['native_range_memory_stats'] is None and terminal[5]['road_transaction_stats']['calls']>0
   assert terminal[5]['scene_memory_two_entry_stats']['calls']>0
   counters=terminal[5]['corrected_road_pair_stats'];assert counters['native_calls']>0
   assert received==expected[i] and terminal[5]['input_reused']==bool(i)
   rows.append(dict(scene_memory_two_entry_stats=terminal[5]["scene_memory_two_entry_stats"],pair=i,samples=len(received),input_reused=terminal[5]['input_reused'],road_transaction_stats=terminal[5]['road_transaction_stats'],corrected_road_pair_stats=counters))
  service.invalidate()
  service.start(*list(zip(envs[0]['frames'],envs[0]['scenes'])),alphas)
  oldtoken,oldpacket=service.take();oldhash=fingerprint(oldpacket);service.invalidate()
  assert fingerprint(oldpacket)==oldhash
  try:service.acknowledge(oldtoken)
  except ValueError:pass
  else:raise AssertionError('Retired acknowledgement accepted')
  service.start(*list(zip(envs[0]['frames'],envs[0]['scenes'])),alphas)
  fresh=[]
  for _ in alphas:
   token,p=service.take();fresh.append(fingerprint(p));service.acknowledge(token)
  service.finish();assert fresh==expected[0]
 finally:service.close()
 assert service.closed and not service.process.is_alive()
 out=dict(result='PASS_TWO_ENTRY_SHARED_CHRONOLOGY_RESET',rows=rows,retired_packet_survives=True,stale_ack_rejected=True,fresh_generation_exact=True,joined=True,scope='Bounded parent API with chronological real samples/reset. No live renderer integration or cadence proof.')
 Path('work/camera/prototype-runs/two-entry-shared-service-parity-20261010.json').write_text(json.dumps(out,indent=2));print(out['result'])


