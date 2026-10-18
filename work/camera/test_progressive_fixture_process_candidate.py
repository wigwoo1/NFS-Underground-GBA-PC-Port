from pathlib import Path
import multiprocessing as mp,json,hashlib
from owned_progressive_fixture_process_candidate import worker
def fingerprint(packet):
 return hashlib.sha256(bytes(packet[1])+b''.join(packet[2:7])+str(packet[7]).encode()+packet[8]+packet[9]+repr(packet[10]).encode()).hexdigest()
def run(mode,expected):
 ctx=mp.get_context('spawn');parent,child=ctx.Pipe();process=ctx.Process(target=worker,args=(child,'work/camera/prototype-runs/fullscene-failure-1791576492416199100',7,(.01,.2,.4,.6,.8,.99)));process.start();child.close();received=[];terminal=None
 try:
  while True:
   assert parent.poll(20),'Worker response timed out'
   message=parent.recv()
   if message[0]=='terminal':terminal=message;break
   _,generation,index,packet=message;assert generation==7 and index==len(received);received.append(fingerprint(packet));assert received[-1]==expected[index]
   # Child must wait for ack: no second sample or terminal may appear yet.
   assert not parent.poll(.03)
   if mode=='retire':parent.send(('retire',7))
   elif mode=='bad_ack':parent.send(('ack',8,index))
   else:parent.send(('ack',7,index))
  process.join(10);assert not process.is_alive() and process.exitcode==0 and terminal[5]
  assert terminal[2]=={'complete':'complete','retire':'retired','bad_ack':'error'}[mode]
  assert len(received)==(6 if mode=='complete' else 1)
 finally:
  parent.close()
  if process.is_alive():process.terminate();process.join(5)
 return dict(mode=mode,received=len(received),terminal=list(terminal),joined=True)
if __name__=='__main__':
 ns={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),ns)
 rows=[run(mode,ns['expected']) for mode in ('complete','retire','bad_ack')]
 out=dict(result='PASS_SPAWNED_PROGRESSIVE_SOURCE_PROTOCOL',rows=rows,exact_fullscene_samples=True,ack_before_next_sample=True,scope='Saved-fixture spawned process, complete sample bytes and lifecycle. No live game IPC/history reuse/shared-memory/native GPU integration or cadence proof.')
 Path('outputs/nfsug-native-renderer/camera-research/progressive-fixture-process-20261009.json').write_text(json.dumps(out,indent=2));print(out)
