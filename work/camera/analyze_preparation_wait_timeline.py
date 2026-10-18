"""Join rendering waits to exact original preparation intervals."""
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());stages=r['world_preparation_stage_samples']
index={}
for x in stages:index.setdefault((x['older'],x['newer']),[]).append(x)
rows=[];seen=set()
for x in r['presentation_samples']:
 if 'pair_begin_ns' not in x or x['pair_begin_ns'] in seen:continue
 seen.add(x['pair_begin_ns']);key=(x['source_older'],x['refresh'])
 candidates=index.get(key,[])
 candidates=[s for s in candidates if s['completed_ns']<=x['pair_ready_ns']]
 if not candidates:continue
 s=max(candidates,key=lambda v:v['completed_ns']);a=x['pair_begin_ns'];b=x['pair_ready_ns'];start=s['started_ns'];end=s['completed_ns']
 before=max(0,min(b,start)-a);active=max(0,min(b,end)-max(a,start));after=max(0,b-max(a,end))
 assert before+active+after==b-a
 rows.append(dict(older=key[0],newer=key[1],pair_wait_ms=(b-a)/1e6,before_job_start_ms=before/1e6,overlap_preparation_ms=active/1e6,after_job_complete_ms=after/1e6,construct_wall_ms=s['construct_advance_ns']/1e6,precompute_wall_ms=s['precompute_ns']/1e6,coarse_thread_cpu_ms=(s['construct_thread_cpu_ns']+s['precompute_thread_cpu_ns'])/1e6))
assert rows
out=dict(scope='Exact original-interval wall timeline; overlap is not exclusive CPU and thread CPU has coarse Windows resolution',matched_intervals=len(rows),largest_waits=sorted(rows,key=lambda x:x['pair_wait_ms'],reverse=True)[:20])
p.with_suffix('.preparation-wait-timeline.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

