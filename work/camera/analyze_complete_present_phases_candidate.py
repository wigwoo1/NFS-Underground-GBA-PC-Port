"""Complete bounded present-call partition; no exclusive CPU/scanout claim."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']
assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[]
for gap in ledger['records']:
 t=gap['present_stage_ns']; d=gap['present_renderer_dispatch']
 assert d['kind']=='present'
 stamps=[gap['present_begin_ns'],d['submitted_ns'],d['started_ns'],t['begin'],t['pumped'],t['presented'],t['queried'],d['completed_ns'],gap['present_end_ns']]
 assert all(type(v) is int for v in stamps)
 assert all(a<=b for a,b in zip(stamps,stamps[1:]))
 names=['caller_to_submit','dispatch_wait','dispatch_to_pump','window_pump','native_present','display_stats','query_to_completion','completion_to_caller']
 parts={name:(b-a)/1e6 for name,a,b in zip(names,stamps,stamps[1:])}
 elapsed=(stamps[-1]-stamps[0])/1e6
 assert abs(sum(parts.values())-elapsed)<1e-8
 rows.append(dict(display_index=gap['display_index'],api_interval_ms=gap['interval_ns']/1e6,present_callback_ms=elapsed,**parts))
out=dict(result='PASS_COMPLETE_PRESENT_PHASE_PARTITION',long_intervals=len(rows),rows=sorted(rows,key=lambda x:x['present_callback_ms'],reverse=True),scope='All retained long API intervals with zero drops; exact elapsed partitions, including scheduler/driver wait. Does not prove exclusive CPU/GPU cause or visible60fps.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
