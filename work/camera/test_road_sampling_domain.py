from pathlib import Path
import json
p=Path('work/camera');cases=[];distinct=set()
for alpha in ['0.25','0.5','0.75']:
 spans=0;roads=0
 for c in json.loads((p/f'road-clip-inputs-{alpha}-motion-spans.json').read_text())['cases']:
  rows=c.get('spans',[])
  if rows:roads+=1
  for s in rows:
   a=s['params'];shift=a[0];assert 1<=shift<=10
   assert a[1]==(1<<(shift+15))-1
   height=(a[2]+1)>>16;assert height and not(height&(height-1)) and a[2]==(height<<16)-1
   assert (((a[1]>>16)+1)*2)==1<<shift
   distinct.add((shift,height,a[5]));spans+=1
 cases.append(dict(alpha=float(alpha),roads=roads,spans=spans))
report=dict(result='PASS',cases=cases,distinct_texture_domains=len(distinct),scope='All retained scene171 span traces at three interpolation phases satisfy half-row packed sampling domain; not full-route/material coverage.')
(p/'road-sampling-domain-tests.json').write_text(json.dumps(report,indent=2));print(report)
