import ctypes as C,struct,threading,queue,json
from pathlib import Path
from concurrent.futures import Future
from owned_handoff_copy_service_candidate import HandoffCopyService
from owned_handoff_copy_settlement_candidate import CopySettlement
P=C.c_void_p;U=C.c_uint64;Z=C.c_size_t;Hook=C.CFUNCTYPE(None)
d=C.CDLL(str(Path('work/camera/owned-handoff-request-authority-barrier-test.dll').resolve()))
for name,args,result in [('create',[U],P),('pause',[P,C.c_uint],C.c_int),('pop_token',[P,P,P],P),('destroy',[P],None)]:
 f=getattr(d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=result
d.nf_owned_frame_free.argtypes=[P];d.nf_test_copy_hook.argtypes=[P]
raw=Path('work/camera/motion-actual-scanline-assets/8758-native-complete-frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];checks=[]
for mode in ('published','retired','notify_failure'):
 q=d.nf_owned_handoff_create(epoch);service=HandoffCopyService(d,q,1);entered=threading.Event();go=threading.Event();signals=queue.Queue(1);released=[];errors=[]
 @Hook
 def barrier():entered.set();assert go.wait(5)
 def retire():assert d.nf_owned_handoff_pause(q,1)
 def notify(receipt):
  if mode=='notify_failure':raise queue.Full()
  signals.put_nowait(receipt)
 settle=CopySettlement(notify,lambda:released.append(1),retire,errors.append)
 d.nf_test_copy_hook(C.cast(barrier,P))
 try:
  f=service.submit(raw);f.add_done_callback(settle);assert entered.wait(5)
  if mode=='retired':retire();assert d.nf_owned_handoff_pause(q,0)
  d.nf_test_copy_hook(None);go.set();f.result(5);assert service.wait_idle(5)
  racers=[threading.Thread(target=settle,args=(f,)) for _ in range(4)]
  for t in racers:t.start()
  for t in racers:t.join(5);assert not t.is_alive()
  if mode=='published':
   receipt=signals.get_nowait();size=Z();g=U();p=d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(g));assert p and g.value==receipt['generation'] and C.string_at(p,size.value)==raw;d.nf_owned_frame_free(p)
   assert not released and not errors
  else:
   assert signals.empty() and released==[1] and bool(errors)==(mode=='notify_failure')
   size=Z();g=U();assert not d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(g))
  checks.append(dict(mode=mode,outcome=settle.outcome,reservation_releases=len(released)))
 finally:d.nf_test_copy_hook(None);go.set();service.close();d.nf_owned_handoff_destroy(q)
f=Future();released=[];f.cancel();s=CopySettlement(lambda _:None,lambda:released.append(1),lambda:None,lambda _:None);s(f);s(f);assert released==[1]
f=Future();f.set_result(dict(published=True,epoch=1,generation=1));released=[];errors=[]
def broken_notify(_):raise RuntimeError('Notification failed')
def broken_retire():raise RuntimeError('Retirement failed')
s=CopySettlement(broken_notify,lambda:released.append(1),broken_retire,errors.append);s(f);s(f);assert not released and errors and s.outcome=='failed_retirement'
f=Future();f.set_result(dict(published=False,epoch=1,generation=1));calls=[]
def broken_release():calls.append(1);raise RuntimeError('Reservation callback failed')
s=CopySettlement(lambda _:None,broken_release,lambda:None,lambda _:None);s(f);s(f);assert calls==[1]
Path('work/camera/prototype-runs/handoff-copy-settlement-20261009.json').write_text(json.dumps(dict(result='PASS_ACTUAL_COPY_EXACTLY_ONCE_NOTIFICATION_RESERVATION',checks=checks,cancellation_release_once=True,scope='Component bridge and actual native copies; renderer integration/live4K/timing not verified.'),indent=2));print('PASS_ACTUAL_COPY_EXACTLY_ONCE_NOTIFICATION_RESERVATION')

