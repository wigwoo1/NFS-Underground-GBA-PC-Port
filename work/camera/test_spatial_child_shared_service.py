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
 import os
 os.environ['NFSUG_CHILD_SPATIAL_DECODE_CACHE']='1'
 os.environ['NFSUG_CHILD_VISIBILITY_LIBRARY_REUSE']='0'
 os.environ['NFSUG_ROAD_SINGLE_JOIN']='0'
 os.environ['NFSUG_ROAD_FLAT_JOIN']='1'
 os.environ['NFSUG_LAZY_WALL_TEXTURES']='0'
 os.environ['NFSUG_SINGLE_JOIN_SCENE_PACK']='1'
 os.environ['NFSUG_ENDPOINT_VALIDATION_REUSE']='1'
 os.environ['NFSUG_CHILD_REQUEST_HANDOFF_TRACE']='1'
 os.environ['NFSUG_DIRECT_SHARED_INPUT_DECODE']='1'
 os.environ['NFSUG_CHILD_INPUT_NATIVE_COPY']='0'
 os.environ['NFSUG_SHARED_INPUT_READ_TRACE']='1'
 os.environ['NFSUG_GRAPH_FRAME_MATCH_CACHE']='0'
 os.environ['NFSUG_MODEL_SMALL_BLOCK_BYTES']='0'
 os.environ['NFSUG_NATIVE_SCENE_RANGES']='0'
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
 import owned_progressive_parent_service_candidate as parent
 from owned_scene_single_join_pack_candidate import pack as optimized_pack
 assert parent.pack is optimized_pack
 from owned_progressive_parent_service_candidate import ProgressiveService
 service=ProgressiveService(rom,shared_output=True);rows=[]
 try:
  for i,ns in enumerate(envs):
   service.start(*list(zip(ns['frames'],ns['scenes'])),alphas);received=[]
   for _ in alphas:
    token,p=service.take();received.append(fingerprint(p));service.acknowledge(token)
   assert service.last_start_timing['single_join_pack_selected'] is True
   terminal=service.finish();assert terminal[5]['native_range_memory_stats'] is None and terminal[5]['small_model_block_stats'] is None and terminal[5]['endpoint_validation_reuse_stats']['hits']>0 and terminal[5]['endpoint_validation_retained_entries']==0
   assert received==expected[i] and terminal[5]['input_reused']==bool(i)
   assert terminal[5]['spatial_decode_cache_selected'] is True and 0<terminal[5]['spatial_decode_cache_entries']<=4
   assert terminal[5]['input_read_profile']['direct_shared_decode'] is True
   handoff=terminal[5]['request_handoff_profile'];assert handoff['recv_begin_ns']<=handoff['recv_end_ns']<=terminal[5]['child_started_ns']
   if i:assert handoff['previous_terminal_send_end_ns']<=handoff['previous_idle_cleanup_end_ns']<=handoff['recv_begin_ns']
   rows.append(dict(pair=i,samples=len(received),input_reused=terminal[5]['input_reused'],endpoint_validation_stats=terminal[5]['endpoint_validation_reuse_stats'],retained_entries=terminal[5]['endpoint_validation_retained_entries'],handoff=handoff))
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
 out=dict(result='PASS_SPATIAL_CHILD_SHARED_CHRONOLOGY_RESET',rows=rows,retired_packet_survives=True,stale_ack_rejected=True,fresh_generation_exact=True,joined=True,scope='Bounded parent API with chronological real samples/reset. No live renderer integration or cadence proof.')
 Path('outputs/nfsug-native-renderer/camera-research/checkpoints/spatial-child-20261010/service-parity.json').write_text(json.dumps(out,indent=2));print(out['result'])
