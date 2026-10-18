"""Exact continuous-camera pair timeline and actual captured full road rings."""
from pathlib import Path
import ctypes as C,csv,json,math
p=Path('work/camera');sources=list(csv.DictReader((p/'road-attribute-motion-sources.csv').open()));edges=list(csv.DictReader((p/'road-attribute-motion-edges.csv').open()))
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quaternion(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quaternion)]
class Vertex(C.Structure):_fields_=[('p',Point),('u',C.c_double),('v',C.c_double)]
class Raw(C.Structure):_fields_=[('count',C.c_uint32),('shift',C.c_uint32),('height',C.c_uint32),('affine',C.c_uint32),('material',C.c_uint32),('animation',C.c_uint32),('offsets',C.c_int32*2),('attributes',(C.c_int32*2)*32)]
poses={(int(r['index']),int(r['role'])):Pose(Point(*[float(r[k]) for k in 'xyz']),Quaternion(*[float(r['q'+k]) for k in 'xyzw'])) for r in csv.DictReader((p/'road-attribute-motion-cameras.csv').open())}
motion=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));sample=motion.nf_rigid_scene_sample;sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
probe=C.CDLL(str((p/'road-corrected-clip-probe.dll').resolve()));clip=probe.nf_corrected_clip_probe;clip.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];geometric=probe.nf_geometric_clip_probe;geometric.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
recip=(C.c_uint32*32768).from_buffer_copy((p/'road-correction-reciprocal.bin').read_bytes());fixed=Pose(Point(0,0,0),Quaternion(0,0,0,1))
segments={}
for i,row in enumerate(sources):
 key=(int(row['older_refresh']),int(row['newer_refresh']))
 if key in segments:assert bytes(segments[key][0])==bytes(poses[i,0]) and bytes(segments[key][1])==bytes(poses[i,1])
 else:segments[key]=(poses[i,0],poses[i,1])
def transform(world,target,forced=None):
 key=forced or next(k for k in sorted(segments) if k[0]<=target<=k[1])
 a,b=segments[key];alpha=(target-key[0])/(key[1]-key[0]);out=(Point*len(world))()
 assert sample(C.byref(a),C.byref(b),C.byref(fixed),C.byref(fixed),alpha,world,len(world),out);return out
maximum=0
for row in edges:
 world=(Point*2)(*[Point(*[float(row[f'world{j}'+k]) for k in 'xyz']) for j in (0,1)])
 out=transform(world,float(sources[int(row['index'])]['target']))
 for j in (0,1):maximum=max(maximum,max(abs(getattr(out[j],k)-float(row[f'camera{j}'+k])) for k in 'xyz'))
assert maximum<1e-9
# Reconstruct complete ordered source rings, checking shared endpoint/attribute consistency.
rings={}
for row in edges:
 if int(row['index'])==9:rings.setdefault(int(row['identity']),[]).append(row)
assert len(rings)==3
start,end=[float(sources[i]['target']) for i in (9,10)];runs=0;counts={};knots=0;max_knot=0
for identity,records in rings.items():
 records.sort(key=lambda r:int(r['edge']));count=int(records[0]['count']);assert len(records)==count
 raw=Raw();raw.count=count;raw.shift=int(records[0]['shift']);raw.height=int(records[0]['height']);raw.affine=int(records[0]['affine']);raw.offsets[:]=[int(records[0][k]) for k in ('offset0','offset1')]
 world=(Point*count)(*[Point(*[float(r['world1'+k]) for k in 'xyz']) for r in records])
 for i,row in enumerate(records):
  assert int(row['edge'])==i
  assert all(float(row['world0'+k])==getattr(world[(i+count-1)%count],k) for k in 'xyz')
  raw.attributes[i][:]=[int(row[k]) for k in ('b0','b1')]
  assert [int(row[k]) for k in ('a0','a1')]==[int(records[(i+count-1)%count][k]) for k in ('b0','b1')]
 observed=set()
 for step in range(513):
  camera=transform(world,start+(end-start)*step/512);incoming=(Vertex*count)(*[Vertex(point,0,0) for point in camera]);out=(Vertex*64)();baseline=(Vertex*64)();n=C.c_uint()
  assert clip(incoming,count,out,C.byref(raw),recip,C.byref(n));assert n.value==geometric(incoming,count,baseline)
  for i in range(n.value):assert bytes(out[i].p)==bytes(baseline[i].p) and all(math.isfinite(v) for v in (out[i].u,out[i].v))
  observed.add(n.value);runs+=1
 counts[str(identity)]=sorted(observed)
 # At each source knot, both incident camera pairs must produce same geometry.
 for left in segments:
  for right in segments:
   if left[1]!=right[0] or not start<=left[1]<=end:continue
   a,b=transform(world,left[1],left),transform(world,right[0],right)
   error=max(abs(getattr(x,k)-getattr(y,k)) for x,y in zip(a,b) for k in 'xyz');max_knot=max(max_knot,error);assert error<1e-9;knots+=1
assert knots==3 and any(len(v)>1 for v in counts.values())
report=dict(result='PASS',live_edge_reconstructions=len(edges),maximum_live_camera_error=maximum,source_pair_segments=len(segments),full_ring_samples=runs,output_vertex_counts=counts,source_knot_ring_checks=knots,maximum_knot_geometry_difference=max_knot,scope='Exact opt-in continuous source-camera timeline, including original pair knot; actual retained full road geometry through actual corrected clipping helper. Geometric output byte-exact against geometric clipper and finite UVs. Material/animation held at captured frame9; no GPU coverage/texture pixels, quantized visibility alignment or fullscene timing proof.')
(p/'live-road-exact-timeline-tests.json').write_text(json.dumps(report,indent=2));print(report)
