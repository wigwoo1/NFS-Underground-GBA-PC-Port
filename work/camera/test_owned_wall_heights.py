from pathlib import Path
import struct,json,ctypes as C
from owned_graph_packet import GraphPacket
from owned_scene_bundle import SceneBundle,chunks
from owned_graph_wall_sources import wall_sources,supplemental_wall_sources
from owned_wall_heights import heights
p=Path('work/camera');graphs=descriptors=supplements=edges=0;checks=[]
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((p/'native_visibility.dll').resolve())).nfs_visibility_wall_prepare
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p,C.c_void_p]
for file in sorted((p/'graph-packets').glob('*.ngp')):
 g=GraphPacket.decode(file.read_bytes());at=0;owned={}
 while at<len(g.geometry):
  h=struct.unpack_from('<4I',g.geometry,at);desc=g.geometry[at+16:at+64];at+=64+h[1]*68;owned[h[0]]=desc
  assert struct.unpack_from('<H',desc,10)[0]==65535;descriptors+=1
 sources=list(wall_sources(g));bundlepath=p/'scene-bundles'/ (file.stem+'.nsb')
 if bundlepath.exists():
  bundle=SceneBundle.decode(bundlepath.read_bytes());sources.extend(supplemental_wall_sources(bundle))
  for h,raw in chunks(bundle.supplements,'supplements'):
   desc=raw[32:80];assert struct.unpack_from('<H',desc,10)[0]==65535;owned[h[3]]=desc;supplements+=1
 for w in sources:
  actual=heights(w,owned[w.descriptor],g.context[256:304]);assert len(actual)==4;edges+=1
  state=bytearray(256);struct.pack_into('<I',state,32,0x100000);struct.pack_into('<I',state,72,0x200000);struct.pack_into('<I',state,24,0x300000)
  mi=struct.unpack_from('<H',w.vertices,44)[0];material=bytearray(w.resolved);struct.pack_into('<H',material,0,0)
  table={0x100000+mi*32:bytes(material),0x200000:w.animation}
  for j in range(2):
   index=struct.unpack_from('<H',w.vertices,j*68+42)[0]
   if index!=65535:table[0x300000+index*32]=w.offsets[j*32:(j+1)*32]
  @Reader
  def read(ctx,address,out,n):
   data=table.get(address)
   if data is None or len(data)!=n:return 0
   C.memmove(out,data,n);return 1
  base=struct.unpack_from('<I',g.context,296)[0];bases=(C.c_uint32*2)(base,base);output=(C.c_uint32*4)();scratch=C.create_string_buffer(52)
  assert fn(bytes(state),w.vertices[:68],w.vertices[68:],bases,read,None,output,scratch)
  assert tuple(output)==actual
  changed=bytearray(owned[w.descriptor]);struct.pack_into('<H',changed,10,0)
  try:heights(w,changed,g.context[256:304])
  except ValueError:pass
  else:raise AssertionError('Missing descriptor height ownership accepted')
 graphs+=1;checks.append(dict(refresh=g.refresh,wall_height_edges=len(sources)))
r=dict(result='PASS_OWNED_WALL_HEIGHT_DEPENDENCY_AUDIT',graphs=graphs,descriptors=descriptors,supplemental_descriptors=supplements,edges=edges,checks=checks,scope='All retained descriptors use sentinel height table index; no state28 lookup needed in this corpus. Owned height derivation implemented; non-sentinel without explicit owned offset rejects. All heights match existing ARM-verified native wall preparation helper; complete original scratch/dispatch parity still required.')
(p/'owned-wall-heights.json').write_text(json.dumps(r,indent=2));print(r)

