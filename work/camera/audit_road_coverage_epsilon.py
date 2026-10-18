from pathlib import Path
import ctypes as C,json
from actual_road_interval_geometry import interval_ring,bounds
from road_scheduled_coverage import scheduled_spans,coverage_buffer
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes())
failed=[v for v in json.loads((p/'road-scheduled-coverage-limits.json').read_text())['checks'] if v['maximum_alpha_gap']>=1e-5];checks=[]
for case in failed:
 cmd,begin,center=case['command'],case['begin_a'],case['phase'];a=interval_ring(cmd,begin,0.,table);b=interval_ring(cmd,begin,1.,table);samples=[]
 for epsilon in (1e-6,1e-7,1e-8,1e-9,1e-10,1e-11):
  values=[]
  for phase in (center-epsilon,center+epsilon):
   ring=interval_ring(cmd,begin,phase,table);buf=coverage_buffer(scheduled_spans(a,b,ring,bounds[cmd],table,phase));values.append([sum(v[3] for v in items) for items in buf])
  gaps=[abs(x-y) for x,y in zip(*values)];pixel=max(range(len(gaps)),key=gaps.__getitem__);samples.append(dict(epsilon=epsilon,maximum_gap=gaps[pixel],pixel=pixel,estimated_slope=gaps[pixel]/(2*epsilon)))
 ratios=[samples[i+1]['maximum_gap']/samples[i]['maximum_gap'] for i in range(len(samples)-1)]
 checks.append(dict(case=case,samples=samples,shrink_ratios=ratios,finite_slope_evidence=all(.08<r<.12 for r in ratios)))
r=dict(result='PASS_FINITE_SLOPE_EVIDENCE' if checks and all(v['finite_slope_evidence'] for v in checks) else 'UNRESOLVED',checks=checks,scope='Localized epsilon scaling only; no global continuity or gameplay claim.')
(p/'road-coverage-epsilon-audit.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
