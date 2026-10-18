"""Probe component UV limits at measured crossing vertices; not a live camera replay."""
import ctypes as C,csv,hashlib,json,math,sys
from pathlib import Path
p=Path(__file__).resolve().parent
class Vertex(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('u',C.c_double),('v',C.c_double)]
class Raw(C.Structure):_fields_=[('count',C.c_uint),('shift',C.c_uint),('height',C.c_uint),('affine',C.c_uint),('material',C.c_uint),('animation',C.c_uint),('offset',C.c_int32*2),('attrs',(C.c_int32*2)*32)]
assert C.sizeof(Raw)==288
dll=C.CDLL(str(p/'road-clip-component.dll'));clip=dll.nf_test_road_clip;clip.argtypes=[C.POINTER(Vertex),C.c_uint,C.POINTER(Raw),C.POINTER(C.c_uint32),C.POINTER(Vertex),C.POINTER(C.c_uint),C.POINTER(C.c_uint)];corner=dll.nf_road_vertex_attributes;corner.argtypes=[C.c_double,C.POINTER(C.c_int32),C.c_uint,C.c_uint,C.c_uint,C.POINTER(C.c_uint32),C.POINTER(C.c_double)]
table=(C.c_uint32*32768).from_buffer_copy((p/'road-correction-reciprocal.bin').read_bytes());manifest=Path(sys.argv[1]);s=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=s['prefix'];gpu_path=Path(prefix+'-dense-near-events-gpu-audit.json');gpu=json.loads(gpu_path.read_text());checks=[]
for event_check in gpu['checks']:
 event=event_check['event']
 if event['identity'][0]!=1:continue
 ep=event_check['endpoints'][0];trace=Path(prefix+f"-dense-{ep['index']:02d}-near-{ep['ordinal']}-isolated.ppm.edges.csv");rows=list(csv.DictReader(trace.read_text().splitlines()));n=len(rows);assert n>=3;raw=Raw();raw.count=n
 for field in ['shift','height','affine']:setattr(raw,field,int(rows[0][field]))
 raw.offset[:]=[int(rows[0]['offset0']),int(rows[0]['offset1'])];vertices=(Vertex*n)()
 for row in rows:
  i=int(row['edge']);vertices[i]=Vertex(float(row['x1']),float(row['y1']),float(row['z1']),0,0);raw.attrs[i][:]=[int(row['a2']),int(row['a3'])]
 for moving in event['near_crossing_vertices']:
  limit=(C.c_double*2)();assert corner(64,raw.attrs[moving],raw.shift,raw.height,raw.affine,table,limit);expected=[limit[0]+raw.offset[0]/(256*(1<<raw.shift)),limit[1]+raw.offset[1]/(256*raw.height)];samples=[]
  for epsilon in [1e-3,1e-5,1e-7]:
   for side in [-1,1]:
    vertices[moving].z=64+side*epsilon;out=(Vertex*64)();count=C.c_uint();adjusted=C.c_uint();assert clip(vertices,n,C.byref(raw),table,out,C.byref(count),C.byref(adjusted))
    # Generated vertices approaching the changed source vertex can be identified
    # geometrically inside this component, without matching screen polygons.
    distances=[math.hypot(v.x-vertices[moving].x,v.y-vertices[moving].y) for v in out[:count.value]];closest=min(distances)
    bound=2*epsilon*max(math.hypot(vertices[j].x-vertices[moving].x,vertices[j].y-vertices[moving].y)/abs(vertices[j].z-64) for j in [(moving-1)%n,(moving+1)%n]);selected=[v for v,d in zip(out[:count.value],distances) if d<=max(bound,1e-10)];assert selected
    errors=[math.hypot(v.u-expected[0],v.v-expected[1]) for v in selected];samples.append(dict(epsilon=epsilon,side=side,position_distance=closest,uv_error=max(errors),approaching_vertices=len(selected),generated_count=count.value,adjusted=adjusted.value))
  checks.append(dict(event=event,moving_vertex=moving,trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),samples=samples))
out=Path(prefix+'-dense-road-topology-limit-probe.json');out.write_text(json.dumps(dict(result='MEASURED',checks=checks,component_sha256=hashlib.sha256((p/'road-clip-component.dll').read_bytes()).hexdigest(),scope='Actual native continuous-road clip component, captured attributes and other-vertex depths; perturb changed vertex depth around64. This isolates UV topology limits and is not interpolated actual camera motion or raster proof.'),indent=2));print(json.dumps(dict(report=str(out),vertices=len(checks),smallest_epsilon_max_uv_error=max(c['samples'][-2]['uv_error'] for c in checks))))
