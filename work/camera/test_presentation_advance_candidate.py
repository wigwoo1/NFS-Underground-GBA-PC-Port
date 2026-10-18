import ctypes as C,json,hashlib,shutil
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
d=C.CDLL(str(Path('work/camera/owned-presentation-advance-candidate.dll').resolve()))
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
args=[P,U,U,U,U,U,C.c_double,CB,P,P]
d.nf_owned_handoff_commit_sample.argtypes=args
d.nf_owned_handoff_commit_sample_advance.argtypes=args+[P,U,P]
d.nf_owned_handoff_pause.argtypes=[P,C.c_uint];d.nf_owned_handoff_close.argtypes=[P];d.nf_owned_handoff_destroy.argtypes=[P];d.nf_owned_handoff_last_sample.argtypes=[P,P]
q=d.nf_owned_handoff_create(7);assert q;out=(U*8)();audit=(U*2)(777,888);calls=[]
@CB
def good(ctx):calls.append('good');return 1
@CB
def bad(ctx):calls.append('bad');return 0
checks=[]
def advance(index,previous,callback=good,generation=1):return d.nf_owned_handoff_commit_sample_advance(q,7,generation,10,15,index,.5,callback,None,out,None,previous,audit)
def last():
 x=(U*8)();assert d.nf_owned_handoff_last_sample(q,x)==1;return list(x)
try:
 assert advance(14,10)==-1 and not calls;checks.append('no uninitialized advancement')
 assert d.nf_owned_handoff_commit_sample(q,7,1,10,15,10,.5,good,None,out)==1
 before=last();assert advance(14,9)==-1 and last()==before;checks.append('stale previous rejected')
 assert advance(14,10,bad)==-1 and last()==before and list(audit)==[777,888];checks.append('failed callback leaves publication/audit unchanged')
 assert advance(14,10)==1 and list(audit)==[10,3] and last()[4]==14 and last()[7]==2;checks.append('skipped slots exact and serial advances once')
 assert d.nf_owned_handoff_commit_sample(q,7,1,10,15,16,.5,good,None,out)==-1
 assert d.nf_owned_handoff_commit_sample(q,7,1,10,15,15,.5,good,None,out)==1;checks.append('strict API remains consecutive')
 before=last();assert advance(15,15)==-1 and advance(14,15)==-1 and last()==before;checks.append('duplicate/backward rejected')
 assert d.nf_owned_handoff_pause(q,1)==1
 n=len(calls);assert advance(20,15)==0 and len(calls)==n
 assert d.nf_owned_handoff_pause(q,0)==1
 assert advance(20,15)==0 and len(calls)==n;checks.append('pause/resume stale generation cannot present')
 assert advance(20,15,generation=3)==1 and list(audit)==[15,4];checks.append('fresh generation explicit advancement')
 d.nf_owned_handoff_close(q);n=len(calls);assert advance(22,20,generation=3)==0 and len(calls)==n;checks.append('closed authority rejects callback')
finally:d.nf_owned_handoff_destroy(q)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/presentation-advance-component-20261007');cp.mkdir(exist_ok=True)
for name in ('owned_presentation_advance_candidate.c','owned_frame_handoff.c','test_presentation_advance_candidate.py'):shutil.copy2(Path('work/camera')/name,cp/name)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Separate native DLL component explicit previous-index advancement, callback/lifecycle atomicity. Not integrated live scheduling or60fps proof.'),indent=2));print(json.dumps(checks))
