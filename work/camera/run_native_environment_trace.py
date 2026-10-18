"""Bounded machine CPU/memory context around the actual live runner; no process changes."""
import ctypes as C,time,threading,runpy,json,os
from pathlib import Path
class Memory(C.Structure):
 _fields_=[('length',C.c_ulong),('load',C.c_ulong),('total_physical',C.c_ulonglong),('available_physical',C.c_ulonglong),('total_page',C.c_ulonglong),('available_page',C.c_ulonglong),('total_virtual',C.c_ulonglong),('available_virtual',C.c_ulonglong),('extended',C.c_ulonglong)]
class FileTime(C.Structure):
 _fields_=[('low',C.c_uint32),('high',C.c_uint32)]
k=C.WinDLL('kernel32',use_last_error=True);k.GetSystemTimes.argtypes=[C.POINTER(FileTime)]*3;k.GlobalMemoryStatusEx.argtypes=[C.POINTER(Memory)]
def sample():
 idle,kernel,user=FileTime(),FileTime(),FileTime();m=Memory();m.length=C.sizeof(m)
 if not k.GetSystemTimes(C.byref(idle),C.byref(kernel),C.byref(user)) or not k.GlobalMemoryStatusEx(C.byref(m)):raise OSError(C.get_last_error())
 value=lambda x:x.low+(x.high<<32)
 return dict(stamp_ns=time.perf_counter_ns(),idle_100ns=value(idle),kernel_100ns=value(kernel),user_100ns=value(user),memory_load_percent=m.load,available_physical=m.available_physical,total_physical=m.total_physical,available_commit=m.available_page)
rows=[];errors=[];dropped=0;stop=threading.Event()
def observe():
 global dropped
 while not stop.is_set():
  try:
   v=sample()
   if len(rows)<512:rows.append(v)
   else:dropped+=1
  except Exception as e:errors.append(type(e).__name__);return
  stop.wait(.25)
t=threading.Thread(target=observe,name='bounded-environment-trace',daemon=True);t.start()
try:runpy.run_path('work/camera/run_native_sky_reader_bulk.py',run_name='__main__')
finally:
 stop.set();t.join(2)
 result=dict(result='CAPTURED_ENVIRONMENT_CONTEXT',logical_processors=os.cpu_count(),rows=rows,dropped=dropped,errors=errors,thread_stopped=not t.is_alive(),scope='250ms machine aggregate CPU/memory samples include preparation/startup/cleanup. Temporal context only, no process attribution or causal proof.')
 Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/environment-live.json').write_text(json.dumps(result,indent=2))
