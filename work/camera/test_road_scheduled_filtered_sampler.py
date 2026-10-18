from pathlib import Path
import ctypes as C,json
from actual_road_interval_geometry import interval_ring,bounds
from road_scheduled_sampler import sample_filtered_buffer as sample_buffer
from road_lattice_sampler import sample_contributor_buffer,compose_palette
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());palettes=(p/'stable-road-display-palettes.bin').read_bytes();checks=[]
for item in json.loads((p/'road-actual-temporal-domain-tests.json').read_text())['checks']:
 cmd,begin=item['command'],item['begin_a'];a=interval_ring(cmd,begin,0.,table);b=interval_ring(cmd,begin,1.,table);texture=(p/f'road-{cmd}-index-texture.bin').read_bytes();normalization=(128,256 if cmd==4 else 64)
 for phase in (0.,.5,1.):
  ring=interval_ring(cmd,begin,phase,table);colors=sample_buffer(a,b,ring,bounds[cmd],table,phase,texture,normalization,palettes)
  assert all(all(0<=v<=255+1e-9 for v in c[:3]) and 0<=c[3]<=1+1e-9 for c in colors)
  exact=None
  if phase in (0.,1.):
   original=sample_contributor_buffer(ring,bounds[cmd],texture,normalization,table);expected=[compose_palette(v,palettes[(d//240)*512:(d//240+1)*512]) for d,v in enumerate(original)];exact=colors==expected;assert exact
  checks.append(dict(command=cmd,begin=begin,phase=phase,endpoint_reference_exact=exact))
r=dict(result='PASS_SCHEDULED_FILTERED_COMPONENT',checks=checks,endpoint_pixels=36*38400,interior_pixels=18*38400,scope='Endpoint parity with independent original writer/UV evaluator. Retained display palette; per-scene material palette fidelity and interior texture continuity unverified. No gameplay proof.')
(p/'road-scheduled-filtered-sampler-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],r['endpoint_pixels'],r['interior_pixels'])
