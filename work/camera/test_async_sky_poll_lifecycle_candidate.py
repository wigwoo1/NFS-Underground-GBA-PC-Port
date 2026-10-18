import ctypes as C,json
from types import SimpleNamespace
from pathlib import Path
from owned_native_source_async_sky_roi_worker_candidate import NativeSourceWorker
class Function:
 def __init__(self):self.status=3;self.calls=[]
 def __call__(self,slot,identity,buf,size):self.calls.append((slot,identity,size));return self.status
w=object.__new__(NativeSourceWorker);w.async_records=[];w.async_pending={0:dict(epoch=2,generation=3,display_index=100)};w.async_not_ready=0;w.async_buffer=C.create_string_buffer(512*64*4)
f=Function();session=SimpleNamespace(consumer=SimpleNamespace(d=SimpleNamespace(nf_d3d_async_poll=f)))
w._poll_async(session);assert w.async_not_ready==1 and len(w.async_pending)==1 and not w.async_records
f.status=0;w._poll_async(session);assert not w.async_pending and len(w.async_records)==1 and w.async_records[0]['display_index']==100
w.async_pending[1]=dict(epoch=2,generation=3,display_index=101);f.status=2
try:w._poll_async(session)
except AssertionError:pass
else:raise AssertionError('GPU error swallowed')
assert len(w.async_pending)==1 and len(w.async_records)==1
out=dict(result='PASS_ASYNC_POLL_LIFECYCLE',not_ready_retains_identity=True,ready_consumes_once=True,gpu_error_preserves_unresolved_identity=True,scope='Synthetic worker poll state; native GPU identity/cleanup verified separately.')
Path('work/camera/prototype-runs/async-sky-poll-lifecycle-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
