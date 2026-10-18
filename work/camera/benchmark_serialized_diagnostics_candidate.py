import json,time,statistics,gc
from pathlib import Path
from owned_recent_rows_candidate import RecentRows as Base
from owned_serialized_recent_rows_candidate import RecentRows as Candidate
rows=json.loads(Path('work/camera/prototype-runs/owned-native-1791516210551968900.json').read_text())['world_preparation_stage_samples']
results={'baseline':[],'serialized':[]}; snapshots={'baseline':[],'serialized':[]}
for trial in range(12):
 for name,cls in ([('baseline',Base),('serialized',Candidate)] if trial%2==0 else [('serialized',Candidate),('baseline',Base)]):
  store=cls(60,1048576)
  begin=time.perf_counter_ns()
  for row in rows:store.append(row)
  elapsed=time.perf_counter_ns()-begin
  begin=time.perf_counter_ns();snap=store.snapshot();snapshot_ns=time.perf_counter_ns()-begin
  assert snap==rows
  results[name].append(elapsed);snapshots[name].append(snapshot_ns)
  del store,snap
out={'result':'PASS_ACTUAL_DIAGNOSTIC_COST_PARITY','rows_per_trial':len(rows),'trials':12,'append_total_ns':results,'snapshot_ns':snapshots,'median_append_per_row_ms':{k:statistics.median(v)/len(rows)/1e6 for k,v in results.items()},'median_snapshot_ms':{k:statistics.median(v)/1e6 for k,v in snapshots.items()},'scope':'Alternating actual captured diagnostics; shutdown decode cost included separately. Host uncontrolled; not live cadence or full-process GC proof.'}
Path('work/camera/prototype-runs/serialized-diagnostic-cost-20261008.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
