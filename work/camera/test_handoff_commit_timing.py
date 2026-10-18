import ctypes as C,time,json,threading
from pathlib import Path
d=C.CDLL(str(Path('work/camera/owned-handoff-timing-candidate.dll').resolve()));P=C.c_void_p;U=C.c_uint64;Callback=C.CFUNCTYPE(C.c_int,P)
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
d.nf_owned_handoff_commit_token_timed.argtypes=[P,U,U,Callback,P,C.POINTER(U)]
d.nf_owned_handoff_pause.argtypes=[P,C.c_uint];d.nf_owned_handoff_close.argtypes=[P];d.nf_owned_handoff_destroy.argtypes=[P]
q=d.nf_owned_handoff_create(1);assert q;calls=[]
@Callback
def callback(ctx):calls.append(1);time.sleep(.02);return 1
@Callback
def failed(ctx):return 0
a=(U*6)();rows=[]
try:
 assert d.nf_owned_handoff_commit_token_timed(q,1,1,callback,None,a)==1;assert a[5]>0 and a[3]/a[5]>=.015 and a[4]>=sum(a[:4]);rows.append(list(a))
 assert d.nf_owned_handoff_commit_token_timed(q,2,1,callback,None,a)==0
 assert d.nf_owned_handoff_commit_token_timed(q,1,2,callback,None,a)==0
 assert d.nf_owned_handoff_commit_token_timed(q,1,1,failed,None,a)==-1
 assert d.nf_owned_handoff_pause(q,1)==1
 assert d.nf_owned_handoff_commit_token_timed(q,1,1,callback,None,a)==0
 assert d.nf_owned_handoff_pause(q,0)==1
 assert d.nf_owned_handoff_commit_token_timed(q,1,1,callback,None,a)==0
 assert d.nf_owned_handoff_commit_token_timed(q,1,3,callback,None,a)==1;rows.append(list(a))
 entered=threading.Event();release=threading.Event()
 @Callback
 def held(ctx):entered.set();assert release.wait(2);return 1
 holder_output=(U*6)()
 def hold():assert d.nf_owned_handoff_commit_token_timed(q,1,3,held,None,holder_output)==1
 holder=threading.Thread(target=hold);holder.start();assert entered.wait(2)
 def unlock():time.sleep(.04);release.set()
 unlocker=threading.Thread(target=unlock);unlocker.start()
 assert d.nf_owned_handoff_commit_token_timed(q,1,3,failed,None,a)==-1
 assert a[0]/a[5]>=.02;rows.append(list(a));holder.join(2);unlocker.join(2);assert not holder.is_alive()
 d.nf_owned_handoff_close(q);assert d.nf_owned_handoff_commit_token_timed(q,1,3,callback,None,a)==0;assert len(calls)==2
 out=dict(result='PASS_TIMED_COMMIT_TOKEN',callback_calls=len(calls),ticks=rows,scope='actual native callback duration and pause/epoch/generation/failure/close validation')
 Path('work/camera/handoff-commit-timing-tests.json').write_text(json.dumps(out,indent=2));print(out)
finally:d.nf_owned_handoff_destroy(q)
