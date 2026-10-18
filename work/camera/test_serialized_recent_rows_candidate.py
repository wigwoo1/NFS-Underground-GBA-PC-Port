import json,gc
from pathlib import Path
from owned_recent_rows_candidate import RecentRows as Base
from owned_serialized_recent_rows_candidate import RecentRows as Candidate
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791516210551968900.json').read_text());rows=r['world_preparation_stage_samples']
a=Base(60,1048576);b=Candidate(60,1048576)
for row in rows:a.append(row);b.append(row)
assert a.snapshot()==b.snapshot() and a.stats()==b.stats()
def containers(value):
 seen=set();pending=[value];count=0
 while pending:
  x=pending.pop()
  if id(x) in seen:continue
  seen.add(id(x))
  if isinstance(x,dict):count+=gc.is_tracked(x);pending.extend(x.values())
  elif isinstance(x,(list,tuple)):count+=gc.is_tracked(x);pending.extend(x)
 return count
baseline=sum(containers(row) for row in a.rows);candidate=sum(containers(row) for row in b.rows);assert baseline>1000 and candidate==0
x={'nested':[1]};b.append(x);x['nested'].append(2);snap=b.snapshot();assert snap[-1]=={'nested':[1]};snap[-1]['nested'].append(3);assert b.snapshot()[-1]=={'nested':[1]}
for bad in ({'x':float('nan')},{'x':'x'*1048577}):
 try:b.append(bad)
 except ValueError:pass
 else:raise AssertionError('Invalid diagnostic accepted')
assert len(b)==60 and b.stats()['total_records']==61 and b.stats()['dropped_records']==1
out=dict(result='PASS_SERIALIZED_ACTUAL_DIAGNOSTIC_PARITY',actual_rows=len(rows),baseline_tracked_nested_containers=baseline,candidate_tracked_nested_containers=candidate,scope='Actual retained live preparation diagnostics, snapshots identical; fewer retained tracked containers, not live collection/cadence proof.')
Path('work/camera/prototype-runs/serialized-recent-rows-20261008.json').write_text(json.dumps(out,indent=2));print(out)
