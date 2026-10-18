import json,sys,statistics
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());rows=r['world_preparation_stage_samples'];samples=[]
for row in rows:
 for t in row.get('sample_timings',[]):
  assert t['wall_ns']==t['completed_ns']-t['started_ns'] and t['wall_ns']>=0 and t['thread_cpu_ns']>=0
  samples.append(dict(older=row['older'],newer=row['newer'],alpha=t['alpha'],wall_ms=t['wall_ns']/1e6,coarse_thread_cpu_ms=t['thread_cpu_ns']/1e6))
assert samples
out=dict(scope='Per-sample wall and coarse Windows thread CPU times; does not identify scheduler or GIL cause',interval_count=len(rows),sample_count=len(samples),sample_median_ms=statistics.median(t['wall_ms'] for t in samples),largest_samples=sorted(samples,key=lambda t:t['wall_ms'],reverse=True)[:10],largest_owner_close_ms=max(row.get('prepared_close_ns') or 0 for row in rows)/1e6)
p.with_suffix('.sample-delays.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
