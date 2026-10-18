import runpy,json,time
from pathlib import Path
from live_native_batch_candidate import NativeBatchWorker
NativeBatchWorker.batch_bridge_name='owned-batch-queued-candidate.dll'
NativeBatchWorker.gpu_ready_enabled=False
NativeBatchWorker.gpu_queued_enabled=True
NativeBatchWorker.queued_ordered_gpu=True
NativeBatchWorker.queued_draw_probe_enabled=True
NativeBatchWorker.ready_adapter_name='owned-gpu-ready-bounded-candidate.dll'
NativeBatchWorker.gpu_renderer_name='owned-sky-queued-palette-candidate.dll'
def after_close(self,gpu):
 import ctypes as C
 gpu.nf_owned_gpu_pool_stats.argtypes=[C.c_void_p];gpu.nf_owned_gpu_pool_fences.argtypes=[C.c_void_p]
 targets=(C.c_uint64*5)();fences=(C.c_uint64*4)()
 assert gpu.nf_owned_gpu_pool_stats(targets)==0 and list(targets)==[0]*5
 assert gpu.nf_owned_gpu_pool_fences(fences)==0 and fences[0]==fences[1] and fences[3]==0
 path=Path('work/camera/prototype-runs')/('pool-cleanup-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(targets=list(targets),fences=list(fences)),indent=2));print(path)
NativeBatchWorker._after_gpu_close=after_close
runpy.run_path('work/camera/run_native_batch_candidate.py',run_name='__main__')
