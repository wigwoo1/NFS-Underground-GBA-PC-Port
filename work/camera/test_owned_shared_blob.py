from owned_shared_blob import SharedBlobOwner,read_shared_blob
import multiprocessing as mp,json
from pathlib import Path

def child(connection):
 try:
  while True:
   item=connection.recv()
   if item is None:return
   descriptor,generation= item
   data=read_shared_blob(descriptor,generation)
   connection.send((descriptor,data))
 finally:connection.close()
if __name__=='__main__':
 context=mp.get_context('spawn');parent,other=context.Pipe();process=context.Process(target=child,args=(other,));process.start();other.close();owner=SharedBlobOwner(8*1024*1024);checks=0;rejections=0
 def reject(call):
  global rejections
  try:call()
  except ValueError:rejections+=1;return
  raise AssertionError('Expected rejection')
 try:
  reject(lambda:owner.publish(b'',1));reject(lambda:owner.publish(b'x'*(8*1024*1024+1),1))
  stale=None
  for generation in range(4):
   data=bytes(range(256))*(8192+generation*4096);descriptor=owner.publish(data,generation)
   reject(lambda:owner.publish(b'x',generation));reject(lambda:owner.close());reject(lambda:read_shared_blob(descriptor,generation+1));reject(lambda:owner.acknowledge((descriptor[0],generation,999,descriptor[3])))
   if stale is not None:reject(lambda:read_shared_blob(stale,stale[1]))
   parent.send((descriptor,generation));assert parent.poll(10);ack,result=parent.recv();assert result==data and isinstance(result,bytes);owner.acknowledge(ack);checks+=1;stale=descriptor
  reject(lambda:owner.acknowledge(stale));parent.send(None);process.join(10);assert not process.is_alive() and process.exitcode==0
  name=owner.memory.name;owner.close();owner.close();reject(lambda:owner.publish(b'x',1))
  from multiprocessing.shared_memory import SharedMemory
  try:memory=SharedMemory(name=name)
  except FileNotFoundError:checks+=1
  else:memory.close();raise AssertionError('Mapping retained after close')
 finally:
  parent.close()
  if process.is_alive():process.terminate();process.join(5)
 out=dict(result='PASS',exact_cross_process_blobs=4,checks=checks,rejections=rejections,scope='Bounded acknowledged immutable blob transport component; not live scene integration or performance proof')
 Path('work/camera/owned-shared-blob-tests.json').write_text(json.dumps(out,indent=2));print(out)
