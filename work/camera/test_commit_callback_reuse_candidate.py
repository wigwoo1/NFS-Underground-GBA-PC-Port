import threading,weakref,gc,json
from concurrent.futures import Future
from pathlib import Path
from owned_commit_callback_reuse_install_candidate import ReusedAdapter
class Worker:
 def __init__(self):self.fail=None;self.calls=[]
 def invoke(self,name):
  self.calls.append(name);f=Future()
  if self.fail==name:f.set_exception(ValueError(name))
  else:f.set_result({'status':0})
  return f
 def prepare(self,*args):return self.invoke('prepare')
 def present(self,*args):return self.invoke('present')
 def abort(self,*args):return self.invoke('abort')
w=Worker();a=ReusedAdapter.__new__(ReusedAdapter);a.worker=w;a.owner=None;a._current=None;a._thread=threading.get_ident();a._install_callbacks()
def native(*args):
 if args[8](None):return 0
 return args[10](None)
a.f=native;identities=(id(a._draw_callback),id(a._present_callback))
for i in range(100):assert a.run(object(),1,1,1,2,i,.5,0)['native_result']==1 and a._current is None
assert identities==(id(a._draw_callback),id(a._present_callback))
for failure in ('prepare','present'):
 w.fail=failure
 try:a.run(object(),1,1,1,2,101,.5,0)
 except ValueError as e:assert str(e)==failure
 else:raise AssertionError('Failure hidden')
 assert a._current is None
assert w.calls[-1]=='abort';w.fail=None
try:a.run(object(),1,1,1,2,102,.5,0,on_prepared=lambda:a.run(object(),1,1,1,2,103,.5,0))
except RuntimeError:pass
else:raise AssertionError('Re-entry accepted')
assert a._current is None
errors=[]
def foreign():
 try:a.run(object(),1,1,1,2,104,.5,0)
 except RuntimeError:errors.append(True)
t=threading.Thread(target=foreign);t.start();t.join();assert errors==[True]
b=ReusedAdapter.__new__(ReusedAdapter);b.worker=Worker();b.owner=None;b._current=None;b._thread=threading.get_ident();b._install_callbacks();b.f=native;assert b.run(object(),1,1,1,2,0,.5,0)["native_result"]==1
ref=weakref.ref(b);del b;assert ref() is None
ref_failed=weakref.ref(a);del a;gc.collect();assert ref_failed() is None
Path('work/camera/prototype-runs/commit-callback-reuse-component-20261009.json').write_text(json.dumps(dict(passed=True,calls=100,failures=['prepare','present','reentry','foreignthread'],adapter_releases_without_gc=True,scope='Mockworker/nativeinvoker; actualnativehandoff/live4K qualification remains.'),indent=2));print('PASS_REUSED_COMMIT_CALLBACK_LIFECYCLE')

