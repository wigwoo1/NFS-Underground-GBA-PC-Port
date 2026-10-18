"""Renderer-thread-owned bounded metadata for delayed diagnostic crop results."""
import ctypes as C
import hashlib
import threading
import os

class CropLedger:
 def __init__(self,gpu,limit=120):
  if not 1<=limit<=3600:raise ValueError('Invalid diagnostic limit')
  self.gpu=gpu;self.owner=threading.get_ident();self.limit=limit;self.serial=0
  self.pending={};self.completed=[];self.omitted=[];self.retired=[]
  self.crop_origin=(int(os.environ.get("NF_ASYNC_CROP_X","300")),int(os.environ.get("NF_ASYNC_CROP_Y","600")))
  if not 0<=self.crop_origin[0]<=3776 or not 0<=self.crop_origin[1]<=2144:raise ValueError("Async crop origin is outside the 4K target")
  self.buffer=C.create_string_buffer(3072);self.identity=C.c_uint64()
  gpu.nf_crop_enqueue.argtypes=[C.c_uint64,C.c_uint,C.c_uint]
  gpu.nf_crop_poll.argtypes=[C.POINTER(C.c_uint64),C.c_void_p,C.c_size_t]
 def check_owner(self):
  if threading.get_ident()!=self.owner:raise RuntimeError('Crop ledger owner mismatch')
 def poll(self):
  self.check_owner()
  for _ in range(3):
   rc=self.gpu.nf_crop_poll(C.byref(self.identity),self.buffer,3072)
   if rc in (0,2):return
   if rc!=1:raise RuntimeError('Crop poll failed: '+str(rc))
   ident=self.identity.value
   if ident not in self.pending:raise RuntimeError('Unowned crop identity')
   row=self.pending.pop(ident)
   completed=dict(row,capture_id=ident,sha256=hashlib.sha256(self.buffer.raw).hexdigest(),bytes=3072)
   if os.environ.get('NF_ASYNC_CROP_SAVE_PIXELS')=='1':completed['pixels_hex']=self.buffer.raw.hex()
   self.completed.append(completed)
 def enqueue(self,metadata,target,epoch):
  self.check_owner();self.poll()
  if self.serial>=self.limit:return False
  required=('epoch','generation','display_index','source_older','refresh','alpha')
  row={key:metadata[key] for key in required}
  if row['epoch']!=epoch:raise ValueError('Selected crop epoch mismatch')
  x,y=self.crop_origin
  row.update(target=int(target),consumer_thread=self.owner,crop=[x,y,x+64,y+16])
  self.serial+=1;ident=self.serial
  rc=self.gpu.nf_crop_enqueue(ident,x,y)
  if rc==2:self.omitted.append(dict(row,capture_id=ident,reason='diagnostic_queue_full'));return False
  if rc!=0:raise RuntimeError('Crop enqueue failed: '+str(rc))
  self.pending[ident]=row
  if len(self.pending)>3:raise RuntimeError('Crop ownership exceeds native capacity')
  return True
 def retire(self):
  # Called on owner before GPU close. No blocking drain at a game deadline.
  self.check_owner();self.poll()
  self.retired.extend(dict(row,capture_id=ident,reason='close_before_ready') for ident,row in self.pending.items());self.pending.clear()
 def report(self):
  self.check_owner()
  return dict(attempts=self.serial,completed=self.completed,omitted=self.omitted,retired=self.retired,pending=len(self.pending),scope='Final-target diagnostic crop may contain foreground; GPU completion is not commit or physical scanout proof.')
