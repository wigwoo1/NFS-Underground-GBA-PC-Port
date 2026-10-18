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
 ctx=mp.get_context('spawn');parent,child=ctx.Pipe();process=ctx.Process(target=worker,args=(child,rom));process.start();child.close();rows=[]
 try:
  for i,ns in enumerate(envs):
   decoder=FrameDecoder(7);scenes=ns['scenes'];frames=ns['frames'];parent.send((7,pack(frames[0],scenes[0]) if i==0 else None,scenes[0].identity,pack(frames[1],scenes[1]),alphas));received=[]
   while True:
    assert parent.poll(20);message=parent.recv()
    if message[0]=='terminal':break
    _,g,index,p=message;assert g==7 and index==len(received);p=(p[0],decoder.decode(p[1]),*p[2:]);received.append(fingerprint(p));parent.send(('ack',g,index))
   assert message[5]['child_idle_release_enabled'] is True
   assert message[2]=='complete',message
   assert received==expected[i] and message[5]['input_reused']==bool(i) and tuple(message[5]['history_identity'])==scenes[1].identity
   rows.append(dict(pair=chosen[('first','second')[i]],samples=len(received),input_reused=message[5]['input_reused']));decoder.close()
  parent.send(None);process.join(10);assert not process.is_alive() and process.exitcode==0
 finally:
  parent.close()
  if process.is_alive():process.terminate();process.join(5)
 out=dict(result='PASS_CHRONOLOGICAL_PROGRESSIVE_HISTORY',rows=rows,shared_source_sections=chosen['shared_files'],same_pid=process.pid,joined=True,scope='Two chronological captured fullscene intervals; exact samples versus direct sequential history. No live game timing/nativeGPU proof for persistent service.')
 Path('outputs/nfsug-native-renderer/camera-research/idle-release-chronological-process-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
