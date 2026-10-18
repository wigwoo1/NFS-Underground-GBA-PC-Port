"""Live-shaped progressive sample owner; service integration remains experimental."""
import ctypes as C,json,threading,time,math
from concurrent.futures import Future,CancelledError
class ProgressivePair:
 def __init__(self,alphas,budget=64*1024*1024):
  self.alphas=tuple(alphas)
  if not 1<=len(self.alphas)<=8 or len(set(self.alphas))!=len(self.alphas) or any(not math.isfinite(a) or not 0<a<1 for a in self.alphas):raise ValueError('Invalid samples')
  self.budget=budget;self.bytes=0;self.cv=threading.Condition();self.samples={};self.source_masks={};self.source_cameras=();self.first=Future();self.closed=False;self.complete=False;self.error=None
 def publish(self,p):
  a,f,cb,mb,bb,ob,maskb,total,detailb,diagnosticb,cameras=p
  def doubles(raw):
   if type(raw) is not bytes or len(raw)%8:raise ValueError('Invalid double bytes')
   return (C.c_double*(len(raw)//8)).from_buffer_copy(raw)
  camera,models,bounds=map(doubles,(cb,mb,bb));detail=json.loads(detailb);diagnostic=json.loads(diagnosticb);n=detail['geometry_records']
  if len(camera)!=12 or len(models)!=12*n or len(bounds)!=4*n or len(ob)!=4*(n+1) or type(total) is not int or not 0<=total<=32768 or len(maskb)!=max(1,total):raise ValueError('Invalid complete sample dimensions')
  offsets=(C.c_uint32*(n+1)).from_buffer_copy(ob);mask=(C.c_uint8*len(maskb)).from_buffer_copy(maskb)
  if offsets[0]!=0 or offsets[-1]!=total or any(x>y for x,y in zip(offsets,offsets[1:])):raise ValueError('Invalid face offsets')
  size=len(f)+sum(map(len,(cb,mb,bb,ob,maskb)))
  with self.cv:
   if self.closed:raise CancelledError('Pair retired')
   if self.complete or len(self.samples)>=len(self.alphas) or a!=self.alphas[len(self.samples)]:raise ValueError('Out of order sample')
   if self.bytes+size>self.budget:raise ValueError('Sample budget exceeded')
   if self.source_cameras and self.source_cameras!=cameras:raise ValueError('Camera source changed')
   self.source_cameras=cameras;self.samples[a]=(f,camera,models,bounds,detail);self.source_masks[a]=(offsets,mask,total,diagnostic);self.bytes+=size
   if not self.first.done():self.first.set_result(self)
   self.cv.notify_all()
 def sample(self,alpha,timeout=20):
  if alpha not in self.alphas or not math.isfinite(timeout) or not 0<=timeout<=30:raise ValueError('Unrequested sample')
  deadline=time.monotonic()+timeout
  with self.cv:
   if self.error is not None:raise self.error
   while alpha not in self.samples:
    if self.closed:raise CancelledError('Pair retired')
    if self.error is not None:raise self.error
    if self.complete:raise ValueError('Missing completed sample')
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('Sample pending')
    self.cv.wait(remaining)
   if self.closed:raise CancelledError('Pair retired')
   return self.samples[alpha]
 def finish(self):
  with self.cv:
   if self.closed or len(self.samples)!=len(self.alphas):raise ValueError('Incomplete pair')
   self.complete=True;self.cv.notify_all()
 def fail(self,error):
  with self.cv:
   self.error=error
   if not self.first.done():self.first.set_exception(error)
   self.cv.notify_all()
 def close(self):
  with self.cv:
   self.closed=True;self.samples.clear();self.source_masks.clear();self.source_cameras=();self.bytes=0
   if not self.first.done():self.first.cancel()
   self.cv.notify_all()
