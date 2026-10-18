"""Native lifecycle ordering while Python registration callback is gated."""
import ctypes as C,threading,json,time
from pathlib import Path
from live_native_batch_candidate import NativeBatchWorker,Callback
from owned_active_batch_publication import ActiveBatchPublication
P=C.c_void_p;U=C.c_uint64
path=str(Path('work/camera/owned-batch-present-candidate.dll').resolve());d=C.CDLL(path);reg=C.PyDLL(path)
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
d.nf_owned_handoff_pause.argtypes=[P,C.c_uint];d.nf_owned_handoff_destroy.argtypes=[P]
reg.nf_owned_handoff_commit_token.argtypes=[P,U,U,Callback,P]
entered=threading.Event();release=threading.Event();pause_started=threading.Event();pause_done=threading.Event();errors=[];tokens=[];order=[]
class GatedRegistry(ActiveBatchPublication):
 def begin(self,*args):
  entered.set()
  if not release.wait(5):raise RuntimeError('Registration gate timeout')
  token=super().begin(*args);order.append('registered');return token
w=NativeBatchWorker.__new__(NativeBatchWorker);w.d=d;w.registration_bridge=reg;w.owner=d.nf_owned_handoff_create(7);w.batch_publication=GatedRegistry()
rows=[dict(epoch=7,generation=1,source_older=10,refresh=14,display_index=20,alpha=.25)]
def register():
 try:tokens.append(w.register_native_batch(7,1,rows,object()))
 except BaseException as e:errors.append(repr(e))
def pause():
 try:
  pause_started.set();assert d.nf_owned_handoff_pause(w.owner,1);order.append('pause_ack');pause_done.set()
 except BaseException as e:errors.append(repr(e))
a=threading.Thread(target=register);b=threading.Thread(target=pause)
try:
 a.start();assert entered.wait(5);b.start();assert pause_started.wait(5)
 assert not pause_done.wait(.05),'Pause passed active native registration lock'
 release.set();a.join(5);b.join(5);assert not a.is_alive() and not b.is_alive() and not errors,errors
 assert order==['registered','pause_ack'] and tokens[0] is not None
 assert w.batch_publication.finish(tokens[0],[])==() and w.batch_publication.active is None
 assert w.register_native_batch(7,1,rows,object()) is None
 assert d.nf_owned_handoff_pause(w.owner,0)
 rows[0]['generation']=3;token=w.register_native_batch(7,3,rows,object());assert token is not None
 assert w.batch_publication.finish(token,[])==()
finally:
 release.set()
 if a.ident:a.join(5)
 if b.ident:b.join(5)
 assert not a.is_alive() and not b.is_alive(),'Do not destroy live native owner'
 d.nf_owned_handoff_destroy(w.owner)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-batch-concurrent-registration-20261007');cp.mkdir(parents=True,exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',order=order,threads_joined=True,checks=['pause waits for active native registration','registered owner retired without committed prefix','retired token rejects','resumed generation registers'],scope='Actual native locks and live worker registration method with gated stand-in owner; not full GPU concurrency or physical input'),indent=2))
print('PASS concurrent native registration/pause ordering')
