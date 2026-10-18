"""Attribute observed submit waiting without treating overlapping wall stages as CPU."""
import json,sys,statistics
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());sub=r['worker_submit_stage_samples'];prep=r['world_preparation_stage_samples']
def summary(values):
 values=sorted(values)
 return dict(count=len(values),total_ms=sum(values)/1e6,median_ms=statistics.median(values)/1e6,p95_ms=values[int(.95*(len(values)-1))]/1e6,max_ms=max(values)/1e6)
submit={k:summary([x[k] for x in sub]) for k in ('space_wait_ns','snapshot_lock_ns','preparation_submit_ns','native_push_ns','notification_ns')}
preparation={k:summary([x[k] for x in prep]) for k in ('construct_advance_ns','precompute_ns','construct_thread_cpu_ns','precompute_thread_cpu_ns')}
wall=r['timing']['wall_seconds'];cpu=sum(x['construct_thread_cpu_ns']+x['precompute_thread_cpu_ns'] for x in prep)/1e9
out=dict(scope='overlapping live stage durations; thread CPU has coarse Windows resolution; wait totals are not additive with preparation wall time',submit=submit,preparation=preparation,wall_seconds=wall,simulated_seconds=r['timing']['simulated_seconds'],preparation_cpu_seconds=cpu,preparation_one_core_fraction=cpu/wall,largest_submit_wall_stage=max(submit,key=lambda k:submit[k]['total_ms']))
p.with_suffix('.preparation-backpressure.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
