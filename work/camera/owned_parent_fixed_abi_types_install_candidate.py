"""Cache fixed parent ABI types; every invocation owns fresh private buffers."""
import ctypes as C,inspect,textwrap
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
from owned_uncovered_window_candidate import OwnedD3DConsumer
import owned_native_source_segmented_release_worker_candidate as worker
Commit8=C.c_uint64*8;Wait4=C.c_uint64*4;Stages7=C.c_uint64*7;Present27=C.c_uint64*27;Input4=C.c_uint32*4
TYPES=dict(Commit8=Commit8,Wait4=Wait4,Stages7=Stages7,Present27=Present27,Input4=Input4)
def replace(method,pairs):
 source=textwrap.dedent(inspect.getsource(method))
 for old,new in pairs:
  assert source.count(old)==1,(method.__qualname__,old)
  source=source.replace(old,new)
 ns=dict(method.__globals__,**TYPES);exec(compile(source,'parent-fixed-abi-types','exec'),ns);return ns[method.__name__]
NativeSourceCommitAdapter.run=replace(NativeSourceCommitAdapter.run,[('(U*8)(*[123]*8)','Commit8(*[123]*8)'),('(U*4)()','Wait4()'),('(U*7)()','Stages7()')])
OwnedD3DConsumer.present=replace(OwnedD3DConsumer.present,[('(C.c_uint64*27)()','Present27()')])
worker.NativeSourceWorker._poll_input=replace(worker.NativeSourceWorker._poll_input,[('(C.c_uint32*4)()','Input4()')])
