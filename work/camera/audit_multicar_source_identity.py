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
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791277545531619000.json').read_text());folder=Path(report['full_scene_failure_capture']['folder']);scenes=[];supp=[];frames=[]
for label in ('older','newer'):
 frame=(folder/(label+'.frame.bin')).read_bytes();frames.append(frame);scene=ClosedGraph(struct.unpack_from('<Q',frame,24)[0],struct.unpack_from('<I',frame,4)[0],GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes()),*( (folder/(label+'.'+field+'.bin')).read_bytes() for field in ('objects','callbacks','associations')));scenes.append(scene);supp.append(ClosedSupplements.decode((folder/(label+'.supplements.bin')).read_bytes(),scene))
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);portal=PortalMotionPair(*(s.graph for s in scenes),table,PreparedMotionPair(*frames));pair=CompleteSupplementalCandidates(*scenes,*supp,portal,rom)

from owned_ordinary_model_visits import ordinary_model_visits
from owned_motion_pairs import records
out=[]
for endpoint,scene in enumerate(scenes):
 visits=ordinary_model_visits(scene,portal.sample(endpoint));models=[(i,x) for i,x in enumerate(records(frames[endpoint])['records']) if x['kind']==3]
 items=[]
 for v in visits:
  source_position=[struct.unpack_from('<i',v['source'],12+k*4)[0]/256 for k in range(3)]
  expected_descriptor=rom[v['dispatch']['descriptor']-0x08000000:v['dispatch']['descriptor']-0x08000000+40]
  matches=[i for i,row in models if bytes(row['blocks'][1])==expected_descriptor]
  items.append(dict(object=v['object'],parent=v['parent'],ordinal=v['ordinal'],distance=v['distance'],position=v['position'],dispatch=v['dispatch'],source_position=source_position,matching_model_records=matches))
 out.append(dict(endpoint=endpoint,refresh=scene.refresh,visits=items,model_records=[i for i,_ in models]))
(folder/'multicar-source-identity.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
print('motion objects',len(portal.motion.arguments[4]),'pairs',portal.motion.arguments[0]['pairs'])
