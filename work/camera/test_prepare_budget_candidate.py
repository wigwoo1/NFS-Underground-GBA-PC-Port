from copy import deepcopy
from analyze_prepare_budget_candidate import analyze
entry=dict(display_index=1,begin_ns=0,end_ns=100,interval_ns=100,draw_begin_ns=10,draw_end_ns=70,renderer_dispatch=dict(kind='prepare',submitted_ns=20,started_ns=25,completed_ns=65),source_prepare_ns=20,consumer_stages=[dict(stage='upload',elapsed_ns=10)],hud_lease_stages=dict(snapshot_begin_ns=30,snapshot_end_ns=40,snapshot_new=True))
r=dict(gc_trace_dropped=0,gc_collection_samples=[],bounded_diagnostic_stats=dict(whole_run_api_intervals=dict(over_33_333ms=1,long_intervals=dict(total=1,dropped=0,records=[entry]))))
out=analyze(r);row=out['rows'][0]
assert row['pre_submit_ms']==10/1e6 and row['dispatch_wait_ms']==5/1e6 and row['worker_ms']==40/1e6 and row['caller_resume_ms']==5/1e6
assert row['worker_other_ms']==10/1e6 and out['groups']['gc_at_most_2ms']['count']==1
for change in ('order','budget','dropped','missing_record','snapshot_budget','duplicate_stage','negative_stage'):
 bad=deepcopy(r)
 if change=='order':bad['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'][0]['renderer_dispatch']['completed_ns']=80
 elif change=='budget':bad['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'][0]['source_prepare_ns']=50
 elif change=='dropped':bad['gc_trace_dropped']=1
 elif change=='missing_record':bad['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['total']=2
 elif change=='snapshot_budget':bad['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'][0]['hud_lease_stages']['snapshot_end_ns']=60
 elif change=='duplicate_stage':bad['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'][0]['consumer_stages'].append(dict(stage='upload',elapsed_ns=1))
 elif change=='negative_stage':bad['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'][0]['consumer_stages'][0]['elapsed_ns']=-1
 try:analyze(bad)
 except AssertionError:pass
 else:raise AssertionError('Invalid evidence accepted: '+change)
print('PASS_PREPARE_BUDGET_PARTITION_INVALID_EVIDENCE_REJECTION')
