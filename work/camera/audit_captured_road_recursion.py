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
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791275919432481000.json').read_text());folder=Path(report['full_scene_failure_capture']['folder']);scenes=[];supp=[];frames=[]
for label in ('older','newer'):
 frame=(folder/(label+'.frame.bin')).read_bytes();frames.append(frame);scene=ClosedGraph(struct.unpack_from('<Q',frame,24)[0],struct.unpack_from('<I',frame,4)[0],GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes()),*( (folder/(label+'.'+field+'.bin')).read_bytes() for field in ('objects','callbacks','associations')));scenes.append(scene);supp.append(ClosedSupplements.decode((folder/(label+'.supplements.bin')).read_bytes(),scene))
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);portal=PortalMotionPair(*(s.graph for s in scenes),table,PreparedMotionPair(*frames));pair=CompleteSupplementalCandidates(*scenes,*supp,portal,rom)

from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
checks=[]
for endpoint,scene in enumerate(scenes):
 sources=road_candidates(scene,ClosedSceneMemory(scene,rom));active={q[0] for q in portal.sample(endpoint) if not q[5]&8}
 for x in sources:
  if x.descriptor not in active:continue
  child=struct.unpack_from('<H',x.descriptor_bytes,6)[0];replace=bool(x.descriptor_bytes[18]&8)
  if x.secondary or replace or child!=65535:
   checks.append(dict(endpoint=endpoint,refresh=scene.refresh,descriptor=x.descriptor,secondary=x.secondary,child=child,replaces_self=replace,sibling=struct.unpack_from('<H',x.descriptor_bytes,24)[0],missing=list(x.missing)))
assert checks
out=dict(result='CAPTURED_ROAD_RECURSION_AUDIT',checks=checks,scope='Source flags and active endpoint ownership only; recursive dispatch not implemented.')
(folder/'road-recursion-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
