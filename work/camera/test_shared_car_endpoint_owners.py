import json,struct,sys
from pathlib import Path
from types import SimpleNamespace
from owned_closed_graph import ClosedGraph
from owned_model_builder_inputs import OwnedModelBuilders
from owned_motion_visibility import PortalMotionPair
from sample_owned_motion import PreparedMotionPair
from owned_ordinary_model_visits import ordinary_model_visits
from owned_model_record_owners import endpoint_model_record_owners
r=json.loads(Path(sys.argv[1]).read_text());captures=r['model_scene_captures']
scenes=[ClosedGraph.decode(Path(c['graph']).read_bytes()) for c in captures]
frames=[Path(c['frame']).read_bytes() for c in captures]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);evidence=[]
for e,(scene,capture) in enumerate(zip(scenes,captures)):
 a,b=sorted((e,1 if e==0 else e-1))
 portal=PortalMotionPair(scenes[a].graph,scenes[b].graph,table,PreparedMotionPair(frames[a],frames[b]))
 visits=ordinary_model_visits(scene,portal.sample(int(e==b)))
 owned=SimpleNamespace(builders=OwnedModelBuilders(Path(capture['builders']).read_bytes()))
 owners=endpoint_model_record_owners(scene,visits,frames[e],rom,owned)
 assert 0 in owners.values()
 assert (1 in owners.values())==(e>=2)
 assert len(owners)==len(set(owners.values()))
 evidence.append(dict(refresh=scene.refresh,owners=owners))
Path(sys.argv[1]).with_suffix('.shared-endpoint-owners.json').write_text(json.dumps(evidence,indent=2))
print('PASS four complete endpoint ownership maps, both shared-mesh cars distinct')
