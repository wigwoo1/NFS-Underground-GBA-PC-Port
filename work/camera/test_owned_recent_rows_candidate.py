import json
from pathlib import Path
from owned_recent_rows_candidate import RecentRows
v=RecentRows(3)
for i in range(10000):
 row=dict(index=i,nested=dict(keys=i));v.append(row);row['nested']['keys']=-1
assert v.total_records==10000 and len(v)==3 and [x['index'] for x in v.snapshot()]==[9997,9998,9999]
assert all(x['nested']['keys']==x['index'] for x in v.snapshot())
prior=v.snapshot()
for bad in (dict(value=float('nan')),dict(value='x'*65536)):
 try:v.append(bad)
 except ValueError:pass
 else:raise AssertionError('Invalid record accepted')
assert v.total_records==10000 and v.snapshot()==prior
out=dict(result='PASS_RECENT_ROWS_TOTALS',stats=v.stats(),scope='Record bounds, total/retained counts, detached nested inputs and rejected-record atomicity.')
Path('work/camera/prototype-runs/native-recent-rows-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
