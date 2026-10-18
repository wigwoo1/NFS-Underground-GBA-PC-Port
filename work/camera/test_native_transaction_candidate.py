import ctypes as C,json,threading
from pathlib import Path
p=Path(__file__).parent
d=C.CDLL(str((p/'owned-d3d-native-transaction-candidate.dll').resolve()))
a=C.CDLL(str((p/'owned-draw-commit-highres-candidate.dll').resolve()))
U=C.c_uint64;P=C.c_void_p
a.nf_owned_handoff_create.argtypes=[U];a.nf_owned_handoff_create.restype=P
a.nf_owned_handoff_destroy.argtypes=[P]
f=d.nf_d3d_native_transaction;f.argtypes=[P,P,P,U,U,U,U,U,C.c_double,U,P,C.c_size_t]
authority=C.cast(a.nf_owned_handoff_draw_wait_commit_sample,P)
owner=a.nf_owned_handoff_create(2);assert owner
out=(U*48)(*[123]*48)
def run(generation=1,window=1,size=C.sizeof(out),ptr=out,fn=authority):
 return f(fn,owner,window,2,generation,10,11,0,.5,0,ptr,size)
try:
 assert run()==-2 and list(out)==[123]*48
 assert d.nf_d3d_open()==0
 for kw in ({'size':0},{'size':C.sizeof(out)-8},{'size':C.sizeof(out)+8},{'ptr':None},{'fn':None},{'window':None}):
  assert run(**kw)==-2 and list(out)==[123]*48
 results=[]
 t=threading.Thread(target=lambda:results.append(run()));t.start();t.join(2)
 assert not t.is_alive() and results==[-2] and list(out)==[123]*48
 assert run(generation=999)==0
 assert out[46]==0 and C.c_int64(out[47]).value==-1 and list(out[:8])==[0]*8
 # Exact original authority invokes native callback once; wrong HWND fails pump.
 assert run()==-1 and out[46]==1 and out[47]==38 and list(out[:8])==[0]*8
 assert d.nf_d3d_close()==0
 out[:]=[123]*48
 assert run()==-2 and list(out)==[123]*48
finally:
 d.nf_d3d_close();a.nf_owned_handoff_destroy(owner)
result=dict(result='PASS_NATIVE_TRANSACTION_CANCEL_FAILURE_OWNER_GUARDS',scope='Actual authority generation cancellation; native presentation callback once on pump failure; no successful commit on failure; unopened/closed/null/extent/owner-thread guards. Actual window successful presentation and live worker integration remain unverified.')
Path('work/camera/prototype-runs/native-transaction-component-20261009.json').write_text(json.dumps(result,indent=2))
print(result)
