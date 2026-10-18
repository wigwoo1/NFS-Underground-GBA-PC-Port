import sys,json
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_model_builder_inputs import OwnedModelBuilders
from owned_external_model_owners import external_model_owners
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
report=json.loads(Path(sys.argv[1]).read_text());found=[]
for capture in report['model_scene_captures']:
 closed=ClosedGraph.decode(Path(capture['graph']).read_bytes());builders=OwnedModelBuilders(Path(capture['builders']).read_bytes());frame=Path(capture['frame']).read_bytes()
 owners=external_model_owners(closed,builders,frame,rom)
 if owners:
  assert set(owners.values())=={1};assert 0 not in owners.values();found.append(dict(refresh=capture['refresh'],owners=dict(owners)))
assert len(found)==2,found
Path(sys.argv[1]).with_suffix('.external-owners.json').write_text(json.dumps(found,indent=2))
print('PASS two visible opponent draws resolve to source1 independently from shared player mesh')
