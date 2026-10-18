import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());s=r['bounded_diagnostic_stats']['whole_run_api_intervals'];assert r['result']=='SMOKE_COMPLETE' and r['error'] is None and s['slow_gap_dropped']==0 and r['gc_trace_dropped']==0
rows=[]
for x in s['slow_gap_samples']:
 a=x['worker_execution'];b=x['present_worker_execution']
 for t in (a,b):
  assert t['submitted_ns']<=t['started_ns']<=t['ended_ns'];assert t['wall_ns']==t['ended_ns']-t['started_ns'];assert t['cpu_ns']>=0 and t['cycles']>=0;assert t['thread_id']!=r['producer_thread_id']
 gc=[g for g in r['gc_collection_samples'] if g['start_ns']<x['end_ns'] and g['end_ns']>x['start_ns']]
 rows.append(dict(index=x['display_index'],gap_ms=(x['end_ns']-x['start_ns'])/1e6,draw_callback_ms=x['draw_ns']/1e6,worker_wall_ms=a['wall_ns']/1e6,worker_cpu_ms=a['cpu_ns']/1e6,worker_cycles=a['cycles'],worker_queue_ms=a['queue_to_execution_ns']/1e6,present_wall_ms=b['wall_ns']/1e6,present_cpu_ms=b['cpu_ns']/1e6,gc_max_ms=max(((g['end_ns']-g['start_ns'])/1e6 for g in gc),default=0)))
assert len(rows)==s['over_25ms']
retained=[x['prepared']['worker_execution'] for x in r['presentation_samples'] if x['native_result']==1]
out=dict(observed_retained_cpu_ticks_ns=sorted({x['cpu_ns'] for x in retained}),retained_window_cycle_median=statistics.median(x['cycles'] for x in retained),retained_window_wall_median_ms=statistics.median(x['wall_ns'] for x in retained)/1e6,all_slow_gap_cycle_median=statistics.median(x['worker_execution']['cycles'] for x in s['slow_gap_samples']),result='MEASURED_SLOW_FRAME_RENDER_THREAD_CPU',gaps=len(rows),without_long_collection=sorted([x for x in rows if x['gc_max_ms']<=8],key=lambda x:x['gap_ms'],reverse=True)[:15],worst=sorted(rows,key=lambda x:x['gap_ms'],reverse=True)[:10],scope='Measured thread CPU/cycles and elapsed time, all slow-gap records retained. Observed thread CPU readings quantized in 15.625ms steps; zero readings cannot establish waiting or CPU absence. Cycles are execution counts, not elapsed time. Slow-gap and retained-window medians have different sampling scopes. Does not distinguish GIL, driver or GPU cause. No scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
