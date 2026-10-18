import ctypes as C,json
from pathlib import Path
p=Path(__file__).parent;d=C.CDLL(str((p/'owned-native-deadline-present-candidate.dll').resolve()));stub=C.CDLL(str((p/'native-present-bridge-test-stub.dll').resolve()))
P=C.c_void_p;U=C.c_uint64
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
d.nf_owned_handoff_pause.argtypes=[P,C.c_uint];d.nf_owned_handoff_close.argtypes=[P];d.nf_owned_handoff_destroy.argtypes=[P]
f=d.nf_owned_native_deadline_present;f.argtypes=[P,U,U,U,U,U,C.c_double,U,P,P,P,P,P]
q=d.nf_owned_handoff_create(1);checks=[]
def run(label,status,expected,generation=1,index=0):
 stub.test_set(status);out=(U*8)(*[123]*8);wait=(U*4)();stages=(U*7)();native_status=C.c_int()
 result=f(q,1,generation,10,11,index,.5,0,C.cast(stub.test_present,P),out,wait,stages,C.byref(native_status))
 assert result==expected,(label,result)
 if expected==1:assert out[0]==1 and out[1]==generation and out[4]==index and stub.test_calls()==1 and native_status.value==0
 else:assert list(out)==[123]*8
 checks.append(dict(label=label,result=result,calls=stub.test_calls(),native_status=native_status.value))
try:
 run('occluded_no_commit',3,-1);run('failed_no_commit',4,-1)
 run('success',0,1);run('duplicate_order_rejected',0,-1)
 assert checks[-1]['calls']==0
 assert d.nf_owned_handoff_pause(q,1)==1
 run('paused_retired',0,0);assert checks[-1]['calls']==0
 assert d.nf_owned_handoff_pause(q,0)==1
 run('stale_generation',0,0);assert checks[-1]['calls']==0
 run('resumed_next_slot',0,1,generation=3,index=1)
 d.nf_owned_handoff_close(q);run('closed',0,0,generation=3,index=2);assert checks[-1]['calls']==0
finally:d.nf_owned_handoff_destroy(q)
result=dict(result='PASS_NATIVE_DEADLINE_PRESENT_LIFECYCLE',checks=checks,scope='Native C test stub verifies commit/order/occlusion/pause/generation/close; no graphics pixels, live cancellation race or cadence verified.')
(p/'prototype-runs/native-deadline-present-lifecycle.json').write_text(json.dumps(result,indent=2));print(result['result'])
