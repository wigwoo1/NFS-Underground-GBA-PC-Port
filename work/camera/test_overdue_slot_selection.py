import json,copy,shutil
from pathlib import Path
from owned_motion_clock import scene_samples,deadline
from owned_overdue_slot_selection import select
checks=0
for older,newer in ((100,105),(105,111),(111,116),(116,122)):
 origin=123456789;slots=scene_samples(origin,100,older,newer,12);original=copy.deepcopy(slots);previous=slots[0]['index']-1
 for now in [slots[0]['deadline_ns']-1]+[s['deadline_ns']+d for s in slots for d in (-1,0,1)]+[slots[-1]['deadline_ns']+1000000000]:
  tail,audit=select(slots,origin,now,previous);due=[i for i,s in enumerate(slots) if s['deadline_ns']<=now];first=due[-1] if due else 0
  assert list(tail)==slots[first:] and all(x is y for x,y in zip(tail,slots[first:])) and slots==original
  if first:
   assert audit['skipped_count']==first and audit['target_index']==tail[0]['index'] and audit['last_skipped_deadline_ns']<=audit['observed_ns']
  else:assert audit is None
  checks+=1
 assert select(slots,origin,slots[-1]['deadline_ns']+1000000000,None)==(tuple(slots),None)
 bad=copy.deepcopy(slots);bad[0]['deadline_ns']+=1
 try:select(bad,origin,0,previous)
 except ValueError:pass
 else:raise AssertionError('wrong grid accepted')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/overdue-slot-selection-20261007');cp.mkdir(exist_ok=True)
for n in ('owned_overdue_slot_selection.py','test_overdue_slot_selection.py'):shutil.copy2(Path('work/camera')/n,cp/n)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',clock_boundary_checks=checks,scope='Pure candidate tail selector on exact original-cycle scene samples; immutable source slot references retained. Initial native publication never skipped, future slots preserved, deadline boundaries and source-grid rejection. Not integrated gameplay or60fps proof.'),indent=2));print('PASS',checks,'exact clock boundary selections')
