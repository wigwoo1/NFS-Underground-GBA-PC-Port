import runpy
from owned_motion_scene import MotionScene
from owned_closed_supplements import ClosedSupplements
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_model_builder_inputs import OwnedModelBuilders
from owned_motion_pairs import records
import sys
from pathlib import Path
folder=Path(sys.argv[1]);data=runpy.run_path('work/camera/audit_complete_model_transition.py');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();scenes=[]
for endpoint,closed in enumerate(data['scenes']):
 label=('older','newer')[endpoint]
 scenes.append(MotionScene(closed,ClosedSupplements.decode((folder/(label+'.supplements.bin')).read_bytes(),closed,rom),OwnedModelBuilders((folder/(label+'.builders.bin')).read_bytes()),data['sources'][endpoint]))
history=EndpointRoadPlanner(rom,data['table']);roads,_=history.plan(scenes[0].graph)
prepared=PreparedWorldMotion(*data['frames'],*scenes,history,roads,rom);counts=[]
try:
 for alpha in (0,.1,.25,.5,.75,.9,.99,1):
  frame,*_=prepared.sample(alpha);counts.append(sum(r['kind']==3 for r in records(frame)['records']))
  if alpha in (0,1):assert frame==data['frames'][int(alpha)]
 print('PASS retained full-world boundary CPU sampling',counts)
finally:prepared.close();history.close()
