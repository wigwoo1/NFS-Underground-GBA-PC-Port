"""Map independently reconstructed queue plans to captured record occurrences."""
from pathlib import Path
import json,struct
from ordered_wall_plans import assemble
p=Path('work/camera');r=json.loads((p/'repeated-scene-plans.json').read_text())
unused=list(enumerate(r['reconstructed']));plans=[]
for index,(c,o,wp) in enumerate(zip(r['commands'],r['origins'],r['wall_passes'])):
    if c[0]!=2 or c[5]: continue
    record=list(struct.unpack('<8H',struct.pack('<4I',*o[2:6])))
    matches=[(i,x) for i,x in unused if x['source']==c[2] and x['pass_id']==int(bool(wp[1])) and x['record']==record]
    assert len(matches)==1,(index,record,matches)
    i,plan=matches[0];unused.remove((i,plan))
    plans.append(dict(plan,captured_index=index,object_dispatch=None))
assert not unused
# Object-selected wall still uses captured metadata; this test reconstructs queue walls only.
for index,(c,wp) in enumerate(zip(r['commands'],r['wall_passes'])):
    if c[0]==2 and c[5]:plans.append(dict(captured_index=index,source=c[2],pass_id=int(bool(wp[1])),object_dispatch=c[1]))
result=assemble(r['commands'],plans,r['wall_passes'],occurrences=True)
assert result['complete'] and [x['command'] for x in result['commands']]==r['commands']
report=dict(result='PASS',serial=53,native_queue_draws=len(r['reconstructed']),deferred_draws=sum(x['pass_id']==1 for x in r['reconstructed']),record_occurrence_mapping_unique=True,scope='Exact retained pose queue reconstruction; object draw retained from capture. No interpolated occurrence continuity or full-scene proof.')
(p/'repeated-scene-plan-tests.json').write_text(json.dumps(report,indent=2));print(report)
