import os
import ctypes as C,json,time
from pathlib import Path
d=C.CDLL(str((Path(__file__).parent/os.environ.get('NFSUG_RETIREMENT_TEST_DLL','owned-draw-commit-retirement-candidate.dll')).resolve()))
d.nf_owned_handoff_create.argtypes=[C.c_uint64];d.nf_owned_handoff_create.restype=C.c_void_p
for name in ('destroy','close'):getattr(d,'nf_owned_handoff_'+name).argtypes=[C.c_void_p]
d.nf_owned_handoff_pause.argtypes=[C.c_void_p,C.c_uint];d.nf_owned_handoff_epoch.argtypes=[C.c_void_p,C.c_uint64]
d.nf_owned_handoff_last_sample.argtypes=[C.c_void_p,C.c_void_p]
cb=C.CFUNCTYPE(C.c_int,C.c_void_p);calls=[]
@cb
def present(ctx):calls.append(1);return 1
commit=d.nf_owned_handoff_commit_sample;commit.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_double,cb,C.c_void_p,C.c_void_p]
retire=d.nf_owned_handoff_retire_expired;retire.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_void_p,C.c_size_t]
q=d.nf_owned_handoff_create(2);bind=d.nf_owned_handoff_bind_display_clock;bind.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64]
origin=time.perf_counter_ns()-1000000000;checks=0
assert bind(q,2,1,origin)==1 and bind(q,2,1,origin)==1 and bind(q,2,1,origin+1)==-1
assert bind(q,2,9,origin)==0
try:
 out=(C.c_uint64*8)();assert commit(q,2,1,100,104,0,.5,present,None,out)==1;saved=list(out)
 def retirement(first,last,expected,g=1,o=origin,size=64):
  global checks
  a=(C.c_uint64*8)(*([123]*8));before=len(calls);rc=retire(q,2,g,first,last,o,a,size);assert rc==expected and len(calls)==before
  if expected!=1:assert list(a)==[123]*8
  checks+=1;return list(a)
 row=retirement(1,3,1);assert row[6:]==[3,1]
 last=(C.c_uint64*8)();assert d.nf_owned_handoff_last_sample(q,last)==1 and list(last)==saved
 retirement(1,3,-1);retirement(5,6,-1);retirement(4,4,-1,o=time.perf_counter_ns()+1000000000)
 for size in (0,8,63,65):retirement(4,4,-1,size=size)
 assert retire(q,2,1,4,4,origin,None,64)==-1
 assert commit(q,2,1,100,104,5,.5,present,None,out)==-1
 assert commit(q,2,1,100,104,4,.5,present,None,out)==1 and out[7]==2
 assert d.nf_owned_handoff_pause(q,1)==1;retirement(5,5,0)
 assert d.nf_owned_handoff_pause(q,0)==1;retirement(5,5,0)
 retirement(5,5,-1,g=3)
 assert bind(q,2,3,origin)==1
 row=retirement(5,6,1,g=3);assert row[6:]==[5,2]
 assert commit(q,2,3,100,104,7,.5,present,None,out)==1 and out[7]==3
 assert d.nf_owned_handoff_epoch(q,3)==1
 assert d.nf_owned_handoff_last_sample(q,last)==0
 assert commit(q,3,4,100,104,0,.5,present,None,out)==1 and out[7]==1
 d.nf_owned_handoff_close(q);a=(C.c_uint64*8)(*([123]*8));assert retire(q,3,4,1,1,origin,a,64)==0 and list(a)==[123]*8
finally:d.nf_owned_handoff_destroy(q)
out=dict(library=d._name,result='PASS_ISOLATED_EXPIRED_SLOT_ACCOUNTING',retirement_checks=checks,presentation_callbacks=len(calls),scope='Actual isolated native API. Retirement does not call present or mutate last successful sample/serial. Exact expired ordering, future/size/null/stale/pause/closed guards, subsequent presentation and epoch reset verified. No live integration, dropped-slot cadence or gameplay qualification.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/start-floor-first-live-20261010/retirement-component.json').write_text(json.dumps(out,indent=2));print(out)



