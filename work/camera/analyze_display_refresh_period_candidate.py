import json,sys,statistics
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text());samples=[];previous=None;seen={}
for row in p['rows']:
 if row[7]!=0 or not row[10] or not row[11]:continue
 key=row[10];time_ns=row[11]*1000000000//row[3]
 if key in seen:assert seen[key]==time_ns;continue
 seen[key]=time_ns
 if previous:
  delta=key-previous[0];dt=time_ns-previous[1]
  assert delta>0 and dt>0
  samples.append(dict(refreshes=delta,ns_per_refresh=dt/delta))
 previous=(key,time_ns)
assert samples
one=[x['ns_per_refresh'] for x in samples if x['refreshes']==1];assert one
interval=statistics.median(one)
out=dict(result='MEASURED_EXECUTION_DISPLAY_SCHEDULER_INTERVAL',single_refresh_samples=len(one),all_samples=len(samples),median_interval_ns=interval,nominal_hz=1e9/interval,min_single_ns=min(one),max_single_ns=max(one),fixed60_excess_period_ns=interval-1e9/60,predicted_fixed60_drift_30_seconds_ms=(interval-1e9/60)*1800/1e6,scope='SyncRefreshCount/SyncQPCTime consecutive scheduler samples; not full-frame motion, physical4K or input latency certification. Median estimate not pacing configuration.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
