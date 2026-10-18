"""Renderer thread CPU measurements; wall minus CPU is not a cause label."""
import json,sys,statistics
from pathlib import Path
from analyze_prepare_budget_candidate import analyze
r=json.loads(Path(sys.argv[1]).read_text());partition=analyze(r)
events=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'];by_index={x['index']:x for x in partition['rows']};rows=[]
for e in events:
 base=by_index[e['display_index']];hud=e['hud_lease_stages'];cpu=e['source_prepare_thread_cpu_ns'];assert cpu is not None and cpu>=0
 stages={x['stage']:dict(wall_ms=x['elapsed_ns']/1e6,thread_cpu_ms=x['thread_cpu_ns']/1e6,thread_cycles=x.get('thread_cycles')) for x in e['consumer_stages']};assert all(x['thread_cpu_ms']>=0 for x in stages.values())
 rows.append(dict(index=base['index'],gc_ms=base['gc_ms'],source_thread_cycles=e.get('source_prepare_thread_cycles'),snapshot_thread_cycles=hud.get('snapshot_thread_cycles'),source_wall_ms=base['source_ms'],source_thread_cpu_ms=cpu/1e6,snapshot_wall_ms=base['hud_snapshot_ms'],snapshot_thread_cpu_ms=hud['snapshot_thread_cpu_ns']/1e6,consumer_stages=stages))
groups={}
for name,group in [('all',rows),('gc_at_most_2ms',[x for x in rows if x['gc_ms']<=2])]:
 groups[name]=dict(count=len(group))
 if group:
  groups[name]['median_ms']={k:statistics.median(x[k] for x in group) for k in ('source_wall_ms','source_thread_cpu_ms','snapshot_wall_ms','snapshot_thread_cpu_ms')}
  groups[name]['median_cycles']={k:statistics.median(x[k] for x in group) for k in ('source_thread_cycles','snapshot_thread_cycles') if all(x[k] is not None for x in group)}
  groups[name]['consumer_median_cycles']={k:statistics.median(x['consumer_stages'][k]['thread_cycles'] for x in group) for k in group[0]['consumer_stages'] if all(x['consumer_stages'][k]['thread_cycles'] is not None for x in group)}
  groups[name]['consumer_median_ms']={k:{metric:statistics.median(x['consumer_stages'][k][metric] for x in group) for metric in ('wall_ms','thread_cpu_ms')} for k in group[0]['consumer_stages']}
out=dict(result='PREPARE_THREAD_CPU_WALL_ACCOUNTED',groups=groups,rows=rows,scope='Instrumented long API intervals only. Thread CPU excludes waiting but includes work on renderer thread; wall minus CPU can include scheduling, GIL, native/driver waits. No specific causal attribution or smooth pixel/scanout claim; CPU clock granularity may exceed short stage wall intervals. Execution cycles are not converted to milliseconds and are not exclusive attribution.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],groups)
