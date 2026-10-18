import struct,json,sys
from pathlib import Path
from owned_graph_packet import GraphPacket
from owned_closed_graph import ClosedGraph
from owned_motion_visibility import PortalMotionPair
from sample_owned_motion import PreparedMotionPair
from owned_ordinary_model_visits import ordinary_model_visits
from owned_spatial_descriptors import SpatialDescriptors
folder=Path(sys.argv[1] if len(sys.argv)>1 else 'work/camera/prototype-runs/fullscene-failure-1791282927836604600');scenes=[];frames=[]
for label in ('older','newer'):
 frame=(folder/(label+'.frame.bin')).read_bytes();frames.append(frame)
 scenes.append(ClosedGraph(struct.unpack_from('<Q',frame,24)[0],struct.unpack_from('<I',frame,4)[0],GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes()),*((folder/(label+'.'+f+'.bin')).read_bytes() for f in ('objects','callbacks','associations'))))
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);portal=PortalMotionPair(*(s.graph for s in scenes),table,PreparedMotionPair(*frames));spatial=SpatialDescriptors(scenes[0].graph)
for i,scene in enumerate(scenes):
 for visit in ordinary_model_visits(scene,portal.sample(i),True):
  point=tuple(struct.unpack_from('<i',visit['source'],12+j*4)[0]>>8 for j in (0,2));parent=visit['parent'];selected=spatial.select(parent,point);fallback=spatial.fallback(parent,point) if selected==65535 else None
  print(dict(endpoint=i,object=visit['object'],model=visit['dispatch']['model'],parent=parent,point=point,selected=selected,fallback=fallback,flags=struct.unpack_from('<H',visit['source'],10)[0],neighbors=list(spatial.neighbors(parent)),chain_regions=[h[3] for h,raw in __import__('owned_scene_bundle').chunks(scene.objects,'graph_objects') if any(struct.unpack_from('<I',raw,128+k*168)[0]==visit['object'] for k in range(h[5]))]))

