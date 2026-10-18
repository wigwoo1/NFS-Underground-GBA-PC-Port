import json,gc
from pathlib import Path
from owned_serialized_execution_traces_candidate import TraceRows
paths=['parent-publication-tail-1791615855065878700.json','native-stage-cycles-1791615855039808900.json','parent-pair-retirement-1791615855150593000.json','sample-readiness-margin-1791615855168210200.json']
reports=[]
def tracked_containers(value):
 seen=set();counts={}
 def visit(v):
  if type(v) not in (list,dict,tuple) or id(v) in seen:return
  seen.add(id(v))
  if gc.is_tracked(v):counts[type(v).__name__]=counts.get(type(v).__name__,0)+1
  for x in (v.values() if type(v) is dict else v):visit(x)
 visit(value);return counts
for name in paths:
 original=json.loads((Path('work/camera/prototype-runs')/name).read_text())['rows'];rows=TraceRows(8192)
 for row in original:rows.append(row)
 assert rows.snapshot()==original
 assert all(type(x) is bytes and not gc.is_tracked(x) for x in rows.encoded)
 reports.append(dict(file=name,exact_records=len(rows),decoded_tracked_containers=tracked_containers(original),storage=rows.stats()))
private=TraceRows(1);sample={'nested':[1,{'a':2}]};private.append(sample);sample['nested'][1]['a']=3
assert private.snapshot()==[{'nested':[1,{'a':2}]}]
x=private.snapshot();x[0]['nested'].clear();assert private.snapshot()==[{'nested':[1,{'a':2}]}]
try:private.append({});raise AssertionError('capacity accepted')
except ValueError:pass
large=TraceRows(1)
try:large.append({'x':'a'*5000});raise AssertionError('oversize accepted')
except ValueError:pass
assert len(large)==0
out=dict(result='PASS_PRIVATE_EXACT_BOUNDED_EXECUTION_TRACES',reports=reports,mutation_isolation=True,capacity_rejection=True,oversize_rejection=True,scope='Exact replayed diagnostic records and retention components; decoded counts are representation census, not active heap or causal cadence proof.')
Path('work/camera/prototype-runs/serialized-execution-traces-component.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
