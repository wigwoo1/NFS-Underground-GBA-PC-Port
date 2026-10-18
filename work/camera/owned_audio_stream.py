"""Producer-owned original PCM admission; device submission is asynchronous.
Deadlines use the renderer clock origin plus its original-refresh delay.
No claim of audible/scanout synchronization: device latency must be measured.
"""
import ctypes as C
import threading
import time

class OwnedAudioStream:
 def __init__(self, bridge, output, epoch, rate=48000, capacity=32, minimum_frames=1):
  if not 1<=minimum_frames<=4096:raise ValueError('Invalid PCM batch threshold')
  self.minimum_frames=minimum_frames
  self.bridge=bridge;self.output=output;self.owner=threading.get_ident()
  self.epoch=epoch;self.generation=1;self.rate=rate;self.first_sample=0
  self.pending=None;self.paused=False;self.closed=False;self.accepted=0;self.retries=0;self.last_result=None
  P=C.c_void_p;U=C.c_uint64
  for name,args,restype in (('create',[U,C.c_uint,C.c_uint],P),('push',[P,U,U,U,U,U,P,C.c_uint],C.c_int),('retire',[P,U],U),('resume',[P,U,U],C.c_int),('status',[P,P],C.c_int),('close',[P,C.c_uint],C.c_int)):
   f=getattr(output,'nf_audio_output_'+name);f.argtypes=args;f.restype=restype
  bridge.nf_original_audio_read.argtypes=[P,C.c_uint]
  bridge.nf_original_audio_available.argtypes=[P]
  if not bridge.nf_original_audio_configure(rate):raise RuntimeError('Original audio configuration failed')
  self.handle=output.nf_audio_output_create(epoch,rate,capacity)
  if not self.handle:raise RuntimeError('Audio output creation failed')
 def _owner(self):
  if self.closed or threading.get_ident()!=self.owner:raise RuntimeError('Closed or foreign audio owner')
 def status(self):
  self._owner();out=(C.c_uint64*14)()
  if not self.output.nf_audio_output_status(self.handle,out):raise RuntimeError('Audio status unavailable')
  if out[4]:raise RuntimeError('Audio device error '+str(out[4]))
  return tuple(out)
 def pump(self,refresh,origin_ns,delay_refreshes):
  """One bounded chunk per call. Retry pending bytes before reading more PCM.
  False means explicit backpressure/not-ready; caller must retry without
  advancing logic to manufacture missing sound or declaring dropped PCM okay.
  """
  self._owner()
  if self.paused:return False
  if delay_refreshes<0:raise ValueError('Negative presentation delay')
  if self.pending is None:
   available=(C.c_uint*2)()
   if not self.bridge.nf_original_audio_available(available) or available[0]!=available[1]:raise RuntimeError('Original stereo availability mismatch')
   if available[0]<self.minimum_frames:return True
   buf=(C.c_int16*8192)();n=self.bridge.nf_original_audio_read(buf,min(4096,available[0]))
   if n<=0:raise RuntimeError('Original PCM read failed')
   delay=(delay_refreshes*280896*1000000000+16777215)//16777216
   deadline=origin_ns+delay+(self.first_sample*1000000000+self.rate-1)//self.rate
   self.pending=(buf,n,refresh,deadline)
  buf,n,tag,deadline=self.pending
  result=self.output.nf_audio_output_push(self.handle,self.epoch,self.generation,tag,self.first_sample,deadline,buf,n)
  self.last_result=result
  if result==1:self.first_sample+=n;self.accepted+=n;self.pending=None;return True
  if result in (0,-3,-4):self.retries+=1;return False
  raise RuntimeError('Audio admission rejected '+str(result))
 def pump_retry_busy(self,refresh,origin_ns,delay_refreshes,attempts=4):
  """Bounded retry of lock contention only; never wait for device capacity."""
  if not 1<=attempts<=8:raise ValueError('Invalid busy retry bound')
  for attempt in range(attempts):
   if self.pump(refresh,origin_ns,delay_refreshes):return True
   if self.last_result!=-3:return False
   if attempt+1<attempts:time.sleep(0) # Yield to the lock owner; never wait for capacity.
  return False
 def retire(self,epoch=None):
  self._owner();epoch=self.epoch if epoch is None else epoch
  generation=self.output.nf_audio_output_retire(self.handle,epoch)
  if not generation:raise RuntimeError('Audio retirement rejected')
  self.epoch=epoch;self.generation=generation;self.paused=True
  self.pending=None;self.first_sample=0
  if not self.bridge.nf_original_audio_clear():raise RuntimeError('Original audio clear failed')
 def resume(self):
  """Nonblocking: caller supplies a newly aligned origin to subsequent pump."""
  self._owner()
  if not self.paused:raise RuntimeError('Audio is not retired')
  if not self.output.nf_audio_output_resume(self.handle,self.epoch,self.generation):return False
  self.paused=False;return True
 def close(self):
  self._owner()
  if not self.output.nf_audio_output_close(self.handle,5000):raise RuntimeError('Audio shutdown retained resources')
  self.closed=True;self.handle=None
