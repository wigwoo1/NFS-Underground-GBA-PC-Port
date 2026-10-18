"""Atomic committed display metadata, failure/retirement and pause race."""
import ctypes as C,time,threading,struct,json
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P);d=C.CDLL(str(Path('work/camera/owned-frame-handoff.dll').resolve()))
for name,args,r in (('create',[U],P),('commit_sample',[P,U,U,U,U,U,C.c_double,CB,P,P],C.c_int),('last_sample',[P,P],C.c_int),('pause',[P,C.c_uint],C.c_int),('epoch',[P,U],C.c_int),('close',[P],None),('destroy',[P],None)):
 f=getattr(d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=r
q=d.nf_owned_handoff_create(7);assert q;calls=[];rows=[]
@CB
def success(ctx):calls.append(1);return 1
@CB
def failed(ctx):return 0
def commit(gen,index,callback=success,alpha=.5,epoch=7):
 out=(U*8)(*([123456]*8));before=list(out);r=d.nf_owned_handoff_commit_sample(q,epoch,gen,10,14,index,alpha,callback,None,out)
 if r!=1:assert list(out)==before
 else:rows.append(list(out))
 return r,list(out)
def snapshot(expected):
 out=(U*8)(*([654321]*8));r=d.nf_owned_handoff_last_sample(q,out);assert r==expected
 if not r:assert list(out)==[654321]*8
 return list(out)
try:
 snapshot(0);assert commit(1,20)[0]==1;first=snapshot(1);assert first[:5]==[7,1,10,14,20] and struct.unpack('<d',struct.pack('<Q',first[5]))[0]==.5 and first[6]>0 and first[7]==1
 for alpha in (-.1,1.1,float('nan'),float('inf')):assert commit(1,21,alpha=alpha)[0]==-1 and snapshot(1)==first
 assert commit(1,22)[0]==-1 and len(calls)==1
 assert commit(1,21,failed)[0]==-1 and snapshot(1)==first
 entered=threading.Event();release=threading.Event();results=[]
 @CB
 def held(ctx):entered.set();assert release.wait(5);return 1
 t=threading.Thread(target=lambda:results.append(commit(1,21,held)));t.start();assert entered.wait(1);assert snapshot(1)==first
 paused=[];pt=threading.Thread(target=lambda:paused.append(d.nf_owned_handoff_pause(q,1)));pt.start();time.sleep(.01);assert not paused and snapshot(1)==first
 release.set();t.join(5);pt.join(5);assert not t.is_alive() and not pt.is_alive() and results[0][0]==1 and paused==[1]
 latest=snapshot(1);assert latest[4]==21 and latest[7]==2 and latest[6]>=first[6]
 assert commit(1,22)[0]==0 and snapshot(1)==latest
 assert d.nf_owned_handoff_pause(q,0);assert commit(1,22)[0]==0;assert commit(3,22)[0]==1
 assert d.nf_owned_handoff_epoch(q,8);snapshot(0);assert commit(3,23)[0]==0;assert commit(4,0,epoch=8)[0]==1
 d.nf_owned_handoff_close(q);snapshot(0);assert commit(4,1,epoch=8)[0]==0
finally:d.nf_owned_handoff_destroy(q)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006');(cp/'tests.json').write_text(json.dumps({'result':'PASS','committed_rows':rows,'checks':['metadata only after successful callback','failure/invalid/order rejection no output mutation','concurrent pause sees atomically completed new sample','retired generation cannot publish','resume preserves index continuity','epoch reset removes old sample','closed rejects snapshot/commit'],'scope':'Native ownership/publication concurrency component with controlled callbacks; not GPU/scanout/gameplay proof'},indent=2));print('PASS atomic committed sample metadata',len(rows),'successful commits')
