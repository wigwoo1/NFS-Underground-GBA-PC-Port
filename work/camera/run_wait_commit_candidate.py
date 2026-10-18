import runpy
import live_owned_gpu_worker
from live_wait_commit_candidate import WaitCommitWorker
if __name__=='__main__':
 live_owned_gpu_worker.LiveOwnedGPUWorker=WaitCommitWorker
 runpy.run_path('work/camera/run_owned_native_prototype.py',run_name='__main__')
