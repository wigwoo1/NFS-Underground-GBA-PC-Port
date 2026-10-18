"""Bounded native owner-thread worker; caller owns game timing and sample selection."""
import queue,threading,ctypes as C,hashlib
from concurrent.futures import Future
from owned_native_source_staged_session_candidate import NativeSourceSession
class NativeSourceWorker:
 def __init__(self,capacity=2):
  if capacity<1:raise ValueError('capacity')
  self.jobs=queue.Queue(capacity);self.ready=threading.Event();self.error=None;self.closed=False;self.completed=0;self.thread=threading.Thread(target=self._run,name='NFSUG native source renderer');self.thread.start()
  if not self.ready.wait(20):raise TimeoutError('native initialization still running')
  if self.error:raise self.error
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
 def _run(self):
  session=None
  try:
   session=NativeSourceSession();self.ready.set()
   while True:
    job=self.jobs.get()
    if job is None:break
    kind,owned,e,g,i,diagnostic,future=job
    try:
     if kind=='draw':result=session.draw(owned,e,g,i)
     elif kind=='prepare':result=session.prepare(owned,e,g,i)
     elif kind=='present':result=session.present(e,g,i)
     elif kind=='abort':session.abort(e,g,i);result=None
     else:raise ValueError('Unknown native job')
     if diagnostic:
      import numpy as np
      rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
      rgb=np.frombuffer(rgba.raw,np.uint8).reshape(2160,3840,4)[:,:,:3];result['native_rgb_sha256']=hashlib.sha256(rgb.tobytes()).hexdigest()
     self.completed+=1;future.set_result(result)
    except BaseException as error:future.set_exception(error);raise
  except BaseException as error:self.error=error
  finally:
   if session is not None:
    try:session.close()
    except BaseException as error:self.error=error
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
