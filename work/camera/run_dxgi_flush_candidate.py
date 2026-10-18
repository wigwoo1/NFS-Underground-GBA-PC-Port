import runpy,json,time,ctypes as C
from pathlib import Path
from live_native_batch_candidate import NativeBatchWorker
NativeBatchWorker.dxgi_bridge_name='owned-dx-flush-bridge.dll'
NativeBatchWorker.dxgi_scene_timer_enabled=True
try:runpy.run_path('work/camera/run_dxgi_batch_candidate.py',run_name='__main__')
finally:
 d=C.CDLL(str(Path('work/camera/owned-dx-flush-bridge.dll').resolve()));d.nf_dx_phase_read.argtypes=[C.c_uint,C.c_void_p];rows=[]
 for i in range(d.nf_dx_phase_count()):
  out=(C.c_uint64*18)();assert d.nf_dx_phase_read(i,out)==1;rows.append(list(out))
 gpu=[];d.nf_dx_gpu_read.argtypes=[C.c_uint,C.c_void_p]
 for i in range(d.nf_dx_gpu_count()):
  out=(C.c_uint64*4)();assert d.nf_dx_gpu_read(i,out)==1;gpu.append(list(out))
 cleanup=(C.c_uint64*4)();d.nf_dx_gpu_cleanup.argtypes=[C.c_void_p];assert d.nf_dx_gpu_cleanup(cleanup)==1
 scene=[];d.nf_dx_scene_read.argtypes=[C.c_uint,C.c_void_p]
 for i in range(d.nf_dx_scene_count()):
  out=(C.c_uint64*3)();assert d.nf_dx_scene_read(i,out)==1;scene.append(list(out))
 scene_cleanup=(C.c_uint64*5)();d.nf_dx_scene_cleanup.argtypes=[C.c_void_p];assert d.nf_dx_scene_cleanup(scene_cleanup)==1
 path=Path('work/camera/prototype-runs')/('dxgi-phase-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(scene_gpu=scene,scene_cleanup=list(scene_cleanup),gpu_fields=['phase_identity','prior_scene_tail','blit_start','blit_end'], readiness_bits={'before_lock':1,'after_lock':2,'before_unlock':4,'after_unlock':8},gpu=gpu,gpu_skipped=d.nf_dx_gpu_skipped(),gpu_cleanup=list(cleanup),rows=rows,dropped=d.nf_dx_phase_dropped(),fields=['entry','before_lock','after_lock','before_unlock','after_unlock','before_present','after_present','restored','frequency']),indent=2));print(path)
