import json,gc,copy
from pathlib import Path
from owned_recent_rows_candidate import RecentRows as Base
from owned_serialized_recent_rows_candidate import RecentRows as Candidate
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791520413131316600.json').read_text());results=[]
def tracked(root):
 seen=set();stack=[root];n=0
 while stack:
  value=stack.pop()
  if id(value) in seen:continue
  seen.add(id(value));n+=gc.is_tracked(value)
  if isinstance(value,dict):stack.extend(value.values())
  elif isinstance(value,(list,tuple)):stack.extend(value)
 return n
for key in ['inputs','original_update_samples','sky_capture_records','consumer_boundary_stage_samples','worker_submit_stage_samples']:
 rows=r[key];base=Base();candidate=Candidate()
 for row in rows:
  original=copy.deepcopy(row);base.append(original);candidate.append(original);original['post_append_mutation']=True
 assert base.snapshot()==candidate.snapshot() and base.stats()==candidate.stats()
 results.append(dict(key=key,rows=len(rows),baseline_nested_tracked=tracked(list(base.rows)),candidate_nested_tracked=tracked(list(candidate.rows))))
# Capacity eviction and oversized-row behavior remain identical.
for cls in [Base,Candidate]:
 obj=cls(3,20)
 for i in range(5):obj.append({'i':i})
 assert obj.snapshot()==[{'i':2},{'i':3},{'i':4}] and obj.total_records==5
 try:obj.append({'long':'x'*30})
 except ValueError:pass
 else:raise AssertionError('Oversize record accepted')
out=dict(result='PASS_CAPTURED_FROZEN_RECENT_ROW_PARITY',rows=results,guards='mutation isolation, eviction, byte limit',scope='Captured diagnostic records only, no live performance or game-state representation change.')
Path('work/camera/prototype-runs/frozen-recent-row-parity-20261009.json').write_text(json.dumps(out,indent=2));print(out)
