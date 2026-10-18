from pathlib import Path
import ctypes as C,struct,json,threading
p=Path('work/camera');d=C.CDLL(str((p/'owned-handoff-copy-candidate.dll').resolve()));P=C.c_void_p;U=C.c_uint64;Z=C.c_size_t;Callback=C.CFUNCTYPE(C.c_int,P)
for name,args,result in [('create',[U],P),('push',[P,P,Z],C.c_int),('pop_token',[P,P,P],P),('pause',[P,C.c_uint],C.c_int),('commit_token',[P,U,U,Callback,P],C.c_int),('destroy',[P],None)]:
 f=getattr(d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=result
d.nf_owned_frame_free.argtypes=[P]
raw=(p/'motion-actual-scanline-assets/8758-native-complete-frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];q=d.nf_owned_handoff_create(epoch);calls=[]
@Callback
def present(ctx):calls.append(1);return 1
assert d.nf_owned_handoff_push(q,raw,len(raw));size=Z();token=U();owner=d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(token));assert owner
assert d.nf_owned_handoff_push(q,raw,len(raw));assert d.nf_owned_handoff_pause(q,1);assert not d.nf_owned_handoff_push(q,raw,len(raw));assert d.nf_owned_handoff_commit_token(q,epoch,token.value,present,None)==0
assert C.string_at(owner,size.value)==raw;assert d.nf_owned_handoff_pause(q,0);assert d.nf_owned_handoff_commit_token(q,epoch,token.value,present,None)==0
assert not d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(token));d.nf_owned_frame_free(owner)
assert d.nf_owned_handoff_push(q,raw,len(raw));owner=d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(token));assert owner;assert d.nf_owned_handoff_commit_token(q,epoch,token.value,present,None)==1
# Actual overlapping pause waits for an active serialized presentation callback.
entered=threading.Event();release=threading.Event();paused=threading.Event();results=[]
@Callback
def blocking(ctx):entered.set();assert release.wait(5);return 1
t=threading.Thread(target=lambda:results.append(d.nf_owned_handoff_commit_token(q,epoch,token.value,blocking,None)));t.start();assert entered.wait(5)
u=threading.Thread(target=lambda:(d.nf_owned_handoff_pause(q,1),paused.set()));u.start();assert not paused.wait(.05);release.set();t.join(5);u.join(5);assert results==[1] and paused.is_set();assert d.nf_owned_handoff_commit_token(q,epoch,token.value,present,None)==0
d.nf_owned_frame_free(owner);d.nf_owned_handoff_destroy(q)
r=dict(result='PASS_OWNED_HANDOFF_PAUSE_GENERATIONS',retired_pending=True,popped_memory_preserved=True,prepause_tokens_rejected_after_resume=True,concurrent_pause_serialized_with_commit=True,scope='Native handoff lifecycle only; original simulation pause/resume clock routing not yet integrated.')
(p/'owned-handoff-pause-tests.json').write_text(json.dumps(r,indent=2));print(r)
