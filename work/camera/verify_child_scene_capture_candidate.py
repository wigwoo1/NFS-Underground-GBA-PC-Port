"""Reconstruct captured closed scenes and verify endpoint identity and history."""
import sys,json,hashlib
from pathlib import Path
folder=Path(sys.argv[1]);manifest=json.loads((folder/'manifest.json').read_text())
for name,item in manifest['files'].items():
 data=(folder/name).read_bytes()
 assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
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

rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);frames=[];scenes=[]
for name in ('older','newer'):
 raw_supp=(folder/(name+'.supplements.bin')).read_bytes();refresh=struct.unpack_from('<I',raw_supp,8)[0];epoch=struct.unpack_from('<Q',raw_supp,24)[0]
 graph=ClosedGraph(epoch,refresh,GraphPacket.decode((folder/(name+'.graph.bin')).read_bytes()),*((folder/(name+'.'+section+'.bin')).read_bytes() for section in ('objects','callbacks','associations')))
 scenes.append(MotionScene(graph,ClosedSupplements.decode((folder/(name+'.supplements.bin')).read_bytes(),graph,rom),OwnedModelBuilders((folder/(name+'.builders.bin')).read_bytes()),OwnedModelSources.decode((folder/(name+'.current-sources.bin')).read_bytes(),graph)))
 frames.append((folder/(name+'.frame.bin')).read_bytes())
from owned_road_history_diagnostic import restore
from owned_road_record_diagnostic import decode
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()))
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
prepared=None
try:
 for frame,scene in zip(frames,scenes):scene.match(frame)
 assert [list(x.identity) for x in scenes]==[manifest['older'],manifest['newer']]
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 phases=[0,.125,.25,.375,.5,.625,.75,.875,1]
 samples=[]
 for alpha in phases:
  frame,*rest=prepared.sample(alpha)
  if alpha==0:assert frame==frames[0]
  if alpha==1:assert frame==frames[1]
  samples.append(dict(alpha=alpha,frame_bytes=len(frame),sha256=hashlib.sha256(frame).hexdigest()))
 result=dict(result='PASS_CLOSED_SCENE_HISTORY_RECONSTRUCTION',capture=str(folder.resolve()),older=manifest['older'],newer=manifest['newer'],samples=samples,scope='Closed source reconstruction and endpoint equality; native GPU pixels and original-game fidelity pending')
 Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result['result'],result['older'],result['newer'])
finally:
 if prepared is not None:prepared.close()
 history.close()
