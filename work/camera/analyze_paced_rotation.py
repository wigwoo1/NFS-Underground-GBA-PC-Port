from pathlib import Path
import csv,json,math,statistics
p=Path('work/camera');rows=[r for r in csv.DictReader((p/'paced-retained-rotation.csv').open()) if r['ready']=='1'];report={'fresh_samples':len(rows)}
for obj in ['camera','object']:
 q=[tuple(float(r[obj+'_q'+a]) for a in 'xyzw') for r in rows];norm=[math.sqrt(sum(v*v for v in x)) for x in q];assert all(math.isfinite(n) and abs(n-1)<1e-8 for n in norm)
 groups={'within_pair':[],'pair_change':[]}
 for i in range(1,len(rows)):
  assert float(rows[i]['target'])>float(rows[i-1]['target'])
  dot=abs(sum(a*b for a,b in zip(q[i-1],q[i]))/(norm[i-1]*norm[i]));angle=math.degrees(2*math.acos(min(1,dot)))
  boundary=(rows[i]['older'],rows[i]['newer'])!=(rows[i-1]['older'],rows[i-1]['newer']);groups['pair_change' if boundary else 'within_pair'].append(angle)
 report[obj]={'max_quaternion_norm_error':max(abs(n-1) for n in norm),'degrees_per_display':{k:{'intervals':len(v),'median':statistics.median(v),'max':max(v),'nonzero':sum(x>1e-5 for x in v)} for k,v in groups.items()}}
report['scope']='Input pose angular-step diagnostic; no universal smoothness threshold, geometry/visibility continuity not tested.'
(p/'paced-rotation-tests.json').write_text(json.dumps(report,indent=2));print(report)
