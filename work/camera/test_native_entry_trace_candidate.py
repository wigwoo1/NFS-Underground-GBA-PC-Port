import ctypes as C,json,time
from pathlib import Path
from concurrent.futures import Future
from owned_native_source_entry_trace_adapter_candidate import NativeSourceCommitAdapter,P,U
class Worker:
 def prepare(self,*args):f=Future();f.set_result(dict(publication=[1,1,0]));return f
 def present(self,*args):f=Future();f.set_result(dict(status=0));return f
 def abort(self,*args):f=Future();f.set_result(None);return f
p=Path('work/camera');d=C.CDLL(str((p/'owned-draw-entry-trace-candidate.dll').resolve()));d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P;d.nf_owned_handoff_destroy.argtypes=[P];d.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
owner=d.nf_owned_handoff_create(1);assert owner
try:
 adapter=NativeSourceCommitAdapter(Worker(),owner);row=adapter.run(None,1,1,10,14,0,.5,time.perf_counter_ns()+5000000)
 assert row['native_result']==1;t=row['native_entry_trace'];assert all(t[i]<=t[i+1] for i in range(8));assert row['transaction_begin_ns']<=t[0]<=t[3]<=row['callback_timing']['draw_begin_ns']<=row['callback_timing']['draw_end_ns']<=t[4];assert t[5]<=row['wait'][0]<=row['wait'][2]<=t[6]
 cancelled=adapter.run(None,1,1,10,14,1,.7,0,on_prepared=lambda:d.nf_owned_handoff_pause(owner,1));assert cancelled['native_result']==0
 out=dict(result='PASS_NATIVE_ENTRY_TRACE_SUCCESS_CANCEL_ORDER',trace=t,cancelled=cancelled['native_entry_trace'],scope='Synthetic callbacks verify ordering and pause cancellation, not live GPU/cadence.')
 (p/'prototype-runs/native-entry-trace-component-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
finally:d.nf_owned_handoff_destroy(owner)
