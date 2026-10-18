from pathlib import Path
import json
p=Path('work/camera');a=json.loads((p/'stable-road-projected-inputs.json').read_text());b=json.loads((p/'stable-road-projected-policy-5.json').read_text());changed=0;unchanged=0
for x,y in zip(a['checks'],b['checks']):
 assert x['surface']==y['surface'];assert len(x['triangles'])==len(y['triangles'])
 for v,w in zip(x['triangles'],y['triangles']):
  assert v[2:]==w[2:]
  if v[2]!=64:assert v==w;unchanged+=1
  else:
   for k in range(2):assert abs(w[k]-(a['projection'][k]+(v[k]-a['projection'][k])*64*258111/16777216))<1e-8
   changed+=1
assert a['checks'][0]['triangles']==b['checks'][0]['triangles'];print(dict(result='PASS',near_triangle_occurrences_changed=changed,retained_occurrences_unchanged=unchanged,depth_uv_unchanged=True,unclipped_road_exact=True))
