"""Original road texture writer coverage in private scratch VRAM."""
from pathlib import Path
import json,hashlib,struct
p=Path('work/camera');cases=[]
for alpha in ('0.25','0.5','0.75'):
 data=json.loads((p/f'road-clip-inputs-{alpha}-motion-writes.json').read_text())
 trace=json.loads((p/f'sampled-object-dispatch-{alpha}-motion-writes-tests.json').read_text());control=json.loads((p/f'sampled-object-dispatch-{alpha}-motion-tests.json').read_text());assert trace['draws']==control['draws'] and trace['calls']==control['calls']
 calls=0;coverage=set();outside=0;right=bottom=0;roads=[]
 for c in data['cases']:
  base,_,_,stride=c['framebuffer'];assert stride==240
  l,r,t,b=c['bounds'];pixels=set()
  for address,size in c.get('writes',[]):
   assert size==2 and address%2==0 and 0x06000000<=address<0x06020000
   y,x=divmod(address-base,stride);assert 0<=y<160 and 0<=x<240 and x%2==0
   pixels.add((y,x));coverage.add((y,x));calls+=1
   outside+=int(x<l or x+2>r or y<t or y>=b)
   right=max(right,x+2-r);bottom=max(bottom,y-b)
  roads.append(dict(source=c['source'],writes=len(c.get('writes',[])),unique_pixels=len(pixels)))
 assert calls>0 and outside>0
 digest=hashlib.sha256(b''.join(struct.pack('<2H',*v) for v in sorted(coverage))).hexdigest()
 cases.append(dict(alpha=float(alpha),write_calls=calls,unique_16bit_samples=len(coverage),writes_outside_half_open_bounds=outside,max_right_coordinate_excess=right,max_bottom_row_excess=bottom,coverage_sha256=digest,roads=roads,draw_order_unchanged=True))
report=dict(result='PASS',cases=cases,scope='Original road raster routines execute in isolated scratch VRAM. 16bit write addresses verified inside framebuffer; inherited half-open rectangle does not contain all writes. Native high-resolution clipping, texture palette parity, live rendering and timing remain unverified.')
(p/'road-write-tests.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='cases'});print([{k:v for k,v in c.items() if k!='roads'} for c in cases])
