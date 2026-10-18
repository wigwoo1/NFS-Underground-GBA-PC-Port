"""One bounded blob lease; control-channel acknowledgement precedes reuse.
Single publisher owns lifecycle. Consumer copies immutable bytes before ack.
No concurrent mutation or retained native/shared-memory pointers are allowed.
"""
import struct
from multiprocessing.shared_memory import SharedMemory
_HEADER=struct.Struct('<4Q');_MAGIC=0x4e465342
class SharedBlobOwner:
 def __init__(self,capacity):
  if not isinstance(capacity,int) or not 1<=capacity<=64*1024*1024:raise ValueError('Invalid shared blob capacity')
  self.capacity=capacity;self.memory=SharedMemory(create=True,size=_HEADER.size+capacity);self.serial=0;self.pending=None;self.closed=False
 def publish(self,data,generation):
  if self.closed or self.pending is not None:raise ValueError('Shared blob unavailable')
  if not isinstance(data,bytes) or not 0<len(data)<=self.capacity or not isinstance(generation,int) or not 0<=generation<2**64:raise ValueError('Invalid shared blob publication')
  self.serial+=1
  self.memory.buf[_HEADER.size:_HEADER.size+len(data)]=data
  _HEADER.pack_into(self.memory.buf,0,_MAGIC,generation,self.serial,len(data))
  self.pending=(self.memory.name,generation,self.serial,len(data));return self.pending
 def acknowledge(self,descriptor):
  if self.closed or descriptor!=self.pending or self.pending is None:raise ValueError('Invalid shared blob acknowledgement')
  self.pending=None
 def retire_after_consumer_exit(self,consumer):
  """Release an abandoned lease only after its sole consumer is terminal.
  Never permits reuse; a still-live or unstarted consumer is insufficient proof.
  """
  if self.closed:return
  if consumer.is_alive() or consumer.exitcode is None:raise ValueError('Shared blob consumer is not terminal')
  self.memory.close();self.memory.unlink();self.pending=None;self.closed=True
 def close(self):
  if self.closed:return
  if self.pending is not None:raise ValueError('Unacknowledged shared blob')
  self.memory.close();self.memory.unlink();self.closed=True

def read_shared_blob(descriptor,expected_generation):
 if not isinstance(descriptor,tuple) or len(descriptor)!=4:raise ValueError('Invalid shared blob descriptor')
 name,generation,serial,length=descriptor
 if not isinstance(name,str) or generation!=expected_generation or not isinstance(serial,int) or serial<=0 or not isinstance(length,int) or not 1<=length<=64*1024*1024:raise ValueError('Invalid shared blob identity')
 memory=SharedMemory(name=name)
 try:
  if length>memory.size-_HEADER.size or _HEADER.unpack_from(memory.buf)!=(_MAGIC,generation,serial,length):raise ValueError('Stale shared blob lease')
  result=bytes(memory.buf[_HEADER.size:_HEADER.size+length])
  if _HEADER.unpack_from(memory.buf)!=(_MAGIC,generation,serial,length):raise ValueError('Changed shared blob lease')
  return result
 finally:memory.close()
