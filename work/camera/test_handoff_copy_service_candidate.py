import ctypes as C,struct,threading,time,json
from pathlib import Path
from owned_handoff_copy_service_candidate import HandoffCopyService
P=C.c_void_p;U=C.c_uint64;Z=C.c_size_t;Hook=C.CFUNCTYPE(None)
d=C.CDLL(str(Path('work/camera/owned-handoff-request-authority-barrier-test.dll').resolve()))
for name,args,result in [('create',[U],P),('pause',[P,C.c_uint],C.c_int),('pop_token',[P,P,P],P),('destroy',[P],None)]:
 f=getattr(d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=result
d.nf_owned_frame_free.argtypes=[P];d.nf_test_copy_hook.argtypes=[P]
raw=Path('work/camera/motion-actual-scanline-assets/8758-native-complete-frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0]
checks=[]
for retire in (False,True):
 q=d.nf_owned_handoff_create(epoch);service=HandoffCopyService(d,q,2);entered=threading.Event();release=threading.Event()
 @Hook
 def barrier():entered.set();assert release.wait(5)
 d.nf_test_copy_hook(C.cast(barrier,P))
 try:
  first=service.submit(raw);assert entered.wait(5);second=service.submit(raw)
  assert not service.wait_idle(.01),'In-flight copy incorrectly reported idle'
  try:service.submit(raw)
  except RuntimeError:pass
  else:raise AssertionError('Unbounded admission')
  try:service.submit(bytearray(raw))
  except ValueError:pass
  else:raise AssertionError('Mutable payload admitted')
  if retire:assert d.nf_owned_handoff_pause(q,1);assert d.nf_owned_handoff_pause(q,0)
  d.nf_test_copy_hook(None);release.set()
  answers=[first.result(5),second.result(5)];assert service.wait_idle(5);assert all(x['published']==(not retire) for x in answers)
  owners=[]
  while True:
   size=Z();g=U();p=d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(g))
   if not p:break
   assert C.string_at(p,size.value)==raw;owners.append(p)
  assert len(owners)==(0 if retire else 2)
  for p in owners:d.nf_owned_frame_free(p)
  service.close();assert not service.thread.is_alive() and service.pending==0
  try:service.submit(raw)
  except RuntimeError:pass
  else:raise AssertionError('Closed admission accepted')
  checks.append(dict(retired=retire,published=[x['published'] for x in answers]))
 finally:
  d.nf_test_copy_hook(None);release.set();service.close();d.nf_owned_handoff_destroy(q)
q=d.nf_owned_handoff_create(epoch);service=HandoffCopyService(d,q,2);entered=threading.Event();release=threading.Event()
@Hook
def close_barrier():entered.set();assert release.wait(5)
d.nf_test_copy_hook(C.cast(close_barrier,P))
try:
 first=service.submit(raw);assert entered.wait(5);second=service.submit(raw)
 assert not service.wait_idle(.01),'In-flight copy incorrectly reported idle'
 assert d.nf_owned_handoff_pause(q,1)
 closer=threading.Thread(target=service.close);closer.start()
 deadline=time.monotonic()+5
 while not service.closed:
  assert time.monotonic()<deadline;time.sleep(.001)
 assert closer.is_alive();d.nf_test_copy_hook(None);release.set();closer.join(5);assert not closer.is_alive()
 assert not first.result(5)['published']
 try:second.result(5)
 except RuntimeError:pass
 else:raise AssertionError('Queued request published on close')
 assert service.pending==0 and not service.thread.is_alive()
 checks.append(dict(close_inflight_joined=True,queued_retired=True))
finally:
 d.nf_test_copy_hook(None);release.set();service.close();d.nf_owned_handoff_destroy(q)
Path('work/camera/prototype-runs/handoff-copy-service-20261009.json').write_text(json.dumps(dict(result='PASS_BOUNDED_COPY_SERVICE_ACTUAL_FRAME_RETIREMENT',checks=checks,scope='Component service only; no renderer notification/live4K/game timing integration.'),indent=2));print('PASS_BOUNDED_COPY_SERVICE_ACTUAL_FRAME_RETIREMENT')



