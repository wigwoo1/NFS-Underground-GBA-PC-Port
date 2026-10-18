"""Single-allocation immutable scene packing; original wire and checks unchanged."""
import inspect,textwrap
from owned_scene_process_transport import pack as original
source=textwrap.dedent(inspect.getsource(original))
changes={
"struct.pack('<8I',0x3353474e,g.refresh,g.root,0,len(g.geometry),len(g.offsets),1,len(g.faces))+g.context+g.geometry+g.offsets+g.faces":"b''.join((struct.pack('<8I',0x3353474e,g.refresh,g.root,0,len(g.geometry),len(g.offsets),1,len(g.faces)),g.context,g.geometry,g.offsets,g.faces))",
"struct.pack('<8IQ',0x3143474e,1,scene.graph.refresh,*map(len,sections),scene.graph.epoch)+b''.join(sections)":"b''.join((struct.pack('<8IQ',0x3143474e,1,scene.graph.refresh,*map(len,sections),scene.graph.epoch),*sections))",
"struct.pack('<6IQ',0x3143534e,1,s.refresh,s.source_refresh,len(s.geometry),len(s.textures),s.epoch)+s.geometry+s.textures":"b''.join((struct.pack('<6IQ',0x3143534e,1,s.refresh,s.source_refresh,len(s.geometry),len(s.textures),s.epoch),s.geometry,s.textures))"}
for old,new in changes.items():assert source.count(old)==1;source=source.replace(old,new)
namespace=dict(original.__globals__);exec(compile(source,'single-allocation-scene-pack','exec'),namespace);pack=namespace['pack']
