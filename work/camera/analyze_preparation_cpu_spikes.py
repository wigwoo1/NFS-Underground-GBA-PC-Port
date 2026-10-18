"""Separate owner CPU work from wall delay using existing preparation telemetry."""
import json,sys,statistics
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());rows=[]
for s in r['world_preparation_stage_samples']:
 wall=(s['completed_ns']-s['started_ns'])/1e6
 cpu=(s['construct_thread_cpu_ns']+s['precompute_thread_cpu_ns'])/1e6
 samples=s.get('sample_timings',[])
 rows.append(dict(older=s['older'],newer=s['newer'],wall_ms=wall,coarse_cpu_ms=cpu,wall_minus_coarse_cpu_ms=wall-cpu,alpha_count=len(samples),construct_ms=s['construct_advance_ns']/1e6,precompute_ms=s['precompute_ns']/1e6,sample_wall_ms=[x['wall_ns']/1e6 for x in samples],sample_cpu_ms=[x['thread_cpu_ns']/1e6 for x in samples]))
def group(items):
 return dict(count=len(items),median_wall_ms=statistics.median(x['wall_ms'] for x in items),median_cpu_ms=statistics.median(x['coarse_cpu_ms'] for x in items),median_wall_minus_cpu_ms=statistics.median(x['wall_minus_coarse_cpu_ms'] for x in items)) if items else dict(count=0)
out=dict(scope='Windows coarse thread CPU: negative residuals allowed; no exclusive scheduling or causal GIL attribution',intervals=len(rows),under_33ms=group([x for x in rows if x['wall_ms']<33.333]),over_100ms=group([x for x in rows if x['wall_ms']>100]),largest_cpu_jobs=sorted(rows,key=lambda x:x['coarse_cpu_ms'],reverse=True)[:10],by_alpha_count={str(n):group([x for x in rows if x['alpha_count']==n]) for n in sorted({x['alpha_count'] for x in rows})})
p.with_suffix('.cpu-spikes.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='largest_cpu_jobs'},indent=2));print('largest CPU job:',out['largest_cpu_jobs'][0])
