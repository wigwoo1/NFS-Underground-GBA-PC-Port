import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_scene_bundle import chunks
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());checks=[]
for f in r['wall_diagnostic_frames']:
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());s=ClosedSupplements.decode(Path(f['supplements']).read_bytes(),c)
 texture_indices={}
 for _,raw in chunks(s.textures,'textures'):
  h=struct.unpack_from('<12I',raw);texture_indices.setdefault(h[5],set()).update(raw[120:])
 palettes=[(h[3],raw[464:976]) for h,raw in chunks(s.geometry,'supplements')]
 changed={i for _,p in palettes for i in range(256) if p[i*2:i*2+2]!=c.graph.context[384+i*2:386+i*2]}
 varying={i for i in range(256) if len({p[i*2:i*2+2] for _,p in palettes})>1}
 checks.append(dict(refresh=c.refresh,descriptors=[d for d,_ in palettes],changed_from_graph=sorted(changed),varying_between_calls=sorted(varying),materials=[dict(index=mi,used_indices=sorted(ids),varying_used=sorted(ids&varying),changed_used=sorted(ids&changed)) for mi,ids in sorted(texture_indices.items())]))
report=dict(result='SUPPLEMENTAL_PALETTE_USAGE_AUDIT',checks=checks,scope='All texel indices and captured draw palette versions; confirms color dependencies, does not derive palette writes.')
Path('work/camera/supplemental-palette-usage-audit.json').write_text(json.dumps(report,indent=2));print([(x['refresh'],len(x['varying_between_calls']),[(m['index'],len(m['varying_used']),len(m['changed_used'])) for m in x['materials']]) for x in checks])
