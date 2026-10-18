import ctypes as C,threading,struct,json
from pathlib import Path
d=C.CDLL(str(Path('work/camera/owned-handoff-copy-barrier-test.dll').resolve()));P=C.c_void_p;U=C.c_uint64;Z=C.c_size_t;Hook=C.CFUNCTYPE(None)
for name,args,result in [('create',[U],P),('push',[P,P,Z],C.c_int),('pop',[P,P],P),('epoch',[P,U],C.c_int),('pause',[P,C.c_uint],C.c_int),('close',[P],None),('destroy',[P],None)]:
 f=getattr(d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=result
d.nf_test_copy_hook.argtypes=[P];d.nf_owned_frame_free.argtypes=[P]
raw=Path('work/camera/motion-actual-scanline-assets/8758-native-complete-frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];checks=[]
for action in ('pause_resume','epoch','close','capacity','unchanged'):
 q=d.nf_owned_handoff_create(epoch);entered=threading.Event();release=threading.Event();answer=[];errors=[];before=d.nf_test_rejected_copies()
 @Hook
 def barrier():entered.set();release.wait(5)
 d.nf_test_copy_hook(C.cast(barrier,P))
 def push():
  try:answer.append(d.nf_owned_handoff_push(q,raw,len(raw)))
  except BaseException as e:errors.append(repr(e))
 thread=threading.Thread(target=push);thread.start();assert entered.wait(5);d.nf_test_copy_hook(None)
 try:
  if action=='pause_resume':assert d.nf_owned_handoff_pause(q,1);assert d.nf_owned_handoff_pause(q,0)
  elif action=='epoch':assert d.nf_owned_handoff_epoch(q,epoch+1)
  elif action=='close':d.nf_owned_handoff_close(q)
  elif action=='capacity':
   for i in range(3):assert d.nf_owned_handoff_push(q,raw,len(raw))
  release.set();thread.join(5);assert not thread.is_alive() and not errors
  expected=int(action=='unchanged');assert answer==[expected]
  assert d.nf_test_rejected_copies()==before+(not expected)
  size=Z();owners=[]
  while True:
   p=d.nf_owned_handoff_pop(q,C.byref(size))
   if not p:break
   assert C.string_at(p,size.value)==raw;owners.append(p)
  assert len(owners)==(3 if action=='capacity' else expected)
  for p in owners:d.nf_owned_frame_free(p)
  checks.append(action)
 finally:release.set();thread.join(5);d.nf_owned_handoff_destroy(q)
out=dict(result='PASS_COPY_PUBLICATION_RACES',checks=checks,scope='test-only barrier after actual native full copy; final publication path unchanged, rejects free copies; production candidate has no hook')
Path('work/camera/handoff-copy-race-tests.json').write_text(json.dumps(out,indent=2));print(out)
