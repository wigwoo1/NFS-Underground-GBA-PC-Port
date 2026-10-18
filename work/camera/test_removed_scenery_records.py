import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
from owned_scenery_record_pairs import prepare_scenery_record_pairs
from owned_removed_scenery_visit import removed_scenery_visit
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791284010890227200.json').read_text());frames=[];scenes=[];rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
for capture in r['model_scene_captures']:
 frame=Path(capture['frame']).read_bytes();frames.append(frame);graph=ClosedGraph.decode(Path(capture['graph']).read_bytes());scenes.append(MotionScene(graph,ClosedSupplements.decode(Path(capture['supplements']).read_bytes(),graph,rom),OwnedModelBuilders(Path(capture['builders']).read_bytes()),OwnedModelSources.decode(Path(capture['current-sources']).read_bytes(),graph)))
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);portal=PortalMotionPair(*(s.graph.graph for s in scenes),table,PreparedMotionPair(*frames));queues=[portal.sample(i) for i in (0,1)]
visit=removed_scenery_visit(*scenes,*queues,31);assert visit['source'][136]==255 and not visit['allocated']
pairs=prepare_scenery_record_pairs(scenes,queues,rom,{31});assert len(pairs)==1 and pairs[0].older_allocated and not pairs[0].newer_allocated
assert len(pairs[0].older_blocks)==len(pairs[0].newer_blocks)==12
print('PASS: source31 complete removal record pair, original inactive source allocation preserved')
