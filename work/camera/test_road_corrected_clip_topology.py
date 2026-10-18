"""Exercise the actual corrected ring helper through near-plane topology changes."""
from pathlib import Path
import ctypes as C,json,math,random
p=Path('work/camera')
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Vertex(C.Structure):_fields_=[('p',Point),('u',C.c_double),('v',C.c_double)]
class Raw(C.Structure):
 _fields_=[('count',C.c_uint32),('shift',C.c_uint32),('stored_height',C.c_uint32),('affine',C.c_uint32),('material',C.c_uint32),('animation',C.c_uint32),('offsets',C.c_int32*2),('attributes',(C.c_int32*2)*32)]
lib=C.CDLL(str((p/'road-corrected-clip-probe.dll').resolve()))
clip=lib.nf_corrected_clip_probe;clip.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
geometric=lib.nf_geometric_clip_probe;geometric.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
vertex=lib.nf_road_vertex_attributes;vertex.argtypes=[C.c_double,C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
recip=(C.c_uint32*32768).from_buffer_copy((p/'road-correction-reciprocal.bin').read_bytes())
rng=random.Random(100364);rings=boundary=0;counts=set();maximum=0
def run(depths,raw):
 points=[(-30,-20),(30,-20),(30,20),(-30,20)]
 incoming=(Vertex*4)(*[Vertex(Point(x,y,z),0,0) for (x,y),z in zip(points,depths)])
 out=(Vertex*64)();base=(Vertex*64)();count=C.c_uint(999)
 assert clip(incoming,4,out,C.byref(raw),recip,C.byref(count))
 n=geometric(incoming,4,base);assert count.value==n
 for i in range(n):
  assert bytes(out[i].p)==bytes(base[i].p)
  assert all(math.isfinite(v) for v in (out[i].u,out[i].v))
 return out,n
for affine in (0,1):
 for trial in range(200):
  raw=Raw();raw.count=4;raw.shift=rng.randrange(1,11);raw.stored_height=2*rng.randrange(1,513);raw.affine=affine
  raw.offsets[:]=[rng.randrange(-100,101),rng.randrange(-100,101)]
  for attrs in raw.attributes[:4]:attrs[:]=[rng.randrange(-16384,32768),rng.randrange(-16384,32768)]
  # One moving corner crosses the plane; both neighboring vertices remain front.
  for z in (40,63,63.9999999,64,64.0000001,65,100):
   out,n=run([z,100,150,90],raw);rings+=1;counts.add(n)
   if z==63.9999999:
    uv=(C.c_double*2)();assert vertex(64,raw.attributes[0],raw.shift,raw.stored_height,affine,recip,uv)
    expected=[uv[0]+raw.offsets[0]/(256*(1<<raw.shift)),uv[1]+raw.offsets[1]/(256*raw.stored_height)]
    # Ordered loop emits incoming intersection first, outgoing second.
    error=max(abs(getattr(out[i],key)-expected[k]) for i in (0,1) for k,key in enumerate(('u','v')))
    maximum=max(maximum,error);assert error<1e-6;boundary+=2
  # Empty, on-plane, two-crossing and four-crossing source rings.
  for depths in ([40]*4,[64]*4,[40,40,100,100],[40,100,40,100]):
   out,n=run(depths,raw);rings+=1;counts.add(n)
raw=Raw();raw.count=4;raw.shift=6;raw.stored_height=128
incoming=(Vertex*4)(*[Vertex(Point(i,i,100),0,0) for i in range(4)])
rejections=0
for count,mutation in [(2,None),(33,None),(4,'count'),(4,'height'),(4,'shift'),(4,'affine'),(4,'nan')]:
 candidate=Raw.from_buffer_copy(raw);src=(Vertex*4).from_buffer_copy(incoming)
 if mutation=='count':candidate.count=3
 if mutation=='height':candidate.stored_height=3
 if mutation=='shift':candidate.shift=11
 if mutation=='affine':candidate.affine=2
 if mutation=='nan':src[0].p.z=float('nan')
 out=(Vertex*64)();C.memset(out,0x5a,C.sizeof(out));before=bytes(out);n=C.c_uint(777)
 assert not clip(src,count,out,C.byref(candidate),recip,C.byref(n))
 assert bytes(out)==before and n.value==777;rejections+=1
report=dict(result='PASS',rings=rings,output_vertex_counts=sorted(counts),ordered_edge_boundary_checks=boundary,maximum_normalized_boundary_error=maximum,atomic_rejections=rejections,scope='Actual renderer corrected-ring helper: geometric positions byte-exact with original geometric clip helper, finite UVs, one-corner topology limits and empty/on-plane/multiple-crossing rings. Synthetic source data; no GPU raster/fullscene motion/degenerate simultaneous-edge UV continuity proof.')
(p/'road-corrected-clip-topology-tests.json').write_text(json.dumps(report,indent=2));print(report)
