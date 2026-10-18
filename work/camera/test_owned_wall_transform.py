from pathlib import Path
import ctypes as C,struct,json
from owned_graph_packet import GraphPacket
from owned_wall_transform import transform
p=Path('work/camera');Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((p/'native_visibility.dll').resolve())).nfs_visibility_region_transform
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_uint,Reader,C.c_void_p,C.c_void_p,C.c_size_t];checks=[];accepted=far=0
for file in sorted((p/'graph-packets').glob('*.ngp')):
 g=GraphPacket.decode(file.read_bytes());at=offset=0;count=0
 while at<len(g.geometry):
  h=struct.unpack_from('<4I',g.geometry,at);n=h[1];at+=64;ring=g.geometry[at:at+n*68];at+=n*68;offsets=g.offsets[offset:offset+n*32];offset+=n*32;camera=g.context[256:304]
  result,scratch=transform(ring,offsets,camera);state=bytearray(256);struct.pack_into('<I',state,84,0x100000);struct.pack_into('<I',state,24,0x200000);owned={0x100000:camera}
  for i in range(n):
   index=struct.unpack_from('<H',ring,i*68+42)[0]
   if index!=65535:owned[0x200000+index*32]=offsets[i*32:(i+1)*32]
  @Reader
  def read(ctx,address,out,size):
   data=owned.get(address)
   if data is None or len(data)!=size:return 0
   C.memmove(out,data,size);return 1
  out=C.create_string_buffer(n*52);status=fn(bytes(state),ring,len(ring),n,read,None,out,n*52);assert status==result and out.raw==scratch,(g.refresh,h[0],status,result,[(i,a,b) for i,(a,b) in enumerate(zip(out.raw,scratch)) if a!=b][:12])
  count+=1;accepted+=result;far+=not result
 checks.append(dict(refresh=g.refresh,regions_exact=count))
r=dict(result='PASS_OWNED_RAW_WALL_TRANSFORM',accepted=accepted,far=far,checks=checks,scope='Complete ring scratch transform matches existing ARM-verified native helper using owned camera/offsets only. Wall prepare/clip/project integration and executed draw parity pending.')
(p/'owned-wall-transform.json').write_text(json.dumps(r,indent=2));print(r)

