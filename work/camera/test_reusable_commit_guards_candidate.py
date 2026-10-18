import threading,json
from pathlib import Path
from concurrent.futures import Future
from owned_native_source_reusable_commit_adapter_candidate import NativeSourceCommitAdapter
class Worker:
 def __init__(self):self.aborts=0;self.fail=False
 def done(self,value):f=Future();f.set_result(value);return f
 def prepare(self,*args):
  if self.fail:raise ValueError('prepare failed')
  return self.done(dict(ok=True))
 def present(self,*args):return self.done(dict(status=0))
 def abort(self,*args):self.aborts+=1;return self.done(None)
w=Worker();a=NativeSourceCommitAdapter(w,None);args=(object(),1,1,1,2,0,.5,0)
def native(*x):
 rc=x[8](None)
 if rc:return 0
 return x[10](None)
a.f=native;ids=tuple(map(id,(a.draw_callback,a.present_callback,a.output,a.wait_output,a.stage_output)))
for i in range(20):assert a.run(*args)['native_result']==1
assert ids==tuple(map(id,(a.draw_callback,a.present_callback,a.output,a.wait_output,a.stage_output)))
a.f=lambda *x: (x[8](None),0)[1]
assert a.run(*args)['native_result']==0 and w.aborts==1
w.fail=True
try:a.run(*args)
except ValueError:pass
else:raise AssertionError('lost prepare error')
w.fail=False;a.f=native
try:a.run(*args,on_prepared=lambda:a.run(*args))
except RuntimeError as e:assert 'reentrant' in str(e)
else:raise AssertionError('reentry accepted')
assert w.aborts==2 and not a.busy and a.active_args is None and a.active_state is None
errors=[]
def foreign():
 try:a.run(*args)
 except RuntimeError as e:errors.append(str(e))
t=threading.Thread(target=foreign);t.start();t.join();assert errors==['Adapter owner thread mismatch']
assert a.run(*args)['native_result']==1
out=dict(result='PASS_REUSABLE_COMMIT_GUARDS',stable_callbacks_and_buffers=True,cancel_aborts=True,exceptions_propagate=True,reentry_rejected=True,wrong_owner_rejected=True,recovers_after_errors=True,scope='Synthetic native callback driver; live identity verified separately.')
Path('work/camera/prototype-runs/reusable-commit-guards-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
