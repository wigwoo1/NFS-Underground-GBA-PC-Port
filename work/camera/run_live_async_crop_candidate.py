import sys,runpy,json,time,atexit
from pathlib import Path
import live_source_async_crop_candidate as diagnostic
sys.modules['live_source_batch_candidate']=diagnostic
instances=[];init=diagnostic.SourceBatchWorker.__init__
def tracked(self,*args,**kwargs):
 init(self,*args,**kwargs);instances.append(self)
diagnostic.SourceBatchWorker.__init__=tracked
def export():
 path=Path('work/camera/prototype-runs')/('async-sky-crops-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(reports=[getattr(x,'async_crop_report',None) for x in instances],errors=[getattr(x,'async_crop_error',None) for x in instances],scope='Asynchronous final-target crops, not physical scanout; missing close report is incomplete verification.'),indent=2));print(path)
atexit.register(export)
original=runpy.run_path
def redirect(path,*args,**kwargs):
 if path=='work/camera/run_queued_source_anchor_candidate.py':path='work/camera/run_queued_async_crop_candidate.py'
 return original(path,*args,**kwargs)
runpy.run_path=redirect
runpy.run_path('work/camera/run_source_compact_diagnostics_candidate.py',run_name='__main__')
