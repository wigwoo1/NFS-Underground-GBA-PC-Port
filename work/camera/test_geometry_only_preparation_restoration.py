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

from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples
history.close();full_frames=tuple(frames);reference=None
from owned_geometry_tail_capability_candidate import GeometryTailOwners
capability=GeometryTailOwners(7,full_frames)
for reduced in (False,True):
 frames=[]
 for key,frame in enumerate(full_frames):
  frames.append(capability.geometry(7,key) if reduced else frame)
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
 prepared=samples=None
 try:
  prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
  samples=ProgressiveSourceWorldSamples(prepared,(.125,.25,.375,.5,.625,.75,.875))
  values=[]
  for alpha in samples.samples:
   frame,camera,models,bounds,detail=samples.sample(alpha);packed=samples.source_masks[alpha]
   if reduced:
    frame=bytes(capability.restore(7,0,frame))
   values.append((frame,bytes(camera),bytes(models),bytes(bounds),detail,bytes(packed[0]),bytes(packed[1]),packed[2:]))
  if reference is None:reference=values
  else:assert values==reference
 finally:
  if samples:samples.close()
  if prepared:prepared.close()
  history.close()
bad_cases=0
for generation,key,prefix in ((8,0,capability.geometry(7,0)),(7,2,b'x'*40),(True,0,b'x'*40),(7,0,b'x'*40),(7,0,capability.geometry(7,1))):
 try:capability.restore(generation,key,prefix)
 except ValueError:bad_cases+=1
 else:raise AssertionError('Invalid capability accepted')
capability.close()
try:capability.geometry(7,0)
except ValueError:bad_cases+=1
else:raise AssertionError('Retired capability accepted')
assert bad_cases==6
result=dict(result='PASS_GEOMETRY_ONLY_COMPONENT_RESTORATION',capability_rejections=bad_cases,fractions=7,full_input_bytes=sum(map(len,full_frames)),geometry_input_bytes=sum(map(len,frames)),scope='Isolated captured pair preparation/classification; exact fullframe restoration from original parent-owned tails and allsourcearrays/masks/details equal. No wire capability/lifetime or GPU/live qualification, ordinary inputs unchanged.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result)
