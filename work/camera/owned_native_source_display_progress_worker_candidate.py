"""Bounded native owner-thread worker; caller owns game timing and sample selection."""
import queue,threading,ctypes as C,hashlib
from concurrent.futures import Future
from owned_dxgi_progress_totals_candidate import DisplayProgressTotals
from owned_native_source_display_stats_session_candidate import NativeSourceSession,NativeFrameIdentityError
class NativeSourceWorker:
 def __init__(self,capacity=2):
  if capacity<1:raise ValueError('capacity')
  self.display_progress=DisplayProgressTotals()
  self.display_stats_counts={};self.display_stats_latest=None
  self.async_records=[];self.async_pending={};self.async_dropped=0;self.async_not_ready=0;self.async_buffer=C.create_string_buffer(512*64*4)
  self.input_lock=threading.Lock();self.input_state=None;self.input_polls=0;self.input_poll_thread=None;self.jobs=queue.Queue(capacity);self.ready=threading.Event();self.error=None;self.closed=False;self.completed=0;self.thread=threading.Thread(target=self._run,name='NFSUG native source renderer');self.thread.start()
  if not self.ready.wait(20):raise TimeoutError('native initialization still running')
  if self.error:raise self.error
 def input_snapshot(self):
  with self.input_lock:
   if self.closed or self.input_state is None:raise RuntimeError('Native input unavailable')
   return self.input_state
 def _poll_input(self,session):
  assert threading.get_ident()==self.thread.ident
  state=(C.c_uint32*4)()
  if session.source.nf_owned_input_poll()!=1:raise RuntimeError('Native input polling failed')
  if session.source.nf_owned_input_snapshot(state)!=1:raise RuntimeError('Native input snapshot failed')
  with self.input_lock:
   self.input_state=tuple(state);self.input_polls+=1;self.input_poll_thread=threading.get_ident()
 def _put(self,item):
  while True:
   if self.error:raise self.error
   if not self.thread.is_alive():raise RuntimeError('native worker stopped')
   try:self.jobs.put(item,timeout=.1);return
   except queue.Full:pass
 def _submit(self,kind,owned,epoch,generation,index,diagnostic=False):
  if self.closed:raise RuntimeError('native worker closed')
  future=Future();self._put((kind,owned,epoch,generation,index,diagnostic,future));return future
 def submit(self,owned,epoch,generation,index,diagnostic=False):return self._submit('draw',owned,epoch,generation,index,diagnostic)
 def prepare(self,owned,epoch,generation,index,diagnostic=False):return self._submit('prepare',owned,epoch,generation,index,diagnostic)
 def present(self,epoch,generation,index):return self._submit('present',None,epoch,generation,index)
 def abort(self,epoch,generation,index):return self._submit('abort',None,epoch,generation,index)
 def _poll_async(self,session):
  d=session.consumer.d;d.nf_d3d_async_poll.argtypes=[C.c_uint,C.c_uint64,C.c_void_p,C.c_size_t]
  for slot,meta in list(self.async_pending.items()):
   rc=d.nf_d3d_async_poll(slot,meta['display_index'],self.async_buffer,len(self.async_buffer))
   if rc==3:self.async_not_ready+=1;continue
   assert rc==0,rc
   self.async_records.append(dict(**meta,rgba_sha256=hashlib.sha256(self.async_buffer.raw).hexdigest(),region=[300,594,512,64]));del self.async_pending[slot]
 def _run(self):
  session=None
  try:
   session=NativeSourceSession();session.source.nf_owned_input_snapshot.argtypes=[C.c_void_p];self._poll_input(session);self.ready.set()
   while True:
    self._poll_input(session);self._poll_async(session)
    try:job=self.jobs.get(timeout=.01)
    except queue.Empty:continue
    if job is None:break
    kind,owned,e,g,i,diagnostic,future=job
    try:
     request=None
     if kind=='prepare' and diagnostic:
      slot=next((n for n in range(3) if n not in self.async_pending),None)
      if slot is None:self.async_dropped+=1
      else:request=(slot,i)
     session.consumer.async_capture_request=request
     if kind=='draw':result=session.draw(owned,e,g,i)
     elif kind=='prepare':result=session.prepare(owned,e,g,i)
     elif kind=='present':
      result=session.present(e,g,i);self.display_progress.observe((e,g),result['dxgi_display_stats']);stats=result['dxgi_display_stats'];key=str(stats[0])+':'+str(stats[1]);self.display_stats_counts[key]=self.display_stats_counts.get(key,0)+1;self.display_stats_latest=stats
     elif kind=='abort':session.abort(e,g,i);result=None
     else:raise ValueError('Unknown native job')
     if request is not None:
      assert session.consumer.async_capture_status==0
      self.async_pending[request[0]]=dict(epoch=e,generation=g,display_index=i)
     if False:
      import numpy as np
      rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
      rgb=np.frombuffer(rgba.raw,np.uint8).reshape(2160,3840,4)[:,:,:3];result['native_rgb_sha256']=hashlib.sha256(rgb.tobytes()).hexdigest()
     self.completed+=1;future.set_result(result)
    except NativeFrameIdentityError as error:future.set_exception(error)
    except BaseException as error:future.set_exception(error);raise
  except BaseException as error:self.error=error
  finally:
   if session is not None:
    try:
     try:self._poll_async(session)
     finally:session.close()
    except BaseException as error:self.error=error
   with self.input_lock:self.input_state=None
   self.ready.set()
   while True:
    try:job=self.jobs.get_nowait()
    except queue.Empty:break
    if job is not None:job[-1].set_exception(self.error or RuntimeError('native worker stopped'))
 def close(self):
  if self.closed:return
  self.closed=True
  if self.thread.is_alive() and not self.error:self._put(None)
  self.thread.join(20)
  if self.thread.is_alive():raise TimeoutError('native worker close still running')
  if self.error:raise self.error
