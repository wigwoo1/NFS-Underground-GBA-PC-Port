from pathlib import Path
import json
p=Path('work/camera');a=json.loads((p/'stable-road-projected-inputs.json').read_text());b=json.loads((p/'stable-road-projected-policy-6.json').read_text());changed=retained=0
for x,y in zip(a['checks'],b['checks']):
 assert x['surface']==y['surface'];assert len(x['triangles'])==len(y['triangles'])
 for v,w in zip(x['triangles'],y['triangles']):
  assert v[2:]==w[2:]
  if v[2]!=64:assert v==w;retained+=1
  else:assert v[:2]!=w[:2];changed+=1
assert a['checks'][0]['triangles']==b['checks'][0]['triangles'];assert changed==8 and retained==25
print(dict(result='PASS',changed_near_occurrences=changed,unchanged_retained_occurrences=retained,all_depth_uv_unchanged=True,unclipped_surface_exact=True,scope='Reciprocal positional interpolation extension only; displacement truncation/wrapping not modeled. No original fixedpoint endpoint parity claim.'))
