import time,threading,json
from pathlib import Path
import owned_native_source_cpu_worker_candidate as m
class Source:
 class Snapshot:
  def __call__(self,p):return 1
 nf_owned_input_snapshot=Snapshot()
 def nf_owned_input_poll(self):return 1
class Session:
 def __init__(self):self.source=Source()
 def prepare(self,*args):time.sleep(.01);return dict(publication=[1,1,0])
 def present(self,*args):return dict(status=0)
 def close(self):pass
m.NativeSourceSession=Session
w=m.NativeSourceWorker();producer=threading.get_ident()
try:
 a=w.prepare(None,1,1,0).result(2);b=w.present(1,1,0).result(2)
 for row in (a,b):
  t=row['worker_execution'];assert t['thread_id']==w.thread.ident and t['thread_id']!=producer;assert t['submitted_ns']<=t['started_ns']<=t['ended_ns'];assert t['wall_ns']==t['ended_ns']-t['started_ns'];assert t['cpu_ns']>=0 and t['cycles']>=0
 assert a['worker_execution']['wall_ns']>=8000000;assert a['worker_execution']['cpu_ns']<a['worker_execution']['wall_ns']
finally:w.close()
assert not w.thread.is_alive()
out=dict(result='PASS_RENDER_WORKER_CPU_WAIT_OWNERSHIP_CLEANUP',prepare=a['worker_execution'],present=b['worker_execution'],scope='Synthetic sleeping work distinguishes elapsed wait from thread CPU; no rendered pixel or live cadence proof.')
Path('work/camera/prototype-runs/native-worker-cpu-component-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
