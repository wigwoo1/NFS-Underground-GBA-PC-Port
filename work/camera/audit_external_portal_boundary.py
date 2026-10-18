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
folder=Path('G:\\EXTRA DATA DRIVE\\Desktop\\Games\\Codex\\NFSUG-Native-PC-Port\\work\\camera\\prototype-runs\\fullscene-failure-1791308040881565000')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);frames=[];scenes=[]
for name in ('older','newer'):
 raw_supp=(folder/(name+'.supplements.bin')).read_bytes();refresh=struct.unpack_from('<I',raw_supp,8)[0];epoch=struct.unpack_from('<Q',raw_supp,24)[0]
 graph=ClosedGraph(epoch,refresh,GraphPacket.decode((folder/(name+'.graph.bin')).read_bytes()),*((folder/(name+'.'+section+'.bin')).read_bytes() for section in ('objects','callbacks','associations')))
 scenes.append(MotionScene(graph,ClosedSupplements.decode((folder/(name+'.supplements.bin')).read_bytes(),graph,rom),OwnedModelBuilders((folder/(name+'.builders.bin')).read_bytes()),OwnedModelSources.decode((folder/(name+'.current-sources.bin')).read_bytes(),graph)))
 frames.append((folder/(name+'.frame.bin')).read_bytes())

from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
from owned_external_model_owners import external_model_owners
from owned_external_model_visit import PreparedExternalModelVisit
portal=PortalMotionPair(*(s.graph.graph for s in scenes),table,PreparedMotionPair(*frames,*scenes))
queues=tuple(portal.sample(i) for i in (0,1))
maps=[external_model_owners(s.graph,s.builders,frame,rom) for s,frame in zip(scenes,frames)]
checks=[]
for owner in sorted(set(maps[0].values())|set(maps[1].values())):
 visit=PreparedExternalModelVisit(tuple(s.graph for s in scenes),tuple(s.sources for s in scenes),owner,rom)
 checks.append(dict(owner=owner,emitted=[owner in m.values() for m in maps],parents=[x[0][0] for x in visit.visits],depths=[visit.motion.matrix(i)[11] for i in (0,1)],samples=[visit.sample(i,queues[i]) for i in (0,1)],parent_regions=[[q for q in queue if q[0]==v[0][0]] for queue,v in zip(queues,visit.visits)]))
result=dict(result='EXTERNAL_PORTAL_BOUNDARY_AUDIT',refreshes=[s.graph.refresh for s in scenes],owner_maps=[dict(m) for m in maps],checks=checks)
Path('work/camera/external-portal-boundary-audit.json').write_text(json.dumps(result,indent=2,default=lambda x:x.hex() if isinstance(x,bytes) else dict(x)));print([{k:v for k,v in row.items() if k!='samples'} for row in checks])
