"""Complete byte-only scene transport; native pointers and decoded caches stay local."""
import struct
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene

def pack(frame,scene):
 scene.match(frame);g=scene.graph.graph
 snapshot=struct.pack('<8I',0x3353474e,g.refresh,g.root,0,len(g.geometry),len(g.offsets),1,len(g.faces))+g.context+g.geometry+g.offsets+g.faces
 sections=(snapshot,g.materials,scene.graph.objects,scene.graph.callbacks,scene.graph.associations)
 graph=struct.pack('<8IQ',0x3143474e,1,scene.graph.refresh,*map(len,sections),scene.graph.epoch)+b''.join(sections)
 s=scene.supplements
 supplements=struct.pack('<6IQ',0x3143534e,1,s.refresh,s.source_refresh,len(s.geometry),len(s.textures),s.epoch)+s.geometry+s.textures
 return (bytes(frame),graph,supplements,None if scene.builders is None else scene.builders.payload,None if scene.sources is None else scene.sources.payload)

def unpack(packet,rom):
 if not isinstance(packet,tuple) or len(packet)!=5:raise ValueError('Invalid process scene envelope')
 if any(x is not None and not isinstance(x,bytes) for x in packet):raise ValueError('Process scene must own immutable bytes')
 frame,graph,supplements,builders,sources=packet
 if frame is None or len(frame)>16*1024*1024:raise ValueError('Invalid process frame')
 if sum(len(x) for x in packet if x is not None)>64*1024*1024:raise ValueError('Process scene budget exceeded')
 g=ClosedGraph.decode(graph);s=ClosedSupplements.decode(supplements,g,rom)
 scene=MotionScene(g,s,None if builders is None else OwnedModelBuilders(builders),None if sources is None else OwnedModelSources.decode(sources,g))
 scene.match(frame)
 return frame,scene
