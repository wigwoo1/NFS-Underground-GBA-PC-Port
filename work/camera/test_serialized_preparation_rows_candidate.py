from pathlib import Path
import sys,json,gc
sys.path.insert(0,str(Path('work/camera').resolve()))
from owned_serialized_preparation_rows_candidate import PreparationRows
raw=json.loads(Path('work/camera/prototype-runs/owned-native-1791587759075186400.json').read_text())
expected=raw['world_preparation_stage_samples'];actual=PreparationRows()
for row in expected:actual.append(row)
assert len(actual)==len(expected) and list(actual)==expected and actual[-1]==expected[-1] and actual[:2]==expected[:2]
assert actual.snapshot()==expected
sentinel={'tuple':(1,2),'bytes':b'unchanged','nested':[{'a':3}]};rows=PreparationRows();rows.append(sentinel);assert rows[0]==sentinel
sentinel['nested'][0]['a']=4;assert rows[0]['nested'][0]['a']==3
for _ in range(999):rows.append({'v':1})
assert len(rows)==1000
try:rows.append({'v':2})
except ValueError:pass
else:raise AssertionError('capacity exceeded')
def tracked(value):
 seen=set();stack=[value];count=0
 while stack:
  item=stack.pop()
  if id(item) in seen:continue
  seen.add(id(item));count+=int(gc.is_tracked(item))
  if isinstance(item,dict):stack.extend(item.values());stack.extend(item.keys())
  elif isinstance(item,(list,tuple)):stack.extend(item)
 return count
out=dict(result='PASS_EXACT_SERIALIZED_PREPARATION_ROWS',requests=len(expected),original_tracked_containers=tracked(expected),serialized_tracked_containers=tracked(actual.rows),normal_gc=gc.isenabled(),scope='Exact retained diagnostic rows, lazy reconstruction, same first1000 policy; tracked container count is component evidence, not collector timing or live60 proof.')
Path('outputs/nfsug-native-renderer/camera-research/serialized-preparation-rows-20261009.json').write_text(json.dumps(out,indent=2));print(out)
