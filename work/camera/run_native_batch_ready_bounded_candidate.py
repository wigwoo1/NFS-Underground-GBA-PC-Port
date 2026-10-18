import runpy,json,time
from pathlib import Path
from live_native_batch_candidate import NativeBatchWorker
NativeBatchWorker.batch_bridge_name='owned-batch-ready-reuse-candidate.dll'
NativeBatchWorker.gpu_ready_enabled=True
NativeBatchWorker.ready_adapter_name='owned-gpu-ready-bounded-candidate.dll'
_original_close=NativeBatchWorker._before_gpu_close
def close(self):
 _original_close(self)
 path=Path('work/camera/prototype-runs')/('gpu-ready-cleanup-'+str(time.time_ns())+'.json');path.write_text(json.dumps({'resources':self.gpu_ready_shutdown},indent=2));print(path)
NativeBatchWorker._before_gpu_close=close
runpy.run_path('work/camera/run_native_batch_candidate.py',run_name='__main__')
