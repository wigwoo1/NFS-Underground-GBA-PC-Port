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
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();out=[]
for scene,supplement in zip(scenes,supp):
 material_ids={struct.unpack_from('<12I',raw)[5] for _,raw in chunks(supplement.textures,'textures')};missing=[]
 for asset in recover_geometry(scene,rom).values():
  for edge,mi in enumerate(asset.material_indices):
   if mi!=65535 and mi not in material_ids:missing.append(dict(descriptor=asset.descriptor,edge=edge,material=mi))
 out.append(dict(refresh=scene.refresh,captured_materials=sorted(material_ids),missing=missing))
(folder/'supplemental-material-closure-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
