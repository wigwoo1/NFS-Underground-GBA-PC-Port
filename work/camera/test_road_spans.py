"""Original road edge setup span destinations; texture writers remain stubbed."""
from pathlib import Path
import json
p=Path('work/camera');cases=[]
for alpha in ('0.25','0.5','0.75'):
 data=json.loads((p/f'road-clip-inputs-{alpha}-motion-spans.json').read_text());spans=0;rows=[];routines=set();overflow=0
 trace=json.loads((p/f'sampled-object-dispatch-{alpha}-motion-spans-tests.json').read_text());control=json.loads((p/f'sampled-object-dispatch-{alpha}-motion-tests.json').read_text());assert trace['draws']==control['draws'] and trace['calls']==control['calls']
 for c in data['cases']:
  base,_,_,stride=c['framebuffer'];assert stride==240
  l,r,t,b=c['bounds']
  for s in c.get('spans',[]):
   params=s['params'];delta=params[6]-base;assert delta>=0
   y,byte_x=divmod(delta,stride);assert t<=y<=b,(alpha,c['source'],y,c['bounds'])
   assert byte_x%2==0 and params[7]>0
   spans+=1;rows.append(y);routines.add(s['routine'])
   # ARM edge setup uses x>>17 and adds 2 to width; track its inferred
   # doubled-coordinate end separately, without claiming final pixel parity.
   overflow+=int(byte_x+params[7]*2>r)
 assert spans>0
 cases.append(dict(alpha=float(alpha),roads=len(data['cases']),spans=spans,first_row=min(rows),last_row=max(rows),routines=sorted(routines),inferred_ends_beyond_right_bound=overflow,draw_order_unchanged=True))
report=dict(result='PASS',cases=cases,scope='Original road edge setup executes; both span texture writers stubbed. Destinations obey inherited vertical inclusive limits with240-byte stride. Horizontal end inference exposes padded spans; final writes, edge inclusion and native coverage parity remain unverified.')
(p/'road-span-tests.json').write_text(json.dumps(report,indent=2));print(report)

