"""Original road-entry clipping evidence; does not prove raster pixel coverage."""
from pathlib import Path
import json
p=Path('work/camera');cases=[]
for alpha in ('0.25','0.5','0.75'):
 data=json.loads((p/f'road-clip-inputs-{alpha}-motion.json').read_text());boundary=0;vertices=0;outside_vertical=0
 for c in data['cases']:
  l,r,t,b=c['bounds'];assert c['state_limits']==[t,b]
  for v in c['vertices']:
   x,y=v[:2];assert l<=x<=r,(alpha,c['source'],v,c['bounds']);outside_vertical+=int(y<t or y>b)
   vertices+=1;boundary+=int(x in (l,r) or y in (t,b))
 assert boundary>0
 cases.append(dict(alpha=float(alpha),roads=len(data['cases']),vertices=vertices,boundary_vertices=boundary,vertices_outside_vertical_bounds=outside_vertical))
report=dict(result='PASS',cases=cases,scope='Original road-entry polygon vertices satisfy horizontal bounds; some remain outside vertical bounds. State carries inherited top/bottom limits for scanline clipping. Edge inclusion, native polygon parity and pixel coverage remain unverified.')
(p/'road-clip-input-tests.json').write_text(json.dumps(report,indent=2));print(report)

