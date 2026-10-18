import runpy
from live_native_batch_candidate import NativeBatchWorker
original=NativeBatchWorker.__init__
def timestamps(self,*args,**kwargs):
 self.gpu_timestamp_probe_enabled=True
 original(self,*args,**kwargs)
NativeBatchWorker.__init__=timestamps
close=NativeBatchWorker.close
def verified_close(self):
 close(self)
 rows=[x for x in self.results if x.get('native_batch_candidate')]
 assert rows and all(x['gpu_timestamp_result']==0 and x['gpu_timestamp_probe'][0]==1 and x['gpu_timestamp_probe'][6]==0 for x in rows)
 assert sum(x['gpu_timestamp_probe'][2] for x in rows)>0
 assert self.shutdown_evidence['gpu_queries_after_close']==0
NativeBatchWorker.close=verified_close
runpy.run_path('work/camera/test_native_batch_worker_reload.py',run_name='__main__')
