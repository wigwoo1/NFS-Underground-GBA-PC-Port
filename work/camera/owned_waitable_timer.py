"""Optional owner-thread high-resolution timer; bounded waits, no clock changes."""
import ctypes as C,threading
class OwnedWaitableTimer:
 def __init__(self):
  self.owner=threading.get_ident();self.handle=None
  self.k=C.WinDLL('kernel32',use_last_error=True)
  self.k.CreateWaitableTimerExW.argtypes=[C.c_void_p,C.c_wchar_p,C.c_uint32,C.c_uint32];self.k.CreateWaitableTimerExW.restype=C.c_void_p
  self.k.SetWaitableTimer.argtypes=[C.c_void_p,C.POINTER(C.c_int64),C.c_int32,C.c_void_p,C.c_void_p,C.c_int]
  self.k.WaitForSingleObject.argtypes=[C.c_void_p,C.c_uint32];self.k.CloseHandle.argtypes=[C.c_void_p]
  self.handle=self.k.CreateWaitableTimerExW(None,None,2,0x1f0003)
  if not self.handle:raise C.WinError(C.get_last_error())
 def wait_slice(self,nanoseconds):
  assert threading.get_ident()==self.owner
  if self.handle is None:raise RuntimeError('Timer closed')
  if not 0<nanoseconds<=10000000:raise ValueError('Timer slice must be positive and at most10ms')
  due=C.c_int64(-max(1,(nanoseconds+99)//100))
  if not self.k.SetWaitableTimer(self.handle,C.byref(due),0,None,None,False):raise C.WinError(C.get_last_error())
  result=self.k.WaitForSingleObject(self.handle,1000)
  if result!=0:raise RuntimeError(('Timer wait failed',result))
 def close(self):
  assert threading.get_ident()==self.owner
  if self.handle is not None:
   if not self.k.CloseHandle(self.handle):raise C.WinError(C.get_last_error())
   self.handle=None
