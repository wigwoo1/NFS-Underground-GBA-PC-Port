"""Real QPC wait and concurrent token retirement; no GPU cadence claim."""
import ctypes as C,time,threading,json
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;d=C.CDLL(str(Path('work/camera/owned-frame-wait-profile-candidate.dll').resolve()))
for name,args,r in (('create',[U],P),('wait_token',[P,U,U,U,P],C.c_int),('pause',[P,C.c_uint],C.c_int),('epoch',[P,U],C.c_int),('close',[P],None),('destroy',[P],None)):
 f=getattr(d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=r
q=d.nf_owned_handoff_create(5);assert q;rows=[];profiles=[]
d.nf_wait_profile_read.argtypes=[P]
def wait(epoch,gen,target,expected):
 out=(U*4)();result=d.nf_owned_handoff_wait_token(q,epoch,gen,target,out);assert result==expected,(result,list(out));rows.append(list(out))
 if expected!=-1:
  profile=(U*12)();assert d.nf_wait_profile_read(profile)==1;assert list(profile)[:3]==[out[0],out[2],out[1]];assert profile[7]==out[3] and profile[5]<=profile[6];profiles.append(list(profile))
 return out
try:
 target=time.perf_counter_ns()+30000000;out=wait(5,1,target,1);assert out[2]>=target and out[3]>0
 out=wait(5,1,time.perf_counter_ns()-1000000,1);assert out[3]==0
 out=wait(5,1,time.perf_counter_ns()+3000000000,-1)
 wait(6,1,time.perf_counter_ns()+100000000,0);wait(5,2,time.perf_counter_ns()+100000000,0)
 result=[];target=time.perf_counter_ns()+500000000
 t=threading.Thread(target=lambda:result.append(wait(5,1,target,0)));t.start();time.sleep(.02);assert d.nf_owned_handoff_pause(q,1);t.join(1);assert not t.is_alive() and result and result[0][2]<target
 assert d.nf_owned_handoff_pause(q,0);wait(5,1,time.perf_counter_ns(),0);wait(5,3,time.perf_counter_ns(),1)
 assert d.nf_owned_handoff_epoch(q,6);wait(5,3,time.perf_counter_ns(),0);wait(6,4,time.perf_counter_ns(),1)
 d.nf_owned_handoff_close(q);wait(6,4,time.perf_counter_ns(),0)
finally:d.nf_owned_handoff_destroy(q)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wait-profile-lifecycle-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps({'result':'PASS','waits':rows,'profiles':profiles,'scope':'Actual original QPC deadline not early, expired fast path, bounded deadline validation, stale epoch/generation rejection, concurrent pause cancellation without presentation lock, resume/new epoch and closed rejection. No live60fps or hardware scanout claim'},indent=2));print('PASS native deadline/retirement',len(rows),'cases')
