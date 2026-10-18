"""Compare model draw owners with complete source state at a failure boundary."""
import struct,sys,json
from pathlib import Path
from owned_graph_packet import GraphPacket
from owned_closed_graph import ClosedGraph
from owned_model_sources import OwnedModelSources
from owned_ordinary_model_visits import ordinary_model_visits
from owned_motion_visibility import PortalMotionPair
from sample_owned_motion import PreparedMotionPair
from owned_object_filter import depth_distance,eligibility
folder=Path(sys.argv[1]);scenes=[];frames=[];sources=[]
for label in ('older','newer'):
 frame=(folder/(label+'.frame.bin')).read_bytes();frames.append(frame);graph=ClosedGraph(struct.unpack_from('<Q',frame,24)[0],struct.unpack_from('<I',frame,4)[0],GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes()),*((folder/(label+'.'+k+'.bin')).read_bytes() for k in ('objects','callbacks','associations')));scenes.append(graph);sources.append(OwnedModelSources.decode((folder/(label+'.current-sources.bin')).read_bytes(),graph))
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);portal=PortalMotionPair(*(s.graph for s in scenes),table,PreparedMotionPair(*frames));visits=[{v['object']:v for v in ordinary_model_visits(s,portal.sample(i),True)} for i,s in enumerate(scenes)];changed=set(visits[0])^set(visits[1]);print('changed',changed)
for index in sorted(changed):
 for i,(scene,packet) in enumerate(zip(scenes,sources)):
  base=struct.unpack_from('<I',scene.graph.context,60)[0];address=base+index*164;raw=packet.sources.get(address)
  print(dict(index=index,endpoint=i,source_refresh=packet.source_refresh,visit=bool(index in visits[i]),slot=raw[136] if raw else None,removal=packet.removals.get(address),eligibility=eligibility(raw) if raw else None,depth=depth_distance(raw,scene.graph.context[256:304])[0] if raw else None,model=struct.unpack_from('<h',raw,54)[0] if raw else None))
