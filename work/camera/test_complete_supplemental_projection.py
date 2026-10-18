import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_scene_bundle import chunks
from owned_graph_wall_sources import supplemental_wall_sources
from owned_complete_supplemental_projection import project_complete
from owned_wall_projection import projected
from types import SimpleNamespace
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());checks=[]
for f in r['wall_diagnostic_frames']:
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());s=ClosedSupplements.decode(Path(f['supplements']).read_bytes(),c)
 proxy=SimpleNamespace(supplements=s.geometry,textures=s.textures,validate=lambda:None);sources=supplemental_wall_sources(proxy)
 for h,raw in chunks(s.geometry,'supplements'):
  bounds=struct.unpack_from('<8H',raw,192)[1:5]
  actual=projected(c.graph,table,(raw,tuple(w for w in sources if w.descriptor==h[3])))
  recovered=project_complete(c,s,rom,h[3],bounds,table)
  assert actual==recovered
  checks.append(dict(refresh=c.refresh,descriptor=h[3],visible_edges=len(recovered[0]),stats=recovered[1]))
out=dict(result='PASS_COMPLETE_SUPPLEMENTAL_ENDPOINT_PROJECTION',invocations=len(checks),checks=checks,scope='Original-pose complete-source nearclip/frontface/material/viewport selection matches captured supplemental geometry inputs. Intermediate continuous clipping and live GPU insertion remain pending.')
Path('work/camera/complete-supplemental-projection-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks))
