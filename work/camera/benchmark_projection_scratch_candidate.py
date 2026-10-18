import runpy,time,json,statistics
from pathlib import Path
v=runpy.run_path('work/camera/test_projection_scratch_candidate.py');a,b,jobs=(v[k] for k in ('a','b','jobs'));rows=[]
for repeat in range(8):
 for name,owner in (('original',a),('scratch',b)) if repeat%2==0 else (('scratch',b),('original',a)):
  start=time.perf_counter_ns();cpu=time.thread_time_ns()
  for i in range(1500):
   m,expected=jobs[i%len(jobs)];result=owner.projected(m,owner.scales[0],owner.centers[0]);assert result==expected
  rows.append(dict(repeat=repeat,name=name,calls=1500,wall_ns=time.perf_counter_ns()-start,thread_cpu_ns=time.thread_time_ns()-cpu))
summary={n:dict(median_wall_us_per_call=statistics.median(x['wall_ns']/x['calls']/1000 for x in rows if x['name']==n),median_thread_cpu_us_per_call=statistics.median(x['thread_cpu_ns']/x['calls']/1000 for x in rows if x['name']==n)) for n in ('original','scratch')}
out=dict(result='PASS_EXACT_OUTPUT',rows=rows,summary=summary,scope='Interleaved actual53vertex native projection calls; includes immutable tuple output and private locking, no fullscene/GC/scanout performance certification');Path('work/camera/projection-scratch-benchmark.json').write_text(json.dumps(out,indent=2));print(summary)
