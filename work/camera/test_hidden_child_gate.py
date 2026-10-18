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
history=EndpointRoadPlanner(rom,table)
try:
 history.plan(scenes[0]);sequence=SampledRoadSequence(*scenes,portal,history);assert 230 in sequence.hidden_children
 faces=bytearray(scenes[1].graph.faces)
 for at in range(16,len(faces),24):
  if struct.unpack_from('<I',faces,at)[0]==33569736:faces[at+12]^=0x40
 changed=replace(scenes[1],graph=replace(scenes[1].graph,faces=bytes(faces)))
 try:SampledRoadSequence(scenes[0],changed,portal,history)
 except ValueError as error:assert str(error)=='Moving road source topology unsupported'
 else:raise AssertionError('Changed child visibility accepted')
 print('PASS hidden child230 gate requires identical owned face bytes at both endpoints; changed flag rejects exemption')
finally:history.close()

