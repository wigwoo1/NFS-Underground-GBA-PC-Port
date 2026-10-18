import sys,runpy,multiprocessing as mp,hashlib,json,struct
from pathlib import Path
from owned_scene_process_transport import pack,unpack

def digest(sample):
 return hashlib.sha256(sample[0]+b''.join(bytes(x) for x in sample[1:4] if x is not None)+json.dumps(sample[4],sort_keys=True).encode()).hexdigest()
def child(packets,rom,output):
 try:
  from owned_endpoint_road_planner import EndpointRoadPlanner
  from owned_prepared_world_motion import PreparedWorldMotion
  pairs=[unpack(x,rom) for x in packets];table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);history=EndpointRoadPlanner(rom,table)
  roads,_=history.plan(pairs[0][1].graph);prepared=PreparedWorldMotion(pairs[0][0],pairs[1][0],pairs[0][1],pairs[1][1],history,roads,rom)
  try:output.put([digest(prepared.sample(a)) for a in (0,.35,1)])
  finally:prepared.close();history.close()
 except BaseException as e:output.put(dict(error=repr(e)))
if __name__=='__main__':
 v=runpy.run_path('work/camera/test_external_fullscene_transition.py');packets=tuple(pack(f,s) for f,s in zip(v['frames'],v['scenes']));expected=[digest(v['samples'][i]) for i in (0,35,100)]
 context=mp.get_context('spawn');out=context.Queue(1);process=context.Process(target=child,args=(packets,v['rom'],out));process.start()
 try:
  result=out.get(timeout=30);process.join(30);assert process.exitcode==0 and result==expected,result
 finally:
  if process.is_alive():process.terminate();process.join()
  out.close();out.join_thread()
 # Decoder still enforces original clock joins after crossing process boundary.
 bad=list(packets[0]);raw=bytearray(bad[1]);struct.pack_into('<I',raw,8,0);bad[1]=bytes(raw)
 try:unpack(tuple(bad),v['rom'])
 except ValueError:pass
 else:raise AssertionError('Mismatched scene clock accepted')
 result=dict(spawned_process_exact_samples=3,source_identity_rejection=True,packet_bytes=[sum(len(x) for x in p if x is not None) for p in packets],scope='complete scene preparation in separate process; live service integration pending')
 Path('work/camera/prototype-runs/scene-process-transport.json').write_text(json.dumps(result,indent=2));print(result)
