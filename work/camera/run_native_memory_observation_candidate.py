"""Bounded once-per-second renderer process memory observation."""
import ctypes as C,json,subprocess,sys,time,os
from pathlib import Path
from collections import deque
class Memory(C.Structure):
 _fields_=[('cb',C.c_uint32),('PageFaultCount',C.c_uint32)]+[(name,C.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
api=C.WinDLL('psapi');api.GetProcessMemoryInfo.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32];api.GetProcessMemoryInfo.restype=C.c_int
child_file=Path('work/camera/prototype-runs')/('memory-child-'+str(time.time_ns())+'.txt')
env=dict(os.environ,NFS_MEMORY_CHILD_FILE=str(child_file.resolve()))
process=subprocess.Popen([sys.executable,'work/camera/run_native_d3d_bounded_diagnostics_candidate.py',*sys.argv[1:]],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env)
kernel=C.WinDLL('kernel32');kernel.OpenProcess.argtypes=[C.c_uint32,C.c_int,C.c_uint32];kernel.OpenProcess.restype=C.c_void_p;kernel.CloseHandle.argtypes=[C.c_void_p]
api.EnumProcessModulesEx.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32]
api.GetModuleFileNameExW.argtypes=[C.c_void_p,C.c_void_p,C.c_wchar_p,C.c_uint32]
rows=deque(maxlen=120);start=time.monotonic();child_handle=None;modules=[]
while process.poll() is None:
 m=Memory();m.cb=C.sizeof(m)
 if api.GetProcessMemoryInfo(int(process._handle),C.byref(m),m.cb):rows.append(dict(seconds=time.monotonic()-start,working_set=m.WorkingSetSize,private_bytes=m.PrivateUsage))
 if child_handle is None and child_file.exists():child_handle=kernel.OpenProcess(0x410,False,int(child_file.read_text()))
 if child_handle:
  child_memory=Memory();child_memory.cb=C.sizeof(child_memory)
  if api.GetProcessMemoryInfo(child_handle,C.byref(child_memory),child_memory.cb):rows[-1].update(child_private_bytes=child_memory.PrivateUsage,child_working_set=child_memory.WorkingSetSize)
 if not modules and time.monotonic()-start>10:
  handles=(C.c_void_p*1024)();needed=C.c_uint32()
  if api.EnumProcessModulesEx(int(process._handle),handles,C.sizeof(handles),C.byref(needed),3):
   for handle in handles[:min(1024,needed.value//C.sizeof(C.c_void_p))]:
    name=C.create_unicode_buffer(32768)
    if api.GetModuleFileNameExW(int(process._handle),handle,name,len(name)):modules.append(name.value)
 time.sleep(1)
if child_handle:kernel.CloseHandle(child_handle)
output=process.stdout.read();print(output)
path=Path('work/camera/prototype-runs')/('native-memory-'+str(time.time_ns())+'.json')
path.write_text(json.dumps(dict(exitcode=process.returncode,loaded_parent_modules=modules,child_pid_file=str(child_file),samples=list(rows),renderer_output=output,scope='Parent and preparation process working set/private bytes where available; GPU allocation excluded, finite interval only.'),indent=2));print(path)
raise SystemExit(process.returncode)
