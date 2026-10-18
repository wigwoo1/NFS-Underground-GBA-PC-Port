"""Opt-in bounded output pickle stream, unchanged receiver and acknowledgement."""
import pickle,time
from owned_streaming_input_write_candidate import BoundedWriter
def send(self,message):
 if self.writer and type(message)is tuple and message[0]=='sample':
  begin=time.perf_counter_ns();writer=BoundedWriter(self.memory)
  pickle.dump(message[3],writer,protocol=5);copied=time.perf_counter_ns()
  if not 0<writer.size<=self.memory.size:raise ValueError('Shared sample exceeds bounded publication')
  self.serial+=1
  self.connection.send(('sample_shared',message[1],message[2],self.serial,writer.size))
  self.last_write_profile=dict(begin_ns=begin,serialized_ns=copied,copied_ns=copied,descriptor_sent_ns=time.perf_counter_ns(),payload_bytes=writer.size,native_copy=True,streaming_pickle=True,copy_elapsed_ns=writer.copy_ns,chunk_count=writer.writes)
 else:self.connection.send(message)
def install():
 import owned_progressive_shared_transport_candidate as transport
 transport.SharedConnection.send=send
