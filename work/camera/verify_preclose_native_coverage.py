import sys,json
from pathlib import Path
raw=Path(sys.argv[1]);r=json.loads(raw.read_text());w=r['live_observation_stats']['whole_run_api_intervals'];b=w['native_success_boundaries'];a=w['all_successful_native_intervals']
assert not r['pause_events'],'Pause-aware active coverage requires separate segments'
assert b['successful_samples']==a['successful_samples'] and b['successful_samples']>0
begin=r['live_observation_begin_ns'];end=r['live_observation_end_ns'];eligible=b['first_success_deadline_ns']
assert begin<=eligible<=b['first_success_ns']<=b['last_success_ns']<=end<r['shutdown_evidence']['close_completed_ns']
assert a['excluded_generation_discontinuities']==0 and a['count']==a['successful_samples']-1
initial=(b['first_success_ns']-eligible)/1e6;trailing=(end-b['last_success_ns'])/1e6
passed=a['over25']==0 and initial<=25 and trailing<=25 and a['skipped_indices_between_successes']==0
out=dict(result='PASS_PRE_CLOSE_COVERAGE_ACCOUNTING',raw=str(raw.resolve()),active_successful_frames=a['successful_samples'],configured_start_delay_ms=(eligible-begin)/1e6,initial_after_deadline_hold_ms=initial,trailing_hold_ms=trailing,active_native_intervals=a,cadence_gate_passed=passed,scope='Unpaused active producer-loop snapshot beforeclose; tail success accounted. Snapshot covers published diagnostic rows, may lag inflight GPUcompletion; no physicalscanout or originaltiming qualification. Zero-success and pauses require explicitfail/segmentedhandling.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],'initial_ms',initial,'trailing_ms',trailing,'cadence_gate',passed)
