"""Check live producer truncation with independent whole-run totals."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());s=r['producer_retention'];rows=r['producer_cycle_samples'];timing=r['timing']
assert r['result']=='SMOKE_COMPLETE' and len(r['pause_events'])==3
assert s['total_records']>240 and s['retained_records']==len(rows)==240 and s['dropped_records']==s['total_records']-240
summary=timing['producer_read_validate_reconstruct_submit'];assert summary['count']==s['total_records'] and summary['median_ms'] is None
assert summary['total_ms']>=sum(row['ns'] for row in rows)/1e6 and summary['max_ms']>=max(row['ns'] for row in rows)/1e6
assert timing['simulation_with_source_hooks']['count']==r['original_updates']
for key,value in timing['producer_stages'].items():
 observed=[row['stages'][key] for row in rows if key in row['stages']]
 assert value['count']>=len(observed) and value['median_ms'] is None
 if observed:assert value['total_ms']>=sum(observed)/1e6 and value['max_ms']>=max(observed)/1e6
assert abs(timing['simulated_seconds']-r['original_updates']*280896/16777216)<1e-9
out=dict(result='PASS_LIVE_PRODUCER_TRUNCATION',producer=s,simulation_count=timing['simulation_with_source_hooks']['count'],intervals=r['bounded_diagnostic_stats']['whole_run_present_intervals'],scope='Live retention coverage/count and whole-run totals bounding recent subset; exact sums additionally covered by captured full-log component replay. Not scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
