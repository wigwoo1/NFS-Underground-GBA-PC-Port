"""Opt-in bounded CPU profile of actual child sparse-memory construction."""
import cProfile,time,json,os
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory
original=ClosedSceneMemory.__init__;profile=cProfile.Profile();rows=[];total=0;dropped=0
def measured(self,closed,rom):
 global total,dropped
 begin=time.perf_counter_ns();cpu=time.thread_time_ns();profile.enable()
 try:return original(self,closed,rom)
 finally:
  profile.disable();total+=1
  row=dict(refresh=closed.refresh,wall_ns=time.perf_counter_ns()-begin,cpu_ns=time.thread_time_ns()-cpu)
  if len(rows)<512:rows.append(row)
  else:dropped+=1
ClosedSceneMemory.__init__=measured
def save():
 stats=[]
 for x in profile.getstats():
  code=x.code;name=code if isinstance(code,str) else code.co_name
  stats.append(dict(name=name,calls=x.callcount,total_seconds=x.totaltime,own_seconds=x.inlinetime))
 path=Path('work/camera/prototype-runs')/('child-scene-memory-cpu-'+str(os.getpid())+'.json')
 path.write_text(json.dumps(dict(total=total,dropped=dropped,records=rows,functions=sorted(stats,key=lambda x:x['total_seconds'],reverse=True),scope='Instrumented actual child constructors; profiler overhead alters timing, no performance comparison or cadence claim.'),indent=2))
