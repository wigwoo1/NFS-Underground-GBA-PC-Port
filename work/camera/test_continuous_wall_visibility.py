import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_scene_bundle import chunks
from owned_complete_supplemental_projection import projection_input
from owned_continuous_wall_visibility import select_wall,endpoint_edge
from owned_wall_projection import projected
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());checks=[]
for f in r['wall_diagnostic_frames']:
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());s=ClosedSupplements.decode(Path(f['supplements']).read_bytes(),c)
 for h,record in chunks(s.geometry,'supplements'):
  bounds=struct.unpack_from('<8H',record,192)[1:5];raw,sources=projection_input(c,s,rom,h[3],bounds)
  exact,stats=projected(c.graph,table,(raw,sources));visible={w.edge:scratch for _,_,w,scratch in exact};ring=b''.join(raw[976+i*140:1044+i*140] for i in range(h[4]))
  for w in sources:
   edge=endpoint_edge(w,ring,c.graph.context[256:304]);base=raw[1076+w.edge*140:1108+w.edge*140]
   out=select_wall(w,raw[32:80],edge,c.graph.context[304:368],bounds,base,table)
   assert out.visible==(w.edge in visible),(c.refresh,w.edge,out)
   if out.visible:
    scratch=visible[w.edge];assert out.x==struct.unpack_from('<2h',scratch) and out.y==struct.unpack_from('<4h',scratch,8) and out.flags==struct.unpack_from('<H',scratch,48)[0]
   checks.append(dict(refresh=c.refresh,descriptor=h[3],edge=w.edge,reason=out.reason))
out=dict(result='PASS_CONTINUOUS_WALL_ENDPOINT_VISIBILITY',edges=len(checks),checks=checks,scope='Integer camera-space endpoint agreement with native selector. Sampled camera-space extension and near-plane transition oracle remain pending.')
Path('work/camera/continuous-wall-visibility-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks))
