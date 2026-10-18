"""Measure GC wall overlap with recorded preparation intervals."""
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());g=r.get('gc_collection_samples',[]);rows=[]
for s in r['world_preparation_stage_samples']:
 a=s['started_ns'];b=s['completed_ns'];overlap=sum(max(0,min(b,x['end_ns'])-max(a,x['start_ns'])) for x in g)
 rows.append(dict(older=s['older'],newer=s['newer'],wall_ms=(b-a)/1e6,gc_overlap_ms=overlap/1e6))
out=dict(scope='Observed GC overlap only, not causal attribution; profile run includes capture/profiler overhead',gc_samples=len(g),gc_dropped=r.get('gc_trace_dropped'),gc_total_ms=sum(x['end_ns']-x['start_ns'] for x in g)/1e6,max_collection_ms=max(((x['end_ns']-x['start_ns'])/1e6 for x in g),default=0),largest_jobs=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:10],largest_gc_overlaps=sorted(rows,key=lambda x:x['gc_overlap_ms'],reverse=True)[:5])
p.with_suffix('.preparation-gc-overlap.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
