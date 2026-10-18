import os,pickle,json,time,statistics
from pathlib import Path
from multiprocessing.shared_memory import SharedMemory
os.environ['NFSUG_PROJECTION_TYPE_COMPONENT']='0'
setup=Path('work/camera/test_projection_array_type_component.py').read_text().split('alphas=(.01,.2,.4,.6,.8,.99)')[0]
exec(compile(setup,'actual-input-decode-setup','exec'))
from owned_scene_process_transport import pack
from owned_direct_shared_input_decode_candidate import decode_private
request=(1,pack(frames[0],scenes[0]),pack(frames[1],scenes[1]),(.01,.2,.4,.6,.8,.99));payload=pickle.dumps(request,protocol=5);memory=SharedMemory(create=True,size=len(payload));timings={False:[],True:[]}
try:
 memory.buf[:]=payload
 for iteration in range(12):
  for selected in ((False,True) if iteration%2==0 else (True,False)):
   started=time.perf_counter_ns();value=decode_private(memory,len(payload)) if selected else pickle.loads(bytes(memory.buf[:len(payload)]));timings[selected].append((time.perf_counter_ns()-started)/1e6);assert value==request
 detached=decode_private(memory,len(payload));memory.buf[:]=bytes(len(payload));assert detached==request
 def check(x):
  if isinstance(x,(tuple,list)):return all(check(y) for y in x)
  if isinstance(x,dict):return all(check(k) and check(v) for k,v in x.items())
  assert type(x) in (bytes,int,float,str,type(None),bool),type(x);return True
 assert check(detached)
 for bad in (0,-1,len(payload)+1,True,1.5):
  try:decode_private(memory,bad)
  except ValueError:pass
  else:raise AssertionError('Bad extent accepted')
 try:decode_private(memory,len(payload))
 except pickle.UnpicklingError:pass
 else:raise AssertionError('Corrupt payload accepted')
finally:memory.close();memory.unlink()
out=dict(result='PASS_DIRECT_SHARED_DECODE_DETACHED_COMPONENT',input_bytes=len(payload),rounds=12,baseline_median_ms=statistics.median(timings[False]),candidate_median_ms=statistics.median(timings[True]),detached_after_overwrite=True,scope='Actual full captured request-sized pickle, exact nested primitive parity and private bytes after shared overwrite; no protocol/worker/live qualification, existing writer lifetime must remain held through synchronous decode.')
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/direct-shared-input-decode-20261010');folder.mkdir(exist_ok=True);(folder/'component.json').write_text(json.dumps(out,indent=2));print(out)
