import ctypes as C,json
from pathlib import Path
from concurrent.futures import Future
import owned_native_transaction_adapter_install_candidate
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
class Worker:
 def __init__(self,mode):self.mode=mode;self.calls=[]
 def done(self,value=None,error=None):
  f=Future();f.set_exception(error) if error else f.set_result(value);return f
 def prepare(self,*args):
  self.calls.append(('prepare',args))
  return self.done({'publication':[2,1,7]},ValueError('prepare')) if self.mode=='prepare_error' else self.done({'publication':[2,1,7]})
 def commit_present(self,*args):
  self.calls.append(('commit',args))
  if self.mode=='job_error':return self.done(error=ValueError('job'))
  callback=0 if self.mode in ('cancel','invalid') else 1
  status=-2 if self.mode=='invalid' else (0 if self.mode=='cancel' else (-1 if self.mode=='batch_error' else 1))
  return self.done(dict(native_callback_count=callback,native_batch_result=38 if self.mode=='batch_error' else (0 if callback else -1),native_result=status,commit=[2,1,10,11,7,0,1,1],wait=[0,123,123,0],stages=[0]*7,presentation={'status':0} if callback else None))
 def abort(self,*args):self.calls.append(('abort',args));return self.done()
rows=[]
for mode in ('success','cancel','invalid','batch_error','prepare_error','job_error','on_prepared_error'):
 w=Worker(mode);a=NativeSourceCommitAdapter(w,1234)
 def notify():
  w.calls.append(('ready',()))
  if mode=='on_prepared_error':raise ValueError('ready')
 error=None
 try:r=a.run('private scene',2,1,10,11,7,.35,123,on_prepared=notify)
 except (ValueError,RuntimeError) as e:error=str(e)
 assert bool(error)==(mode not in ('success','cancel'))
 aborts=sum(x[0]=='abort' for x in w.calls)
 assert aborts==int(mode in ('cancel','invalid','job_error','on_prepared_error'))
 if mode not in ('prepare_error','on_prepared_error'):
  args=next(x[1] for x in w.calls if x[0]=='commit')
  assert args[1:]==(1234,2,1,10,11,7,.35,123) and args[0].value
 rows.append(dict(mode=mode,aborts=aborts,error=error))
out=dict(result='PASS_NATIVE_TRANSACTION_ADAPTER_FORWARDING_ABORT_ERRORS',rows=rows,scope='Mock worker only: exact real authority pointer and argument forwarding, prepare notification ordering, cancellation/error pending abort exactly once; callback-completed batch failure not double-aborted. Actual bridge/worker4K verified separately; live integration timing pending.')
Path('work/camera/prototype-runs/native-transaction-adapter-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
