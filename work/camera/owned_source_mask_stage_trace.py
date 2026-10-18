"""Default-off bounded stage timings for actual source mask construction."""
import time
from owned_thread_cycles import read
rows=[];totals={};dropped=0
def begin():return time.perf_counter_ns(),read()
def end(stage,started):
 global dropped
 stamp=time.perf_counter_ns();cycles=read();wall=stamp-started[0]
 t=totals.setdefault(stage,dict(count=0,total_ns=0,max_ns=0));t['count']+=1;t['total_ns']+=wall;t['max_ns']=max(t['max_ns'],wall)
 if wall>10000000:
  if len(rows)<512:rows.append(dict(stage=stage,begin_ns=started[0],end_ns=stamp,wall_ns=wall,thread_cycles=cycles-started[1]))
  else:dropped+=1
def snapshot():
 captured=list(rows);rows.clear()
 return dict(totals={k:dict(v) for k,v in totals.items()},long_stages=captured,dropped=dropped,scope='Inclusive actual mask phases. Cumulative totals and terminal-drained long rows; wall includes scheduling, cycle counts not waiting-cause proof.')
