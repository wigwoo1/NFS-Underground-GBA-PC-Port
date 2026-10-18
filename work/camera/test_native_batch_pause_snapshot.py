import ctypes as C,threading,json
from pathlib import Path
from owned_native_presentation_batch import BatchItem
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
d=C.CDLL(str(Path('work/camera/owned-batch-present-candidate.dll').resolve()));d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P;d.nf_owned_handoff_destroy.argtypes=[P]
f=d.nf_owned_handoff_batch;f.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P]
pause=d.nf_owned_handoff_pause_snapshot;pause.argtypes=[P,C.c_uint,P,P]
q=d.nf_owned_handoff_create(7);entered=threading.Event();release=threading.Event();calls=[];results=[]
@CB
def draw(ctx):
 calls.append(('draw',ctx))
 if ctx==2 and not release.is_set():entered.set();assert release.wait(3)
 return 0
@CB
def present(ctx):calls.append(('present',ctx));return 1
items=(BatchItem*3)(*[BatchItem(10,14,20+i,0,(i+1)/4,i+1,i+1) for i in range(3)])
samples=(U*24)(*([123]*24));waits=(U*12)();stages=(U*21)();completed=C.c_uint();snap=(U*8)();meta=(U*3)()
t=threading.Thread(target=lambda:results.append(f(q,7,1,items,3,draw,present,samples,waits,stages,C.byref(completed))))
try:
 t.start();assert entered.wait(3)
 assert pause(q,1,snap,meta)==1 and meta[0]==2 and meta[1]==1 and snap[4]==20 and snap[6]<=meta[2]
 paused_snapshot=list(snap);release.set();t.join(3);assert not t.is_alive() and results==[0] and completed.value==1
 assert list(samples)[:8]==paused_snapshot and list(samples)[8:]==[123]*16
 assert pause(q,0,snap,meta)==1 and meta[0]==3 and list(snap)==paused_snapshot
 suffix=(BatchItem*2)(items[1],items[2]);out=(U*16)();w=(U*8)();s=(U*14)();n=C.c_uint()
 assert f(q,7,meta[0],suffix,2,draw,present,out,w,s,C.byref(n))==1 and n.value==2 and [out[4],out[12]]==[21,22]
 assert [x[1] for x in calls if x[0]=='present']==[1,2,3]
finally:
 release.set();t.join(3);assert not t.is_alive();d.nf_owned_handoff_destroy(q)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-batch-pause-snapshot-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',committed_prefix=1,replayed_suffix=2,presented_indices=[20,21,22],scope='Concurrent native lifecycle and atomic committed snapshot with stand-in callbacks; live GPU/Python scene-chain integration not verified.'),indent=2));print('PASS atomic pause prefix snapshot and exact suffix replay')
