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
from owned_geometry_process_codec_candidate import GeometryFrameDecoder,pack_geometry
from owned_progressive_frame_codec_candidate import FrameEncoder
from owned_segmented_frame_candidate import SegmentedFrame
from owned_scene_process_transport import unpack
capability=GeometryTailOwners(7,full_frames)
for reduced in (False,True):
 frames=[]
 for key,frame in enumerate(full_frames):
  frames.append(unpack(pack_geometry(frame,scenes[key]),rom)[0] if reduced else frame)
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
 prepared=samples=None
 try:
  prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
  samples=ProgressiveSourceWorldSamples(prepared,(.125,.25,.375,.5,.625,.75,.875))
  values=[]
  decoder=GeometryFrameDecoder(7,full_frames) if reduced else None
  encoder=FrameEncoder(7,owners=tuple(frames)) if reduced else None
  for alpha in samples.samples:
   frame,camera,models,bounds,detail=samples.sample(alpha);packed=samples.source_masks[alpha]
   if reduced:
    header=struct.unpack_from('<6I2Q',frames[0]);segmented=SegmentedFrame(frame,frames[0],40+header[2])
    frame=bytes(decoder.decode(encoder.encode(segmented)))
   values.append((frame,bytes(camera),bytes(models),bytes(bounds),detail,bytes(packed[0]),bytes(packed[1]),packed[2:]))
  if reference is None:reference=values
  else:assert values==reference
 finally:
  if reduced and decoder:decoder.close()
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
decoder=GeometryFrameDecoder(7,full_frames)
geo=GeometryTailOwners(7,full_frames)
wire=('segmented',7,0,geo.geometry(7,0),40+struct.unpack_from('<I',full_frames[0],8)[0],None)
restored=decoder.decode(wire)
assert bytes(restored)==full_frames[0]
malformed=[list(wire),wire[:-1],('raw',)+wire[1:]]
for position,value in ((1,8),(1,True),(2,2),(2,True),(3,b'x'*40),(3,bytearray(wire[3])),(4,wire[4]+1),(4,True),(5,full_frames[0])):
 fields=list(wire);fields[position]=value;malformed.append(tuple(fields))
wire_rejections=0
for bad in malformed:
 try:decoder.decode(bad)
 except ValueError:wire_rejections+=1
 else:raise AssertionError('Malformed wire accepted')
decoder.close();geo.close()
try:decoder.decode(wire)
except ValueError:wire_rejections+=1
else:raise AssertionError('Retired wire accepted')
assert bytes(restored)==full_frames[0], 'Restored owner lost after retirement'
assert wire_rejections==13
result=dict(result='PASS_GEOMETRY_PROCESS_CODEC_COMPONENT',capability_rejections=bad_cases,wire_rejections=wire_rejections,retained_after_close=True,fractions=7,full_input_bytes=sum(map(len,full_frames)),geometry_input_bytes=sum(map(len,frames)),scope='Isolated captured pair preparation/classification; exact fullframe restoration from original parent-owned tails and allsourcearrays/masks/details equal. Local seeded wire rejection and retained-owner lifetime verified; no spawned process or GPU/live qualification, ordinary inputs unchanged.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result)
