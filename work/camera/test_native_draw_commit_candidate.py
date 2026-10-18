import ctypes as C,json
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
d=C.CDLL(str(Path('work/camera/owned-draw-commit-candidate.dll').resolve()))
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
d.nf_owned_handoff_destroy.argtypes=[P];d.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
f=d.nf_owned_handoff_draw_wait_commit_sample;f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
calls=[]
@CB
def draw(ctx):calls.append('draw');return 0
@CB
def present(ctx):calls.append('present');return 1
@CB
def bad_draw(ctx):calls.append('bad_draw');return 9
q=d.nf_owned_handoff_create(7)
@CB
def cancel_draw(ctx):calls.append('cancel_draw');assert d.nf_owned_handoff_pause(q,1);return 0
checks=[]
def run(label,callback=draw,gen=1,index=20,alpha=.5,expected=1,sequence=None):
 calls.clear();out=(U*8)(*([123]*8));wait=(U*4)();stages=(U*7)()
 result=f(q,7,gen,10,14,index,alpha,0,callback,None,present,None,out,wait,stages)
 assert result==expected,(label,result)
 assert calls==sequence,(label,calls)
 if result!=1:assert list(out)==[123]*8
 else:assert list(out)[:5]==[7,gen,10,14,index] and wait[2]>=wait[1] and all(a<=b for a,b in zip(stages,stages[1:]))
 checks.append(dict(case=label,result=result,calls=list(calls)))
try:
 run('success',sequence=['draw','present'])
 run('draw_failure',bad_draw,index=21,expected=-1,sequence=['bad_draw'])
 run('invalid_alpha',alpha=float('nan'),expected=-1,sequence=[])
 run('cancel_during_draw',cancel_draw,index=21,expected=0,sequence=['cancel_draw'])
 run('retired_token',index=21,expected=0,sequence=[])
 assert d.nf_owned_handoff_pause(q,0)
 run('resume',gen=3,index=21,sequence=['draw','present'])
finally:d.nf_owned_handoff_destroy(q)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-draw-commit-candidate-20261007');cp.mkdir(exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Native handoff transaction component with callback stand-ins; actual GPU integration and cadence not verified'),indent=2))
print('PASS native draw/wait/commit',checks)
