import runpy,sys
from pathlib import Path
from owned_motion_scene import MotionScene
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_record_builder import ModelRecordBuilder
from owned_removed_scenery_visit import depth_hidden_scenery_visit
from owned_scenery_motion import PreparedSceneryMotion
from owned_scenery_record_pairs import SceneryRecordPair
import json
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791284332775142300.json').read_text());folder=Path(r['full_scene_failure_capture']['folder']);sys.argv=['audit',str(folder)];v=runpy.run_path('work/camera/audit_complete_model_transition.py');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();scenes=[]
for i,label in enumerate(('older','newer')):
 graph=v['scenes'][i];scenes.append(MotionScene(graph,ClosedSupplements.decode((folder/(label+'.supplements.bin')).read_bytes(),graph,rom),OwnedModelBuilders((folder/(label+'.builders.bin')).read_bytes()),v['sources'][i]))
queues=[v['portal'].sample(i) for i in (0,1)];builder=ModelRecordBuilder(rom);pairs=[]
for index in (34,37):
 visit=depth_hidden_scenery_visit(*scenes,*queues,index);assert visit['allocated'] and visit['depth']<=0
 old=builder.prepare_visit(scenes[0],queues[0],v['visits'][0][index]);new=builder.prepare_depth_hidden(*scenes,*queues,index)
 assert all(old[k]==new[k] for k in (1,4,5,6,7,8,10));pairs.append(SceneryRecordPair(index,old,new,True,True))
motion=PreparedSceneryMotion(pairs,scenes[0].graph.graph.context[256:304],scenes[1].graph.graph.context[256:304])
for index in (34,37):assert len({motion.matrix(index,i/100) for i in range(101)})==101
print('PASS: two allocated depth-hidden records, exact topology/material, 202 non-held source pose samples')
