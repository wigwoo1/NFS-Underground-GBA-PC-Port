"""Opt-in launch of candidate; preserves standard host arguments."""
import runpy
import live_owned_gpu_worker
from live_native_transaction_candidate import NativeTransactionWorker
if __name__=='__main__':
 live_owned_gpu_worker.LiveOwnedGPUWorker=NativeTransactionWorker
 runpy.run_path('work/camera/run_owned_native_prototype.py',run_name='__main__')
