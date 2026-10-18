"""Bounded parent protocol for one ordered progressive source request."""
import multiprocessing as mp,math,time,os
from owned_geometry_process_codec_candidate import pack_geometry as pack
from owned_progressive_process_service_candidate import worker
from owned_geometry_process_codec_candidate import GeometryFrameDecoder as FrameDecoder
class ProgressiveService:
 def __init__(self,rom,shared_output=False):
  ctx=mp.get_context('spawn');self.connection,child=ctx.Pipe();self.shared_memory=None;self.input_memory=None
  target=worker;args=(child,rom)
  if shared_output:
   from multiprocessing.shared_memory import SharedMemory
   from owned_progressive_shared_transport_candidate import SharedConnection,SharedInputConnection,shared_worker
   self.shared_memory=SharedMemory(create=True,size=64*1024*1024);self.input_memory=SharedMemory(create=True,size=64*1024*1024);target=shared_worker;args=(child,rom,(self.shared_memory.name,self.shared_memory.size,self.input_memory.name,self.input_memory.size))
   self.connection=SharedInputConnection(SharedConnection(self.connection,self.shared_memory),self.input_memory,True)
  self.process=ctx.Process(target=target,args=args);self.process.start();child.close()
  self.receive_poll_trace=os.environ.get('NFSUG_PARENT_RECEIVE_POLL_TRACE')=='1';self.last_receive_poll=None
  self.generation=0;self.active=False;self.closed=False;self.previous=None;self.lease=None;self.decoder=None;self.count=0;self.alphas=();self.newer_identity=None;self.last_terminal=None
 def warm_start(self,frame,scene):
  if self.closed or self.active or self.previous is not None:raise ValueError('Invalid startup state')
  self.connection.send(('warm',self.generation,pack(frame,scene)));message=self._receive(30)
  if message[:2]!=('warm',self.generation):raise RuntimeError('Progressive startup failed: '+repr(message))
  evidence=message[2]
  if (evidence['epoch'],evidence['refresh'])!=tuple(scene.identity[:2]):raise ValueError('Startup identity mismatch')
  self.previous=scene.identity;return evidence
 def start(self,older,newer,alphas):
  if self.closed or self.active:raise ValueError('Progressive service busy or closed')
  alphas=tuple(alphas)
  if not 0<=len(alphas)<=8 or len(set(alphas))!=len(alphas) or any(not math.isfinite(a) or not 0<a<1 for a in alphas):raise ValueError('Invalid sample list')
  oldframe,oldscene=older;newframe,newscene=newer;reuse=self.previous==oldscene.identity
  pack_begin=time.perf_counter_ns();request=(self.generation,None if reuse else pack(oldframe,oldscene),oldscene.identity,pack(newframe,newscene),alphas,True);packed=time.perf_counter_ns()
  self.connection.send(request);self.last_start_timing=dict(pack_begin_ns=pack_begin,packed_ns=packed,sent_ns=time.perf_counter_ns(),input_write=getattr(self.connection,"last_write_profile",None),input_bytes=sum(len(v) for packet in (request[1],request[3]) if packet is not None for v in packet if v is not None));self.decoder=FrameDecoder(self.generation,owners=(bytes(oldframe),bytes(newframe)));self.active=True;self.count=0;self.lease=None;self.alphas=alphas;self.newer_identity=newscene.identity
 def _receive(self,timeout):
  if not math.isfinite(timeout) or not 0<=timeout<=30:raise ValueError('Invalid wait')
  if self.receive_poll_trace:
   begin=time.perf_counter_ns();ready=self.connection.poll(timeout);polled=time.perf_counter_ns()
   if not ready:raise TimeoutError('Progressive worker response pending')
   recv_begin=time.perf_counter_ns();message=self.connection.recv();received=time.perf_counter_ns()
   self.last_receive_poll=dict(begin_ns=begin,poll_completed_ns=polled,recv_begin_ns=recv_begin,received_ns=received)
   return message
  if not self.connection.poll(timeout):raise TimeoutError('Progressive worker response pending')
  return self.connection.recv()
 def take(self,timeout=20):
  if not self.active or self.lease is not None or self.count>=len(self.alphas):raise ValueError('No admissible sample take')
  receive_begin=time.perf_counter_ns();message=self._receive(timeout);received=time.perf_counter_ns()
  if message[0]=='terminal':
   self._terminal(message);raise RuntimeError('Progressive preparation failed: '+str(message[4]))
  kind,generation,index,packet=message
  if kind!='sample' or generation!=self.generation or index!=self.count or packet[0]!=self.alphas[index]:raise ValueError('Unowned progressive sample')
  packet=(packet[0],self.decoder.decode(packet[1]),*packet[2:]);self.lease=(generation,index);self.count+=1;self.last_sample_timing=dict(receive_poll=None if not self.receive_poll_trace else dict(self.last_receive_poll),index=index,receive_begin_ns=receive_begin,received_ns=received,decoded_ns=time.perf_counter_ns(),shared_read=getattr(getattr(self.connection,"connection",None),"last_read_profile",None));return self.lease,packet
 def acknowledge(self,token):
  if not self.active or token!=self.lease:raise ValueError('Unknown progressive acknowledgement')
  self.connection.send(('ack',*token));self.lease=None
 def _terminal(self,message):
  if message[0]!='terminal' or message[1]!=self.generation:raise ValueError('Unowned terminal')
  self.last_terminal=message;self.previous=self.newer_identity if message[2]=='complete' else None
  self.decoder.close();self.decoder=None;self.active=False;self.lease=None
 def finish(self,timeout=20):
  if not self.active or self.lease is not None or self.count!=len(self.alphas):raise ValueError('Incomplete progressive stream')
  message=self._receive(timeout);self._terminal(message)
  if message[2]!='complete' or message[3]!=self.count:raise RuntimeError('Progressive stream failed')
  return message
 def invalidate(self,timeout=20):
  if self.closed:raise ValueError('Service closed')
  if self.active:
   if self.lease is None:
    message=self._receive(timeout)
    if message[0]=='terminal':self._terminal(message)
    else:
     if message[:3]!=('sample',self.generation,self.count):raise ValueError('Invalid cancellation sample')
     self.lease=(self.generation,self.count)
   if self.active:
    self.connection.send(('retire',self.generation));self._terminal(self._receive(timeout))
  self.generation+=1;self.previous=None
 def close(self):
  if self.closed:return
  self.invalidate();self.connection.send(None);self.process.join(15)
  if self.process.is_alive():raise RuntimeError('Progressive worker shutdown pending')
  self.connection.close()
  if self.shared_memory is not None:self.shared_memory.close();self.shared_memory.unlink();self.shared_memory=None
  if self.input_memory is not None:self.input_memory.close();self.input_memory.unlink();self.input_memory=None
  self.closed=True
  if self.process.exitcode!=0:raise RuntimeError('Progressive worker exited with error')
