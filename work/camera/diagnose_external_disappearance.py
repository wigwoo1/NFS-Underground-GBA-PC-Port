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


from owned_external_record_candidate import external_record_candidate
from owned_external_model_visit import PreparedExternalModelVisit
from owned_motion_pairs import records
import ctypes as C
visit=PreparedExternalModelVisit(tuple(s.graph for s in scenes),tuple(s.sources for s in scenes),1,rom)
gpu=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));gpu.nf_owned_pose_face_visible_fractional.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_double,C.c_void_p]
results=[]
try:
 for e,scene in enumerate(scenes):
  queue=prepared.pair.portal.sample(e);v=visit.sample(e,queue);blocks=external_record_candidate(scene.graph,scene.sources,1,queue[v['ordinal']],rom)
  m=struct.unpack('<12i',blocks[2]);vertices=list(struct.iter_unpack('<3h',blocks[4]));points=[tuple(m[9+k]+sum(local[j]*m[j*3+k] for j in range(3))/16384 for k in range(3)) for local in vertices]
  indices=struct.unpack('<'+'H'*(len(blocks[6])//2),blocks[6]);offset=0;visible=0;rect=struct.unpack('<4i',blocks[9]);scale=struct.unpack_from('<I',blocks[0],64)[0];cx,cy=struct.unpack_from('<2h',blocks[3],8)
  for count in blocks[5]:
   polygon=[points[index]+(0.,0.) for index in indices[offset:offset+count]];offset+=count;clipped=[]
   for a,b in zip(polygon[-1:]+polygon[:-1],polygon):
    ai=a[2]>=64;bi=b[2]>=64
    if ai!=bi:
     t=(64-a[2])/(b[2]-a[2]);q=tuple(a[k]+t*(b[k]-a[k]) for k in range(5));clipped.append(q[:2]+(64.,)+q[3:])
    if bi:clipped.append(b)
   if len(clipped)<3:continue
   flat=(C.c_double*(len(clipped)*5))(*(x for q in clipped for x in q));bounds=(C.c_double*4)(*rect);value=gpu.nf_owned_pose_face_visible_fractional(flat,len(clipped),scale,cx,cy,bounds);assert value>=0;visible+=value
  results.append(dict(endpoint=e,visible_faces=visible,rect=rect,depth=m[11],x=m[9],vertex_camera_bounds=[[min(p[k] for p in points),max(p[k] for p in points)] for k in range(3)]))
 print(results);Path('work/camera/external-disappearance-visibility.json').write_text(json.dumps(results,indent=2))
finally:prepared.close();history.close()
