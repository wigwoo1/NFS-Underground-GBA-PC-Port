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
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791276427842950100.json').read_text());folder=Path(report['full_scene_failure_capture']['folder']);scenes=[];supp=[];frames=[]
for label in ('older','newer'):
 frame=(folder/(label+'.frame.bin')).read_bytes();frames.append(frame);scene=ClosedGraph(struct.unpack_from('<Q',frame,24)[0],struct.unpack_from('<I',frame,4)[0],GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes()),*( (folder/(label+'.'+field+'.bin')).read_bytes() for field in ('objects','callbacks','associations')));scenes.append(scene);supp.append(ClosedSupplements.decode((folder/(label+'.supplements.bin')).read_bytes(),scene))

from owned_supplemental_rom_geometry import recover_geometry
from owned_scene_bundle import chunks
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();
for label,scene in zip(('older','newer'),scenes):
 raw=(folder/(label+'.supplements.bin')).read_bytes();ClosedSupplements.decode(raw,scene,rom)
 h=struct.unpack_from('<6I',raw);start=32+h[4]
 if not h[5]:continue
 for field,value in ((2,0),(3,65534),(4,32),(5,65534)):
  bad=bytearray(raw);struct.pack_into('<I',bad,start+field*4,value)
  try:ClosedSupplements.decode(bad,scene,rom)
  except ValueError:pass
  else:raise AssertionError('Malformed material ownership accepted')
print('PASS ROM edge/material and owned state validation; four corrupted identities rejected')
