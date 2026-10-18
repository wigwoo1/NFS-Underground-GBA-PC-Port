"""Actual current native clock commit ordering before any late-slot policy change."""
import ctypes as C,json
from pathlib import Path
base=Path(__file__).parent;d=C.CDLL(str((base/'owned-draw-commit-integer-clock-candidate.dll').resolve()))
d.nf_owned_handoff_create.argtypes=[C.c_uint64];d.nf_owned_handoff_create.restype=C.c_void_p
d.nf_owned_handoff_destroy.argtypes=[C.c_void_p];d.nf_owned_handoff_pause.argtypes=[C.c_void_p,C.c_uint]
callback=C.CFUNCTYPE(C.c_int,C.c_void_p);calls=[]
@callback
def present(ctx):calls.append(1);return 1
f=d.nf_owned_handoff_commit_sample;f.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_double,callback,C.c_void_p,C.c_void_p]
q=d.nf_owned_handoff_create(2);assert q;checks=[]
def commit(g,index,expected,callback_expected):
 before=len(calls);out=(C.c_uint64*8)(*([123]*8));rc=f(q,2,g,100,104,index,.5,present,None,out)
 assert rc==expected and len(calls)-before==callback_expected
 if expected!=1:assert list(out)==[123]*8
 else:assert list(out[:5])==[2,g,100,104,index]
 checks.append(dict(generation=g,index=index,result=rc,present_calls=len(calls)-before))
try:
 commit(1,0,1,1)
 commit(1,2,-1,0)
 commit(1,0,-1,0)
 commit(1,1,1,1)
 assert d.nf_owned_handoff_pause(q,1)==1
 commit(1,2,0,0)
 assert d.nf_owned_handoff_pause(q,0)==1
 commit(1,2,0,0)
 commit(3,5,-1,0)
 commit(3,2,1,1)
 commit(3,3,1,1)
finally:d.nf_owned_handoff_destroy(q)
out=dict(result='PASS_NATIVE_CONTIGUOUS_INDEX_AND_GENERATION_GUARDS',checks=checks,scope='Actual current integer-clock authority: gaps/duplicates/stale generations reject without callback or publication; consecutive indices commit; pause/resume retains consecutive-index obligation. No game timing, GPU pixel or cadence qualification.')
path=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/start-floor-first-live-20261010/commit-order-guards.json');path.write_text(json.dumps(out,indent=2));print(out['result'],len(checks),'checks')

