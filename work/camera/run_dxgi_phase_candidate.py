import runpy,json,time,ctypes as C
from pathlib import Path
from live_native_batch_candidate import NativeBatchWorker
NativeBatchWorker.dxgi_bridge_name='owned-dx-phase-bridge.dll'
try:runpy.run_path('work/camera/run_dxgi_batch_candidate.py',run_name='__main__')
finally:
 d=C.CDLL(str(Path('work/camera/owned-dx-phase-bridge.dll').resolve()));d.nf_dx_phase_read.argtypes=[C.c_uint,C.c_void_p];rows=[]
 for i in range(d.nf_dx_phase_count()):
  out=(C.c_uint64*9)();assert d.nf_dx_phase_read(i,out)==1;rows.append(list(out))
 path=Path('work/camera/prototype-runs')/('dxgi-phase-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=rows,dropped=d.nf_dx_phase_dropped(),fields=['entry','before_lock','after_lock','before_unlock','after_unlock','before_present','after_present','restored','frequency']),indent=2));print(path)
