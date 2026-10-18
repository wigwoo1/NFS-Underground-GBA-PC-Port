import json,sys
from pathlib import Path
rows=[]
for filename in sys.argv[1:-1]:
 r=json.loads(Path(filename).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
 for e in ledger['records']:
  p=e['prepared'];dispatch=p['renderer_dispatch'];transfer=p['bundle_transfer_profile'];a=e['caller_timing']['draw_begin_ns'];b=e['caller_timing']['draw_end_ns']
  assert a<=dispatch['submitted_ns']<=dispatch['started_ns']<=dispatch['completed_ns']<=b
  assert transfer['caller_begin_ns']<=transfer['native_begin_ns']<=transfer['native_end_ns']<=transfer['caller_end_ns']
  stages={x['stage']:x['elapsed_ns']/1e6 for x in p['consumer_stages']}
  residual=(dispatch['completed_ns']-dispatch['started_ns'])/1e6-p['source_prepare_ns']/1e6-sum(stages.values());assert residual>=-.001
  rows.append(dict(source=Path(filename).name,identity=[e['epoch'],e['generation'],e['display_index']],interval_ms=e['interval_ns']/1e6,prepare_dispatch_wait_ms=(dispatch['started_ns']-dispatch['submitted_ns'])/1e6,prepare_execution_ms=(dispatch['completed_ns']-dispatch['started_ns'])/1e6,prepare_caller_return_ms=(b-dispatch['completed_ns'])/1e6,source_prepare_ms=p['source_prepare_ns']/1e6,consumer_stages_ms=stages,prepare_unpartitioned_ms=residual,bundle_native_ms=(transfer['native_end_ns']-transfer['native_begin_ns'])/1e6,bundle_return_ms=(transfer['caller_end_ns']-transfer['native_end_ns'])/1e6,bundle_entry_ms=(transfer['native_begin_ns']-transfer['caller_begin_ns'])/1e6,hud_ready_before_take=None if p['hud_transfer'] is None else p['hud_transfer']['ready_before_take'],hud_transfer_observed=p['hud_transfer'] is not None))
out=dict(result='PASS_LONG_FRAME_PREPARATION_PARTITIONS',rows=rows,scope='Exact retained long-interval preparation dispatch and native bundle call boundaries; native-to-Python return includes scheduling and possible GIL reacquisition, not exclusive causal attribution. No smooth60 qualification.')
Path(sys.argv[-1]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
