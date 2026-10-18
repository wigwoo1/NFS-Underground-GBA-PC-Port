from pathlib import Path
import ctypes as C,json
from actual_road_interval_geometry import interval_ring,bounds
from road_scheduled_coverage import scheduled_spans,coverage_buffer
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());intervals=json.loads((p/'road-actual-temporal-domain-tests.json').read_text())['checks'];checks=[]
for item in intervals:
 cmd,begin=item['command'],item['begin_a'];a=interval_ring(cmd,begin,0.,table);b=interval_ring(cmd,begin,1.,table)
 for center in (.25,.5,.75):
  values=[]
  for phase in (center-1e-8,center+1e-8):
   current=interval_ring(cmd,begin,phase,table);buffer=coverage_buffer(scheduled_spans(a,b,current,bounds[cmd],table,phase));values.append([sum(v[3] for v in items) for items in buffer])
  gap=max(abs(x-y) for x,y in zip(*values));checks.append(dict(command=cmd,begin_a=begin,phase=center,maximum_alpha_gap=gap))
report=dict(result='PASS_SAMPLED_COVERAGE_LIMITS' if all(c['maximum_alpha_gap']<1e-5 for c in checks) else 'REJECTED_SAMPLED_COVERAGE_LIMITS',checks=checks,scope='All38400destination alpha limits across18actualgame matrix/world/source/clip intervals at quarter/mid/threequarter phases +/-1e-8. No fullphase/globalcontinuity/texture/material/GPU/fullscene gameplay proof.')
(p/'road-scheduled-coverage-limits.json').write_text(json.dumps(report,indent=2));print(report['result'],max(v['maximum_alpha_gap'] for v in checks))
