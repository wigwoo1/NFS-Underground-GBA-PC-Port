"""Opt-in bounded direct pickle writes; unchanged protocol and detached receiver."""
import ctypes as C,pickle,time
from owned_shared_payload_copy_binding_candidate import library
class BoundedWriter:
 def __init__(self,memory):self.memory=memory;self.size=0;self.copy_ns=0;self.writes=0
 def write(self,payload):
  if type(payload)is not bytes:raise ValueError('Expected immutable pickle bytes')
  n=len(payload)
  if n>self.memory.size-self.size:raise ValueError('Input exceeds bounded publication')
  if not n:return 0
  target=C.c_char.from_buffer(self.memory.buf,self.size)
  try:
   begin=time.perf_counter_ns();source=C.c_char_p(payload)
   if library.nf_shared_payload_copy(C.addressof(target),self.memory.size-self.size,source,n)!=1:raise ValueError('Native streaming copy failed')
   self.copy_ns+=time.perf_counter_ns()-begin
  finally:del target
  self.size+=n;self.writes+=1;return n
def send(self,message):
 if self.writer and type(message)is tuple and (type(message[0])is int or message[0]=='warm'):
  begin=time.perf_counter_ns();writer=BoundedWriter(self.memory);pickle.dump(message,writer,protocol=5);copied=time.perf_counter_ns()
  if not 0<writer.size<=self.memory.size:raise ValueError('Input exceeds bounded publication')
  self.serial+=1;self.connection.send(('request_shared',self.serial,writer.size))
  self.last_write_profile=dict(begin_ns=begin,serialized_ns=copied,copied_ns=copied,descriptor_sent_ns=time.perf_counter_ns(),payload_bytes=writer.size,native_copy=True,streaming_pickle=True,copy_elapsed_ns=writer.copy_ns,chunk_count=writer.writes)
 else:self.connection.send(message)
def install():
 import owned_progressive_shared_transport_candidate as transport
 transport.SharedInputConnection.send=send
