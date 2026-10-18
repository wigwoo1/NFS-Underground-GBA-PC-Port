"""Fewer temporary header values; existing successful material-cache behavior."""
from owned_road_material_decode_reuse_candidate import source,ns
source=source.replace("h=struct.unpack_from('<12I',g.materials,at)","material_index,payload_bytes,payload_kind,shared_key=struct.unpack_from('<12xI16x3I4x',g.materials,at)")
for old,new in [('h[3]','material_index'),('h[8]','payload_bytes'),('h[9]','payload_kind'),('h[10]','shared_key')]:source=source.replace(old,new)
source=source.replace('  for secondary,field in ((0,8),(1,4)):',"  first_material=struct.unpack_from('<H',desc,8)[0];second_material=struct.unpack_from('<H',desc,4)[0];face_index=None\n  for secondary,mi in ((0,first_material),(1,second_material)):")
source=source.replace("   mi=struct.unpack_from('<H',desc,field)[0]\n",'')
source=source.replace("missing=[];fi=struct.unpack_from('<H',desc,10)[0];address=0 if fi==65535 else face_base+fi*20", "missing=[]\n   if face_index is None:face_index=struct.unpack_from('<H',desc,10)[0]\n   address=0 if face_index==65535 else face_base+face_index*20")
namespace=dict(ns);exec(compile(source,'road-header-decode-candidate','exec'),namespace)
road_candidates=namespace['road_candidates']
