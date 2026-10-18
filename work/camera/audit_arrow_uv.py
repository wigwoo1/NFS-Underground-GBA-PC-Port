"""Compare original integer-column texture sampling to retained world UVs.
This is an offline diagnostic, never a motion correspondence algorithm.
"""
from pathlib import Path
import struct,json,math,csv,ctypes as C
from scene_batches import batches
root=Path('work/camera');p=(root/'reference-scene-0.packet').read_bytes()
sections={t:p[o:o+n] for t,o,n in (struct.unpack_from('<3I',p,32+i*12) for i in range(5))}
m=sections[1];projection=struct.unpack_from('<3d',m,24);pose=struct.unpack_from('<7d',m,48)
def camera(v):
 x,y,z=[v[i]-pose[i] for i in range(3)];qx,qy,qz,qw=pose[3:]
 tx,ty,tz=2*(qy*z-qz*y),2*(qz*x-qx*z),2*(qx*y-qy*x)
 return x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx
w=sections[2];off=8
for index in range(struct.unpack_from('<I',w,4)[0]):
 n,width,height=struct.unpack_from('<3I',w,off);identity=struct.unpack_from('<5I',sections[5],8+index*20)
 if identity[0]==2 and identity[2]==0x0857c6f4:
  verts=[camera(struct.unpack_from('<3d',w,off+12+j*24)) for j in range(n)]
  uv=struct.unpack_from('<8d',w,off+12+n*24);break
 off+=12+n*40+width*height*4
else:raise AssertionError('Arrow wall absent')
native=C.CDLL(str((root/'native_wall.dll').resolve()));fn=native.nfs_wall_unshaded_addresses
fn.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint,C.c_void_p,C.c_void_p]
rows=[];active=0;outside=0
for e in next(batches(root/'shading-spans.bin'))['events']:
 if e['pc']==0x03000304:active=e['blocks'][5][0]
 if active!=0x0857c6f4 or e['pc']!=0x030053e8:continue
 state=e['blocks'][75][1];count=e['regs'][3];src=(C.c_uint32*320)();dst=(C.c_uint32*320)()
 assert fn(C.create_string_buffer(state),e['regs'][1],e['regs'][2],count,src,dst)
 texture=struct.unpack_from('<I',state,36)[0]
 for j in range(count):
  x=(dst[j]-0x06000000)%240;y=(dst[j]-0x06000000)//240
  ray=(x-projection[0])/projection[2];x0,_,z0=verts[0];x1,_,z1=verts[1]
  t=(ray*z0-x0)/((x1-x0)-ray*(z1-z0))
  depth=z0+t*(z1-z0);top_y=verts[0][1]+t*(verts[1][1]-verts[0][1]);bottom_y=verts[3][1]+t*(verts[2][1]-verts[3][1])
  world_y=(y-projection[1])*depth/projection[2];vertical=(world_y-top_y)/(bottom_y-top_y)
  inside=0<=t<=1 and 0<=vertical<=1
  if not inside:outside+=1
  u=(uv[0]+t*(uv[2]-uv[0]))*width
  v=(uv[1]+vertical*(uv[7]-uv[1]))*height
  original_offset=src[j]-texture;ou=original_offset%width;ov=original_offset//width
  # Quantization-only comparison: same nearest/even rule as original address oracle.
  nu=(math.floor(u)%width)&~1;nv=math.floor(v)%height
  rows.append(dict(x=x,y=y,inside_world_wall=inside,original_u=ou,original_v=ov,native_even_u=nu,native_v=nv,native_u_float=u,native_v_float=v))
inside=[r for r in rows if r['inside_world_wall']]
report=dict(rows=len(rows),inside=len(inside),outside=outside,
 exact_texel_matches_inside=sum((r['original_u'],r['original_v'])==(r['native_even_u'],r['native_v']) for r in inside),
 mean_wrapped_u_error_inside=sum(min(abs(r['original_u']-r['native_even_u']),width-abs(r['original_u']-r['native_even_u'])) for r in inside)/len(inside),
 mean_wrapped_v_error_inside=sum(min(abs(r['original_v']-r['native_v']),height-abs(r['original_v']-r['native_v'])) for r in inside)/len(inside),
 scope='Original integer sample coordinates vs continuous world UVs sampled at those integer coordinates, with even-column quantization applied only for comparison. Not 4K GPU pixel-center equivalence.')
with (root/'arrow-uv-audit.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(root/'arrow-uv-audit.json').write_text(json.dumps(report,indent=2));print(report)
