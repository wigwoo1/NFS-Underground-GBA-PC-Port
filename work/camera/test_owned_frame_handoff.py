from pathlib import Path
import ctypes as C,struct,threading,queue,json,hashlib
p=Path('work/camera');d=C.CDLL(str((p/'owned-frame-handoff.dll').resolve()));P=C.c_void_p;Z=C.c_size_t;U=C.c_uint64
for name,args,result in [('create',[U],P),('push',[P,P,Z],C.c_int),('pop',[P,P],P),('epoch',[P,U],C.c_int),('close',[P],None),('destroy',[P],None)]:
 f=getattr(d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=result
d.nf_owned_frame_free.argtypes=[P]
raws=[(p/f'motion-actual-scanline-assets/{r}-native-complete-frame.bin').read_bytes() for r in (8758,8762,8766,8769,8773,8776,8780)];epoch=struct.unpack_from('<Q',raws[0],24)[0];q=d.nf_owned_handoff_create(epoch);assert q
# Bounded capacity, source mutation, popped ownership across epoch retirement.
for raw in raws[:3]:assert d.nf_owned_handoff_push(q,raw,len(raw))
assert not d.nf_owned_handoff_push(q,raws[3],len(raws[3]))
n=Z();owner=d.nf_owned_handoff_pop(q,C.byref(n));assert C.string_at(owner,n.value)==raws[0]
assert d.nf_owned_handoff_epoch(q,epoch+1);assert C.string_at(owner,n.value)==raws[0];d.nf_owned_frame_free(owner);assert not d.nf_owned_handoff_pop(q,C.byref(n));assert not d.nf_owned_handoff_push(q,raws[0],len(raws[0]));d.nf_owned_handoff_destroy(q)
q=d.nf_owned_handoff_create(epoch);signals=queue.Queue(maxsize=1);results=[];errors=[]
def consumer():
 try:
  gpu=C.CDLL(str((p/'owned-world-gpu.dll').resolve()));gpu.nf_owned_gpu_render.argtypes=[P,Z,P,Z]
  for raw in raws:
   signals.get(timeout=30);n=Z();owner=d.nf_owned_handoff_pop(q,C.byref(n));assert owner
   try:
    assert C.string_at(owner,n.value)==raw
    rgb=C.create_string_buffer(3840*2160*3);assert gpu.nf_owned_gpu_render(owner,n.value,rgb,len(rgb))==0
    refresh=struct.unpack_from('<I',raw,4)[0];reference=(p/f'owned-timed-{refresh}.ppm').read_bytes().split(b'\n',3)[3];assert rgb.raw==reference
    results.append(dict(refresh=refresh,sha256=hashlib.sha256(rgb.raw).hexdigest()))
   finally:d.nf_owned_frame_free(owner)
  assert gpu.nf_owned_gpu_contexts()==1;assert gpu.nf_owned_gpu_close()
 except BaseException as e:errors.append(repr(e))
t=threading.Thread(target=consumer);t.start()
for raw in raws:
 # Mutate producer memory after push: consumer must retain original copy.
 buffer=C.create_string_buffer(raw,len(raw));assert d.nf_owned_handoff_push(q,buffer,len(buffer));C.memset(buffer,0,len(buffer));signals.put(1,timeout=30)
t.join(30);assert not t.is_alive() and not errors,errors
Callback=C.CFUNCTYPE(C.c_int,P);calls=[]
@Callback
def commit(ctx):calls.append(1);return 1
d.nf_owned_handoff_commit.argtypes=[P,U,Callback,P];assert d.nf_owned_handoff_commit(q,epoch,commit,None)==1;assert d.nf_owned_handoff_epoch(q,epoch+1);assert d.nf_owned_handoff_commit(q,epoch,commit,None)==0 and len(calls)==1
d.nf_owned_handoff_close(q);assert not d.nf_owned_handoff_push(q,raws[0],len(raws[0]));d.nf_owned_handoff_destroy(q)
report=dict(result='PASS_THREADED_OWNED_FRAME_GPU_HANDOFF',checks=results,capacity=3,source_mutation_isolated=True,popped_owner_survives_epoch=True,stale_commit_rejected=True,scope='Recorded runtime-owned frames across producer/renderer threads; no live simulation scheduling or gameplay timing proof.')
(p/'owned-frame-handoff-tests.json').write_text(json.dumps(report,indent=2));print(report)
