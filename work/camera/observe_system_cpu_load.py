"""Read-only system CPU busy samples; does not attribute processes or GPU load."""
import ctypes as C,time,json
from pathlib import Path
from ctypes import wintypes as W
class FT(C.Structure):_fields_=[('low',W.DWORD),('high',W.DWORD)]
k=C.WinDLL('kernel32',use_last_error=True);k.GetSystemTimes.argtypes=[C.POINTER(FT)]*3
rows=[];previous=None
for _ in range(55):
 f=[FT() for i in range(3)];assert k.GetSystemTimes(*[C.byref(x) for x in f]);v=[(x.high<<32)|x.low for x in f];now=time.perf_counter_ns()
 if previous:
  old,t=previous;idle=v[0]-old[0];total=v[1]+v[2]-old[1]-old[2];rows.append(dict(begin_ns=t,end_ns=now,system_cpu_busy_fraction=1-idle/total if total else None))
 previous=(v,now);time.sleep(1)
p=Path('work/camera/prototype-runs')/('system-cpu-load-'+str(time.time_ns())+'.json');p.write_text(json.dumps(dict(samples=rows,scope='Whole-system CPU average only; cannot exclude single-core bottleneck, scheduling delays, or GPU load'),indent=2));print(p)
