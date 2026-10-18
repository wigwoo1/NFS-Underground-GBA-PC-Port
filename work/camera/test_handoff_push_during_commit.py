import ctypes as C,threading,struct
from pathlib import Path
d=C.CDLL(str(Path('work/camera/owned-frame-handoff.dll').resolve()));P=C.c_void_p;U=C.c_uint64;Callback=C.CFUNCTYPE(C.c_int,P)
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P;d.nf_owned_handoff_push.argtypes=[P,P,C.c_size_t];d.nf_owned_handoff_commit_token.argtypes=[P,U,U,Callback,P];d.nf_owned_handoff_destroy.argtypes=[P]
raw=Path('work/camera/motion-actual-scanline-assets/8758-native-complete-frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];q=d.nf_owned_handoff_create(epoch);entered=threading.Event();release=threading.Event();pushed=threading.Event();results=[]
@Callback
def commit(_):
 entered.set();return int(release.wait(5))
def push():
 results.append(d.nf_owned_handoff_push(q,raw,len(raw)));pushed.set()
t=threading.Thread(target=lambda:results.append(d.nf_owned_handoff_commit_token(q,epoch,1,commit,None)));t.start();assert entered.wait(5);p=threading.Thread(target=push);p.start()
try:assert pushed.wait(2),'Producer blocked behind presentation callback'
finally:release.set();t.join(5);p.join(5);d.nf_owned_handoff_destroy(q)
assert results==[1,1],results
print('PASS producer push completes while presentation callback remains active')
