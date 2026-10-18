"""Validate road writer footprint and derive per-occurrence raster bounds."""
from pathlib import Path
import json
p=Path('work/camera');cases=[]
for alpha in ('0.25','0.5','0.75'):
 data=json.loads((p/f'road-clip-inputs-{alpha}-motion-writes-full.json').read_text());roads=[]
 for c in data['cases']:
  base,_,_,stride=c['framebuffer'];expected=set();doubled=0
  for span in c.get('spans',[]):
   if span['routine']!=0x030056d8:continue
   v=span['params'];doubled+=bool(span['doubled'])
   for x in range(v[7]):
    address=v[6]+x*2;expected.add(address)
    if span['doubled']:expected.add(address+stride)
  actual={a for a,size in c.get('writes',[])};assert all(size==2 for a,size in c.get('writes',[]));
  context_complete=actual==expected
  assert context_complete,(alpha,c["source"],len(actual),len(expected))


  pixels=[divmod(a-base,stride) for a in actual]
  l,r,t,b=c['bounds']
  native_bottom=c['native_bottom_cell_end'];assert native_bottom==max((y+1 for y,x in pixels),default=0)
  envelope=[min((x for y,x in pixels),default=l),max((x+2 for y,x in pixels),default=r),min((y for y,x in pixels),default=t),max((y+1 for y,x in pixels),default=b)]
  assert all(0<=y<160 and 0<=x<240 for y,x in pixels)
  roads.append(dict(native_bottom_cell_end=native_bottom,context_footprint_verified=context_complete,owner=c['owner'],source=c['source'],inherited_bounds=c['bounds'],raster_envelope=envelope,unique_samples=len(actual),doubled_subspans=doubled,bottom_extension=max(0,envelope[3]-b)))
 cases.append(dict(alpha=float(alpha),roads=roads,total_samples=sum(r['unique_samples'] for r in roads)))
report=dict(result='PASS',cases=cases,scope='Exact road source-write envelopes and affine subspan footprints for all occurrences; nonroad writes excluded by road entry/return lifetime. Raster envelopes are per occurrence evidence, not a high-resolution clipping prescription or native eligibility proof.')
(p/'road-coverage-envelope-tests.json').write_text(json.dumps(report,indent=2))
print([(c['alpha'],c['total_samples'],max(r['bottom_extension'] for r in c['roads'])) for c in cases])


