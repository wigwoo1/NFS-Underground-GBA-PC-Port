from owned_shared_blob import SharedBlobOwner
from multiprocessing.shared_memory import SharedMemory
import multiprocessing as mp,json
from pathlib import Path

def reader(connection):
 memory=None
 try:
  name=connection.recv();memory=SharedMemory(name=name);connection.send('attached');connection.recv()
 finally:
  if memory is not None:memory.close()
  connection.close()
if __name__=='__main__':
 context=mp.get_context('spawn');checks=0
 for forced in (False,True):
  owner=SharedBlobOwner(1024*1024);descriptor=owner.publish(b'a'*1024*1024,17);parent,other=context.Pipe();process=context.Process(target=reader,args=(other,));process.start();other.close()
  try:
   parent.send(owner.memory.name);assert parent.poll(5) and parent.recv()=='attached'
   try:owner.retire_after_consumer_exit(process)
   except ValueError:checks+=1
   else:raise AssertionError('Live lease retired')
   if forced:process.terminate()
   else:parent.send(None)
   process.join(5);assert not process.is_alive() and process.exitcode is not None
   name=owner.memory.name;owner.retire_after_consumer_exit(process);owner.retire_after_consumer_exit(process);checks+=1
   try:SharedMemory(name=name)
   except FileNotFoundError:checks+=1
   else:raise AssertionError('Abandoned mapping retained')
   try:owner.publish(b'b',18)
   except ValueError:checks+=1
   else:raise AssertionError('Retired lease reused')
  finally:
   parent.close()
   if process.is_alive():process.terminate();process.join(5)
   if not owner.closed:owner.retire_after_consumer_exit(process)
 out=dict(result='PASS',checks=checks,normal_and_forced_consumer_exit=True,live_retirement_rejected=True,scope='Owned mock consumer lifecycle only; renderer integration pending')
 Path('work/camera/shared-blob-retirement-tests.json').write_text(json.dumps(out,indent=2));print(out)
