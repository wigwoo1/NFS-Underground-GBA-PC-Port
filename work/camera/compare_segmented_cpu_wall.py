"""Compare recorded wall/CPU preparation and aligned coarse process load; no causal attribution."""
import json,sys,statistics
from pathlib import Path
load=json.loads(Path(sys.argv[3]).read_text(encoding='utf-8-sig'))
def summarize(path):
 r=json.loads(Path(path).read_text());stages=[p for p in r['world_preparation_stage_samples'] if not p.get('history_only')]
 vals=[]
 for p in stages:
  wall=p['precompute_ns']/1e6;cpu=p['precompute_thread_cpu_ns']/1e6
  overlaps=[s for s in load['samples'] if s['begin_ns']<p['completed_ns'] and s['end_ns']>p['constructed_ns']]
  vals.append(dict(older=p['older'],newer=p['newer'],wall_ms=wall,cpu_ms=cpu,wall_minus_thread_cpu_ms=wall-cpu,thread_cycles=p['precompute_thread_cycles'],observed_intervals=len(overlaps),top_processes=[s['top'][:2] for s in overlaps]))
 def stats(key):
  v=sorted(x[key] for x in vals);return dict(median=statistics.median(v),p95=v[min(len(v)-1,int(.95*len(v)))],maximum=max(v))
 return dict(report=path,count=len(vals),covered=sum(x['observed_intervals']>0 for x in vals),wall_ms=stats('wall_ms'),cpu_ms=stats('cpu_ms'),wall_minus_cpu_ms=stats('wall_minus_thread_cpu_ms'),largest=sorted(vals,key=lambda x:x['wall_ms'],reverse=True)[:3])
wait=json.loads(Path('work/camera/combined-segmented-wait-stalls.json').read_text())['largest'][0]
out=dict(candidate=summarize(sys.argv[1]),baseline=summarize(sys.argv[2]),largest_candidate_wait={k:wait[k] for k in ['display_index','wait_ms','entered_late_ms','returned_late_ms','max_lock_interval_ms','max_blocking_wait_interval_ms','executed_thread_cycles']},scope='Thread CPU samples are quantized in 15.625ms increments and can exceed wall time; wall-minus-CPU is not a reliable per-stage scheduler estimate. Cycles are executed work evidence, not duration or exclusive cause. Process observations coarse/partial; sequential conditions uncontrolled.')
Path(sys.argv[4]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

