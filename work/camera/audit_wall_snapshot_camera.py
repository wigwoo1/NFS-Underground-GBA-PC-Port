import sys,json,struct,hashlib
from pathlib import Path
sys.path.insert(0,'work/camera');s={};exec(Path('work/camera/test_source_transition_adapter.py').read_text().split('table=struct.unpack',1)[0],s)
checks=[]
for label,frame,scene in zip(('older','newer'),s['frames'],s['scenes']):
 camera=scene.graph.graph.context[256:304];rows=s['records'](frame)['records'];items=[]
 for r in rows:
  if r['kind']!=2:continue
  items.append(dict(source=hashlib.sha256(r['blocks'][0]).hexdigest(),camera_matches_graph=bytes(r['blocks'][3])==camera,camera=list(struct.unpack('<12i',r['blocks'][3])),clip=list(struct.unpack('<4H',r['blocks'][5])),flags=struct.unpack_from('<H',r['blocks'][10],48)[0]))
 checks.append(dict(endpoint=label,refresh=scene.graph.refresh,graph_camera=list(struct.unpack('<12i',camera)),walls=items))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-snapshot-camera-20261007');cp.mkdir(exist_ok=True);(cp/'camera.json').write_text(json.dumps(checks,indent=2));print(json.dumps([dict(endpoint=x['endpoint'],walls=len(x['walls']),matches=sum(w['camera_matches_graph'] for w in x['walls']),graph_camera=x['graph_camera'],distinct_wall_cameras=list({tuple(w['camera']) for w in x['walls']})) for x in checks],indent=2))
