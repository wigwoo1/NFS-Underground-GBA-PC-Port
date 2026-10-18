import runpy,json
from pathlib import Path
s=Path('work/camera/audit_multicar_source_identity.py').read_text().replace('1791277545531619000','1791279197554947500')
v={};exec(compile(s,'new_population_fixture','exec'),v)
from owned_scene_bundle import chunks
import struct
population=[]
for scene in v['scenes']:
 sources={}
 for h,raw in chunks(scene.objects,'graph_objects'):
  for i in range(h[5]):
   index=struct.unpack_from('<I',raw,128+i*168)[0];source=raw[132+i*168:296+i*168]
   sources[index]=dict(parent=h[3],model=struct.unpack_from('<h',source,54)[0],flags=list(struct.unpack_from('<2H',source,8)),active=struct.unpack_from('<H',source,72)[0],slot=source[136])
 population.append(sources)
(v['folder']/'ordinary-source-population.json').write_text(json.dumps(population,indent=2));print('source models', [{k:x for k,x in s.items() if x['model'] in (7,31,32,33,34,35,36)} for s in population])
