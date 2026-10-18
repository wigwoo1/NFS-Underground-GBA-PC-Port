import json,sys,time,statistics
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory
from owned_road_material_decode_reuse_candidate import original,candidate
r=json.loads(Path(sys.argv[1]).read_text());folder=Path(r['live_preparation_profiles'][0]['capture'])
s=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(s,'captured-range-setup','exec'),ns);ns['prepared'].close();ns['history'].close()
rows=[]
for scene in ns['scenes']:
 closed=scene.graph;times={};owners={}
 for label,fn in [('original',original),('candidate',candidate)]:
  values=[]
  memory=ClosedSceneMemory(closed,ns['rom'])
  for i in range(100):
   t=time.perf_counter_ns();obj=fn(closed,memory);values.append(time.perf_counter_ns()-t)
  times[label]=statistics.median(values)/1e6;owners[label]=obj
 a,b=owners.values();assert a==b
 rows.append(dict(refresh=closed.refresh,times_ms=times,candidates=len(a)))
guards=[]
for scene in ns['scenes']:
 closed=scene.graph
 for mode in ['missing','conflict']:
  results=[];logs=[]
  for fn in [original,candidate]:
   memory=ClosedSceneMemory(closed,ns['rom'])
   class FaultMemory:
    def __init__(self):self.calls=[]
    def read(self,address,size):
     self.calls.append((address,size))
     if size>20:
      if mode=='missing':raise ValueError('Injected unowned texture')
      return bytes(size)
     return memory.read(address,size)
   fault=FaultMemory();results.append(fn(closed,fault));logs.append(fault.calls)
  assert results[0]==results[1]
  if mode=='missing':assert logs[0]==logs[1]
  guards.append(dict(refresh=closed.refresh,mode=mode,candidates=len(results[0])))
out=dict(result='PASS_CAPTURED_MATERIAL_DECODE_PARITY',rows=rows,guards=guards,scope='Two captured scenes, exact all road candidate fields; not native4K/live cadence qualification.')
Path('work/camera/prototype-runs/road-material-decode-reuse-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
