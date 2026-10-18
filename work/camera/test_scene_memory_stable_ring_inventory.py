import sys,json,struct
from pathlib import Path
sys.argv=[__file__,'work/camera/prototype-runs/child-scene-1791637661169682300'];ns={};exec(Path('work/camera/test_current_wall_record_scopes.py').read_text().split('from owned_progressive_source_samples_candidate')[0],ns)
def rings(g):
 out={};at=offset=0
 while at<len(g.geometry):
  identifier,n,descriptor,vertices=struct.unpack_from('<4I',g.geometry,at);at+=64;ring=g.geometry[at:at+n*68];at+=n*68
  out[identifier]=(vertices,ring,g.offsets[offset:offset+n*32]);offset+=n*32
 return out
try:
 a,b=(x.graph.graph for x in ns['scenes']);older,newer=rings(a),rings(b);common=older.keys()&newer.keys();stable=[x for x in common if older[x]==newer[x]]
 out=dict(geometry_bytes_equal=a.geometry==b.geometry,offset_bytes_equal=a.offsets==b.offsets,offset_base_equal=struct.unpack_from('<I',a.context,24)[0]==struct.unpack_from('<I',b.context,24)[0],common_descriptors=len(common),stable_vertex_offset_descriptors=len(stable),stable_vertices_bytes=sum(len(older[x][1]) for x in stable),scope='Two actual validated source endpoints; exact addressed vertex rings andoffsetblocks equality. No reuse installed or live benefit inferred.')
finally:ns['history'].close()
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/scene-memory-cpu30-20261010');p.mkdir(exist_ok=True);(p/'stable-rings.json').write_text(json.dumps(out,indent=2));print(out)
