"""Run actual complete-scene reload with opt-in native notification FIFO."""
import runpy
from live_native_batch_candidate import NativeBatchWorker
original=NativeBatchWorker.__init__
def native_notifications(self,*args,**kwargs):
 kwargs['native_notification_queue']=True
 original(self,*args,**kwargs)
NativeBatchWorker.__init__=native_notifications
runpy.run_path('work/camera/test_native_batch_worker_reload.py',run_name='__main__')
