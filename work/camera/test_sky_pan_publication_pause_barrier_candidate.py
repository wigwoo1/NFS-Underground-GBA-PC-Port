import ast,ctypes as C,threading,json
from pathlib import Path
from types import SimpleNamespace as NS
from live_owned_gpu_worker import LiveOwnedGPUWorker
source=ast.parse(Path('work/camera/live_native_sky_pan_worker_candidate.py').read_text())
block=next(n for n in ast.walk(source) if isinstance(n,ast.With) and any('presentation_publication_lock' in ast.unparse(x.context_expr) for x in n.items))
code=compile(ast.fix_missing_locations(ast.Module(body=[block],type_ignores=[])),'production_publication_block','exec')
d=C.CDLL(str(Path('work/camera/owned-handoff-pool-candidate.dll').resolve()));P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
d.nf_owned_handoff_commit_sample.argtypes=[P,U,U,U,U,U,C.c_double,CB,P,P];d.nf_owned_handoff_commit_sample.restype=C.c_int
d.nf_owned_handoff_pause.argtypes=[P,C.c_uint];d.nf_owned_handoff_pause.restype=C.c_int;d.nf_owned_handoff_last_sample.argtypes=[P,P];d.nf_owned_handoff_last_sample.restype=C.c_int;d.nf_owned_handoff_destroy.argtypes=[P]
for trial in range(20):
 q=d.nf_owned_handoff_create(2);committed=threading.Event();release=threading.Event();attempted=threading.Event();paused=threading.Event();errors=[];snapshots=[]
 class Commit:
  def run(self,owned,e,g,older,newer,index,alpha,deadline):
   out=(U*8)();callback=CB(lambda ctx:1);assert d.nf_owned_handoff_commit_sample(q,e,g,older,newer,index,alpha,callback,None,out)==1
   committed.set();assert release.wait(5)
   return dict(native_result=1,commit=list(out))
 worker=NS(native_commit=Commit(),presentation_publication_lock=threading.Lock(),results=[],scene_snapshot_lock=threading.Lock(),resume_scene_chain=NS(items={}),scene_snapshots={},preparation_futures={},preparation_previous=None,native_present_callback=True,diagnostic_async_timer=False,diagnostic_finish=False,d=d,owner=q,pause_revision=0)
 ns=dict(self=worker,owned=None,epoch=2,generation=1,previous=(None,None,10),refresh=11,slot=dict(index=0,deadline_ns=0),alpha=.5,old=NS(boundary=NS(angle=1)),new=NS(boundary=NS(angle=2)),sky=NS(weight=.5),submitted_ns=0,dequeued_ns=0,threading=threading)
 def publish():
  try:exec(code,ns)
  except BaseException as error:errors.append(repr(error))
 def pause():
  try:
   attempted.set()
   with worker.presentation_publication_lock:
    assert d.nf_owned_handoff_pause(q,1);snapshots.append(LiveOwnedGPUWorker.pause_buffer_snapshot(worker));paused.set()
  except BaseException as error:errors.append(repr(error))
 a=threading.Thread(target=publish);b=threading.Thread(target=pause)
 try:
  a.start();assert committed.wait(5);assert worker.presentation_publication_lock.locked();assert not worker.results
  b.start();assert attempted.wait(5);assert not paused.wait(.01)
  release.set();a.join(5);b.join(5);assert not a.is_alive() and not b.is_alive() and not errors,errors
  assert paused.is_set() and snapshots[0]['last_committed']['display_index']==0 and worker.results[0]['display_index']==0
 finally:release.set();a.join(5);b.join(5);d.nf_owned_handoff_destroy(q)
out=dict(result='PASS_SKY_PAN_NATIVE_COMMIT_PYTHON_PUBLICATION_PAUSE_BARRIER',trials=20,scope='Actual production publication AST block and pause snapshot with real native handoff commit/pause; suspended after commit before Python row. No GPU/render/replay timing certification.')
Path('work/camera/prototype-runs/sky-pan-publication-pause-barrier-20261009.json').write_text(json.dumps(out,indent=2));print(out)
