"""One bounded shared publication; caller copies before protocol acknowledgement."""
import pickle,time,os
from multiprocessing.shared_memory import SharedMemory
class SharedConnection:
 def __init__(self,connection,memory,writer=False):
  self.connection=connection;self.memory=memory;self.writer=writer;self.serial=0;self.descriptor_receive_trace=os.environ.get("NFSUG_DESCRIPTOR_RECEIVE_TRACE")=="1"
 def poll(self,*args):return self.connection.poll(*args)
 def send(self,message):
  if self.writer and type(message)is tuple and message[0]=='sample':
   begin=time.perf_counter_ns();payload=pickle.dumps(message[3],protocol=5);serialized=time.perf_counter_ns()
   if not 0<len(payload)<=self.memory.size:raise ValueError('Shared sample exceeds bounded publication')
   self.memory.buf[:len(payload)]=payload;copied=time.perf_counter_ns();self.serial+=1
   self.connection.send(('sample_shared',message[1],message[2],self.serial,len(payload)))
   self.last_write_profile=dict(begin_ns=begin,serialized_ns=serialized,copied_ns=copied,descriptor_sent_ns=time.perf_counter_ns(),payload_bytes=len(payload))
  else:self.connection.send(message)
 def recv(self):
  descriptor_profile=None
  if not self.writer and self.descriptor_receive_trace:
   descriptor_begin=time.perf_counter_ns();wire=self.connection.recv_bytes();descriptor_read=time.perf_counter_ns()
   message=pickle.loads(wire);descriptor_decoded=time.perf_counter_ns()
   descriptor_profile=dict(begin_ns=descriptor_begin,read_ns=descriptor_read,decoded_ns=descriptor_decoded,wire_bytes=len(wire))
  else:message=self.connection.recv()
  if not self.writer and type(message)is tuple and message[0]=='sample_shared':
   if len(message)!=5:raise ValueError('Invalid shared descriptor')
   _,generation,index,serial,size=message
   if any(type(v)is not int for v in (generation,index,serial,size)) or generation<0 or not 0<=index<8 or serial!=self.serial+1 or not 0<size<=self.memory.size:raise ValueError('Unowned shared publication')
   # Bytes copy detaches all pickle storage before acknowledgement releases writer.
   begin=time.perf_counter_ns();payload=bytes(self.memory.buf[:size]);copied=time.perf_counter_ns();packet=pickle.loads(payload);decoded=time.perf_counter_ns();self.serial=serial
   self.last_read_profile=dict(begin_ns=begin,copied_ns=copied,decoded_ns=decoded,payload_bytes=size,descriptor_receive=descriptor_profile)
   return ('sample',generation,index,packet)
  return message
 def close(self):self.connection.close()
class SharedInputConnection:
 def __init__(self,connection,memory,writer=False):
  self.connection=connection;self.memory=memory;self.writer=writer;self.serial=0
 def poll(self,*args):return self.connection.poll(*args)
 def send(self,message):
  if self.writer and type(message)is tuple and (type(message[0])is int or message[0]=='warm'):
   begin=time.perf_counter_ns();payload=pickle.dumps(message,protocol=5);serialized=time.perf_counter_ns()
   if not 0<len(payload)<=self.memory.size:raise ValueError('Input exceeds bounded publication')
   self.memory.buf[:len(payload)]=payload;copied=time.perf_counter_ns();self.serial+=1
   self.connection.send(('request_shared',self.serial,len(payload)))
   self.last_write_profile=dict(begin_ns=begin,serialized_ns=serialized,copied_ns=copied,descriptor_sent_ns=time.perf_counter_ns(),payload_bytes=len(payload))
  else:self.connection.send(message)
 def recv(self):
  message=self.connection.recv()
  if not self.writer and type(message)is tuple and message[0]=='request_shared':
   if len(message)!=3:raise ValueError('Invalid shared input descriptor')
   _,serial,size=message
   if type(serial)is not int or serial!=self.serial+1 or type(size)is not int or not 0<size<=self.memory.size:raise ValueError('Unowned input publication')
   trace=getattr(type(self),'input_read_trace',False)
   begin=time.perf_counter_ns() if trace else None
   payload=bytes(self.memory.buf[:size]);copied=time.perf_counter_ns() if trace else None
   request=pickle.loads(payload);decoded=time.perf_counter_ns() if trace else None
   if trace:self.last_read_profile=dict(begin_ns=begin,copied_ns=copied,decoded_ns=decoded,payload_bytes=size,serial=serial)
   if type(request)is not tuple or not request or not (type(request[0])is int or request[0]=='warm'):raise ValueError('Invalid input command')
   self.serial=serial;return request
  return message
 def close(self):self.connection.close()
def shared_worker(connection,rom,spec):
 from owned_progressive_process_service_candidate import worker
 import os
 SharedInputConnection.input_read_trace=os.environ.get('NFSUG_CHILD_INPUT_READ_TRACE')=='1'
 if os.environ.get('NFSUG_STREAMING_OUTPUT')=='1':
  import owned_streaming_output_write_candidate as output_stream
  output_stream.install()
  print('STREAMING_OUTPUT_SELECTED',flush=True)
 if os.environ.get('NFSUG_DIRECT_SHARED_INPUT_DECODE')=='1':
  if os.environ.get('NFSUG_CHILD_INPUT_NATIVE_COPY')=='1':raise ValueError('Conflicting private input decode candidates')
  import owned_direct_shared_input_decode_install_candidate
 if os.environ.get('NFSUG_CHILD_INPUT_NATIVE_COPY')=='1':import owned_shared_input_read_install_candidate
 memory=SharedMemory(name=spec[0]);inputs=SharedMemory(name=spec[2])
 try:
  if memory.size!=spec[1] or inputs.size!=spec[3]:raise ValueError('Shared publication extent mismatch')
  worker(SharedInputConnection(SharedConnection(connection,memory,True),inputs),rom)
 finally:inputs.close();memory.close()
