"""Join complete slow request ledger to observed long caller waits."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['preparation_retention']['slow_process_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
long=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert long['dropped']==0
rows=[]
for gap in long['records']:
 caller=gap['caller_stages'];a=caller.get('preparation_take_begin_ns');b=caller.get('preparation_take_end_ns')
 if a is None or b is None or b-a<=33333000:continue
 matches=[x for x in ledger['records'] if a<=x['end_ns']<=b and x['begin_ns']<=b]
 row=dict(display_index=gap['display_index'],interval_ms=gap['interval_ns']/1e6,take_ms=(b-a)/1e6,matching_slow_requests=len(matches))
 if matches:
  request=max(matches,key=lambda x:x['end_ns']);child=request['child_boundaries'];assert request['child_gc_dropped']==0
  row.update(older=request['older'],newer=request['newer'],request_total_ms=request['ipc_and_prepare_ns']/1e6,child_prepare_ms=request['child_prepare_ns']/1e6,child_send_ms=request['child_send_ns']/1e6,child_precompute_ms=request['child_precompute_ns']/1e6,child_construct_ms=request['child_construct_ns']/1e6,child_gc_overlap_ms=sum(max(0,min(b,g['end_ns'])-max(a,g['start_ns']))/1e6 for g in request['child_gc_rows']))
 rows.append(row)
out=dict(result='PASS_BOUNDED_SLOW_PROCESS_WAIT_JOIN',slow_requests=ledger['total'],long_waits=len(rows),matched=sum(x['matching_slow_requests']>0 for x in rows),rows=rows,scope=f"Only requests above{ledger['threshold_ns']/1e6:g}ms retained; unmatched wait is not evidence of no child stall. Time association, not exclusive causal attribution; parent begin approximate.")
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
