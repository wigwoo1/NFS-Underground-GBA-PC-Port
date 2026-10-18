from pathlib import Path
import json,collections
from invocation_tree import invocation_tree
p=Path(__file__).resolve().parent;r=json.loads((p/'texture-provenance-tests.json').read_text());counts=collections.Counter();examples=[]
traces={x['serial']:x for x in r['dispatch_samples']}
for snapshot in r['region_invocation_samples']:
 rows=snapshot['records'];trace=traces[snapshot['scene']];commands=trace['commands'];parents,children=invocation_tree(rows,len(commands));counts['scenes']+=1
 counts['calls']+=len(rows);counts['child_calls']+=sum(x is not None for x in parents)
 for index,row in enumerate(rows):
  if row[8]:continue
  owned=set(range(row[6],row[7]));child_slots=set()
  for child in children[index]:child_slots.update(range(rows[child][6],rows[child][7]))
  direct=sorted(owned-child_slots)
  model=[j for j in direct if commands[j][0]==3]
  foreign=[j for j in direct if commands[j][0]!=3 and tuple(trace['origins'][j][2:6])!=tuple(row[:4])]
  assert not foreign,(snapshot['scene'],index,foreign)
  counts['root_direct_commands']+=len(direct);counts['root_model_commands']+=len(model)
  if children[index]:counts['roots_with_children']+=1
  if children[index] or model:
   examples.append(dict(scene=snapshot['scene'],region=row[0]&65535,children=len(children[index]),child_commands=len(child_slots),direct_commands=len(direct),model_commands=len(model)))
report=dict(result='PASS',counts=dict(counts),complex_roots=examples,scope='Captured preorder tree and direct-command provenance. Retains empty children; no sampled child creation or removal.')
(p/'invocation-tree-tests.json').write_text(json.dumps(report,indent=2));print(dict(counts))
# Malformed trees must fail before a caller uses any computed ownership.
invalid=[[[0]*6+[0,1,1]],[[0]*6+[0,1,0],[0]*6+[0,2,1]],[[0]*6+[0,3,0],[0]*6+[0,2,1],[0]*6+[1,3,1]],[[0]*6+[0,2,0],[0]*6+[1,3,0]],[[0]*6+[2,1,0]]]
for rows in invalid:
 try:invocation_tree(rows,3)
 except ValueError:pass
 else:raise AssertionError('invalid tree accepted')
report['malformed_rejections']=len(invalid)
report['counts']['roots_with_children_or_model']=len(examples)
(p/'invocation-tree-tests.json').write_text(json.dumps(report,indent=2));print(report['counts'])
