"""Opt-in bounded native FIFO; only integer notification identities cross C."""
import ctypes as C,math,queue
from pathlib import Path
class NativeNotificationQueue:
 def __init__(self,capacity):
  self.dll=C.CDLL(str(Path('work/camera/owned-notification-queue.dll').resolve()))
  self.dll.nf_notification_create.argtypes=[C.c_uint];self.dll.nf_notification_create.restype=C.c_void_p
  self.dll.nf_notification_put.argtypes=[C.c_void_p,C.c_uint64,C.c_uint]
  self.dll.nf_notification_get.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
  self.dll.nf_notification_destroy.argtypes=[C.c_void_p];self.dll.nf_notification_destroy.restype=None
  self.owner=self.dll.nf_notification_create(capacity)
  if not self.owner:raise RuntimeError('Native notification allocation failed')
  self.last_get=None
 def put(self,value,timeout):
  if not self.owner:raise RuntimeError('Notification queue closed')
  stamp=0 if value==0 else value[0]
  result=self.dll.nf_notification_put(self.owner,stamp,math.ceil(timeout*1000))
  if result==0:raise queue.Full
  if result!=1:raise RuntimeError('Native notification put failed')
 def get(self,timeout):
  if not self.owner:raise RuntimeError('Notification queue closed')
  out=(C.c_uint64*4)();result=self.dll.nf_notification_get(self.owner,math.ceil(timeout*1000),out)
  self.last_get=list(out)
  if result==0:raise queue.Empty
  if result!=1:raise RuntimeError('Native notification get failed')
  return (out[3],) if out[3] else 0
 def close(self):
  if self.owner:self.dll.nf_notification_destroy(self.owner);self.owner=None
