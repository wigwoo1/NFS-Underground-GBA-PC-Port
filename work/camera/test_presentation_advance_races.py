"""Controlled real native callback/lifecycle interleavings, separate DLL only."""
import ctypes as C,threading,json,shutil
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
d=C.CDLL(str(Path('work/camera/owned-presentation-advance-candidate.dll').resolve()))
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
args=[P,U,U,U,U,U,C.c_double,CB,P,P];d.nf_owned_handoff_commit_sample.argtypes=args;d.nf_owned_handoff_commit_sample_advance.argtypes=args+[P,U,P]
for name in ('pause','epoch'):getattr(d,'nf_owned_handoff_'+name).argtypes=[P,U]
d.nf_owned_handoff_close.argtypes=[P];d.nf_owned_handoff_destroy.argtypes=[P];d.nf_owned_handoff_last_sample.argtypes=[P,P]
checks=[]
for lifecycle in ('pause','epoch','close'):
 for success in (False,True):
  q=d.nf_owned_handoff_create(7);entered=threading.Event();release=threading.Event();attempted=threading.Event();done=threading.Event();log=[];results=[];errors=[];out=(U*8)();audit=(U*2)(777,888)
  @CB
  def initial(ctx):return 1
  @CB
  def held(ctx):
   log.append('callback_enter');entered.set()
   if not release.wait(3):errors.append('callback timeout');return 0
   log.append('callback_return');return int(success)
  def present():
   results.append(d.nf_owned_handoff_commit_sample_advance(q,7,1,10,15,14,.5,held,None,out,None,10,audit));log.append('commit_return')
  def mutate():
   attempted.set()
   if lifecycle=='pause':value=d.nf_owned_handoff_pause(q,1)
   elif lifecycle=='epoch':value=d.nf_owned_handoff_epoch(q,8)
   else:d.nf_owned_handoff_close(q);value=1
   log.append('lifecycle_return');assert value==1;done.set()
  pt=threading.Thread(target=present);mt=threading.Thread(target=mutate)
  try:
   assert d.nf_owned_handoff_commit_sample(q,7,1,10,15,10,.5,initial,None,out)==1
   pt.start();assert entered.wait(3);mt.start();assert attempted.wait(3)
   assert not done.wait(.05),'Lifecycle returned during held presentation callback'
   before=(U*8)();assert d.nf_owned_handoff_last_sample(q,before)==1 and before[4]==10
   release.set();pt.join(3);mt.join(3);assert not pt.is_alive() and not mt.is_alive() and not errors and done.is_set()
   assert results==[1 if success else -1]
   assert log.index('callback_return')<log.index('lifecycle_return')
   assert list(audit)==([10,3] if success else [777,888])
   called=[]
   @CB
   def stale(ctx):called.append(1);return 1
   assert d.nf_owned_handoff_commit_sample_advance(q,7,1,10,15,20,.5,stale,None,out,None,14 if success else 10,audit)==0 and not called
   checks.append(dict(lifecycle=lifecycle,success=success,log=log,audit=list(audit),result='PASS'))
  finally:
   release.set()
   if pt.ident:pt.join(3)
   if mt.ident:mt.join(3)
   if pt.is_alive() or mt.is_alive():raise RuntimeError('Live threads; refusing unsafe destroy')
   d.nf_owned_handoff_destroy(q)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/presentation-advance-races-20261007');cp.mkdir(exist_ok=True);shutil.copy2(__file__,cp/Path(__file__).name);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Actual native held-callback lifecycle interleavings for pause/epoch/close and callback success/failure. Separate component only; no live60fps or game input verification.'),indent=2));print('PASS six native callback/lifecycle races')
