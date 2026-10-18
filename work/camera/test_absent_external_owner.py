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
folder=Path('G:\\EXTRA DATA DRIVE\\Desktop\\Games\\Codex\\NFSUG-Native-PC-Port\\work\\camera\\prototype-runs\\fullscene-failure-1791305478926527600')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);frames=[];scenes=[]
for name in ('older','newer'):
 raw_supp=(folder/(name+'.supplements.bin')).read_bytes();refresh=struct.unpack_from('<I',raw_supp,8)[0];epoch=struct.unpack_from('<Q',raw_supp,24)[0]
 graph=ClosedGraph(epoch,refresh,GraphPacket.decode((folder/(name+'.graph.bin')).read_bytes()),*((folder/(name+'.'+section+'.bin')).read_bytes() for section in ('objects','callbacks','associations')))
 scenes.append(MotionScene(graph,ClosedSupplements.decode((folder/(name+'.supplements.bin')).read_bytes(),graph,rom),OwnedModelBuilders((folder/(name+'.builders.bin')).read_bytes()),OwnedModelSources.decode((folder/(name+'.current-sources.bin')).read_bytes(),graph)))
 frames.append((folder/(name+'.frame.bin')).read_bytes())
history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)

from owned_model_record_owners import endpoint_model_record_owners
from owned_ordinary_model_visits import ordinary_model_visits
maps=[]
try:
 for e,scene in enumerate(scenes):
  visits=ordinary_model_visits(scene.graph,prepared.pair.portal.sample(e))
  maps.append(endpoint_model_record_owners(scene.graph,visits,frames[e],rom,scene))
 assert maps==[{12:1,13:0},{10:0}],maps
 prepared.sample(.5);next_dependency='live extended-route verification'
 result=dict(result='PASS_ENDPOINT_OWNERSHIP',maps=maps,next_dependency=next_dependency,scope='Exact endpoint ownership; endpoint ownership; projection exit supported by separate native4K reference test')
 Path('work/camera/absent-external-owner-tests.json').write_text(json.dumps(result,indent=2));print(result)
finally:prepared.close();history.close()
