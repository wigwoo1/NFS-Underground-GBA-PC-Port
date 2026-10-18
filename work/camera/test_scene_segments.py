from pathlib import Path
import json,collections
from scene_segments import scene_segments
p=Path(__file__).resolve().parent;r=json.loads((p/'texture-provenance-tests.json').read_text());traces={x['serial']:x for x in r['dispatch_samples']};counts=collections.Counter()
for snapshot in r['region_invocation_samples']:
 records=snapshot['records'];t=traces[snapshot['scene']];parents,blocks=scene_segments(records,t['commands'],t['origins'],t['wall_passes'])
 def flatten(index):
  output=[]
  for segment in blocks[index]:
   output.extend(flatten(segment['child']) if segment['kind']=='child' else range(segment['begin'],segment['end']))
  assert output==list(range(records[index][6],records[index][7]))
  return output
 output=[]
 for i,parent in enumerate(parents):
  if parent is None:output.extend(flatten(i))
 assert output==list(range(len(t['commands'])))
 for block in blocks:
  for segment in block:
   counts[segment['kind']+'_segments']+=1
   if segment['kind']=='child' and segment['begin']==segment['end']:counts['empty_children_preserved']+=1
 counts['scenes']+=1;counts['commands_exact']+=len(output)
# Independent barrier fixture: equal-phase walls may not merge through empty calls.
rows=[[1,2,3,4,0,0,0,2,0],[5,6,7,8,0,0,1,1,1]]
commands=[[2,0,1,0,0,0],[2,1,2,0,0,0]];origins=[[0,0,1,2,3,4]]*2;phases=[[0,0,0]]*2
_,blocks=scene_segments(rows,commands,origins,phases)
assert [s['kind'] for s in blocks[0]]==['wall','child','wall']
try:scene_segments(rows,commands,[[0]*6]*2,phases)
except ValueError:counts['provenance_rejection']+=1
else:raise AssertionError('foreign direct draw accepted')
report=dict(result='PASS',counts=dict(counts),scope='Lossless captured command segmentation and explicit child/model barriers; no sampled child eligibility or live renderer integration.')
(p/'scene-segment-tests.json').write_text(json.dumps(report,indent=2));print(report)
