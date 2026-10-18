from pathlib import Path
from normalize_source_triangle_packets_candidate import normalize
import json
p=Path('work/camera/prototype-runs');r=normalize((p/'source-clip-packet-records.bin').read_bytes(),(p/'source-clip-packet-payload.bin').read_bytes());draws=[x for x in r['ops'] if x['op']=='draw_triangles' and x['source_primitive']==4 and not x['program']]
assert len(draws)==221
for d in draws:
 s=d['state'];assert set(s['enabled'])=={0xbc0,0xc11,0xde1};assert s['alpha']==[516,.5];assert all(v[6:10]==[1,1,1,1] for v in d['vertices'])
 sampler=d['textures']['0']['sampler'];assert sampler[10240]==sampler[10241]==9728;assert sampler.get(10242,10497)==sampler.get(10243,10497)==10497
result=dict(result='PASS_SOURCE_GEOMETRY_DRAW_STATE_AUDIT',draws=len(draws),sampling='nearest, repeat both axes',alpha='greater than 0.5',blend_enabled=False,vertex_rgba=[1,1,1,1],scope='221 actual source geometry draw commands in five fixture frames; broader routes and sky/HUD not covered.')
(p/'source-material-state-audit.json').write_text(json.dumps(result,indent=2));print(result)

