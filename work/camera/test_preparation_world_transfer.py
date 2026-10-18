import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_graph_packet import GraphPacket
from owned_closed_supplements import ClosedSupplements
from owned_complete_supplemental_candidates import CompleteSupplementalCandidates
from owned_complete_supplemental_gpu import endpoint_gpu_records
from owned_live_wall_adapter import reconstruct
from owned_motion_visibility import PortalMotionPair
from sample_owned_motion import PreparedMotionPair
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791276350925813100.json').read_text());folder=Path(report['full_scene_failure_capture']['folder']);scenes=[];supp=[];frames=[]
for label in ('older','newer'):
 frame=(folder/(label+'.frame.bin')).read_bytes();frames.append(frame);scene=ClosedGraph(struct.unpack_from('<Q',frame,24)[0],struct.unpack_from('<I',frame,4)[0],GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes()),*( (folder/(label+'.'+field+'.bin')).read_bytes() for field in ('objects','callbacks','associations')));scenes.append(scene);supp.append(ClosedSupplements.decode((folder/(label+'.supplements.bin')).read_bytes(),scene))
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);portal=PortalMotionPair(*(s.graph for s in scenes),table,PreparedMotionPair(*frames));pair=CompleteSupplementalCandidates(*scenes,*supp,portal,rom)

from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates


from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_sampled_road_sequence import SampledRoadSequence
from dataclasses import replace

from owned_preparation_pipeline import PreparationPipeline
from owned_prepared_world_motion import PreparedWorldMotion
from owned_motion_scene import MotionScene
history=EndpointRoadPlanner(rom,table);pipeline=PreparationPipeline(1);prepared=None;reference=None
try:
 old_roads,_=history.plan(scenes[0]);owned_history=history.fork();owned_scenes=[MotionScene(a,b) for a,b in zip(scenes,supp)]
 def factory():
  try:return PreparedWorldMotion(*frames,*owned_scenes,owned_history,old_roads,rom)
  finally:owned_history.close()
 future=pipeline.submit(factory);prepared=pipeline.take(future)
 reference=PreparedWorldMotion(*frames,*owned_scenes,history,old_roads,rom)
 from owned_precomputed_world_samples import PrecomputedWorldSamples
 prepared=PrecomputedWorldSamples(prepared,(0,.25,.5,.75,1))
 for alpha in (0,.25,.5,.75,1):
  a=prepared.sample(alpha);b=reference.sample(alpha)
  assert a[0]==b[0] and a[4]==b[4] and list(a[3])==list(b[3])
  assert (list(a[1]) if a[1] is not None else None)==(list(b[1]) if b[1] is not None else None)
  assert (list(a[2]) if a[2] is not None else None)==(list(b[2]) if b[2] is not None else None)
 print('PASS worker prepared fullscene equals synchronous frame/camera/model/clip samples at five alphas')
finally:
 if prepared is not None:prepared.close()
 if reference is not None:reference.close()
 pipeline.close();history.close()
