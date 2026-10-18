"""Optional, thread-owned Windows priority lease for renderer diagnostics."""
import ctypes as C,threading
class ThreadPriorityLease:
 def __init__(self,requested):
  if requested not in (0,1):raise ValueError('Invalid diagnostic renderer priority')
  self.requested=requested;self.owner=threading.get_ident();self.closed=False
  self.kernel=C.WinDLL('kernel32',use_last_error=True);self.kernel.GetCurrentThread.restype=C.c_void_p;self.kernel.GetThreadPriority.argtypes=[C.c_void_p];self.kernel.SetThreadPriority.argtypes=[C.c_void_p,C.c_int]
  self.thread=self.kernel.GetCurrentThread();self.before=self.kernel.GetThreadPriority(self.thread)
  if self.before==0x7fffffff:raise OSError(C.get_last_error(),'Read thread priority failed')
  if requested and not self.kernel.SetThreadPriority(self.thread,requested):raise OSError(C.get_last_error(),'Set thread priority failed')
  self.applied=self.kernel.GetThreadPriority(self.thread);self.restored=None
  if self.applied!=(requested if requested else self.before):
   self.close();raise RuntimeError('Renderer priority verification failed')
 def close(self):
  if threading.get_ident()!=self.owner:raise RuntimeError('Priority lease belongs to another thread')
  if self.closed:return
  if self.requested and not self.kernel.SetThreadPriority(self.thread,self.before):raise OSError(C.get_last_error(),'Restore thread priority failed')
  self.restored=self.kernel.GetThreadPriority(self.thread)
  if self.restored!=self.before:raise RuntimeError('Priority restoration verification failed')
  self.closed=True
 def evidence(self):return dict(requested=self.requested,before=self.before,applied=self.applied,restored=self.restored,closed=self.closed,owner=self.owner)
