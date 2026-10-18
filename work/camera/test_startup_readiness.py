import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_graph_packet import GraphPacket
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);frames=[];scenes=[]
for name in ('older','newer'):
 raw_supp=(folder/(name+'.supplements.bin')).read_bytes();refresh=struct.unpack_from('<I',raw_supp,8)[0];epoch=struct.unpack_from('<Q',raw_supp,24)[0]
 graph=ClosedGraph(epoch,refresh,GraphPacket.decode((folder/(name+'.graph.bin')).read_bytes()),*((folder/(name+'.'+section+'.bin')).read_bytes() for section in ('objects','callbacks','associations')))
 scenes.append(MotionScene(graph,ClosedSupplements.decode((folder/(name+'.supplements.bin')).read_bytes(),graph,rom),OwnedModelBuilders((folder/(name+'.builders.bin')).read_bytes()),OwnedModelSources.decode((folder/(name+'.current-sources.bin')).read_bytes(),graph)))
 frames.append((folder/(name+'.frame.bin')).read_bytes())
history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)


from owned_world_startup_candidate import WorldPreparationService
from owned_sample_signature import signature
service=WorldPreparationService(rom,2);result=None
try:
 evidence=service.warm_start(frames[0],scenes[0]);assert evidence['refresh']==scenes[0].identity[1] and evidence['epoch']==scenes[0].identity[0]
 assert evidence['worker']!=__import__('threading').get_ident();assert service.pipeline.ready=={}
 try:service.warm_start(frames[0],scenes[0])
 except ValueError:pass
 else:raise AssertionError('Repeated startup accepted')
 assert service.history.refresh==scenes[0].identity[1] and service.pipeline.ready=={}
 corrupted=bytearray(frames[0]);corrupted[4]^=1
 try:service.warm_start(bytes(corrupted),scenes[0])
 except ValueError:pass
 else:raise AssertionError('Mismatched startup accepted')
 future=service.submit((frames[0],scenes[0]),(frames[1],scenes[1]))
 result=service.take(future)
 for alpha in (.1,.25,.5,.9):assert signature(result.sample(alpha))==signature(prepared.sample(alpha))
 out=dict(result='PASS_FIRST_BOUNDARY_READINESS',evidence=evidence,signature_checks=4,scope='Captured first boundary only, original history remains at older refresh until normal submit; no simulation advance/live timing proof')
 Path('work/camera/startup-readiness-tests.json').write_text(json.dumps(out,indent=2));print(out)
finally:
 if result is not None:result.close()
 service.close();prepared.close();history.close()
