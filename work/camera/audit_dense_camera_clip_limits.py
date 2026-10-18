"""Actual camera-root samples through unchanged native road/wall clip components."""
import ctypes as C,csv,hashlib,json,math,struct,sys
from pathlib import Path
p=Path(__file__).resolve().parent
class Vertex(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('u',C.c_double),('v',C.c_double)]
class Raw(C.Structure):_fields_=[('count',C.c_uint),('shift',C.c_uint),('height',C.c_uint),('affine',C.c_uint),('material',C.c_uint),('animation',C.c_uint),('offset',C.c_int32*2),('attrs',(C.c_int32*2)*32)]
dll=C.CDLL(str(p/'road-clip-component.dll'));clip=dll.nf_test_road_clip;clip.argtypes=[C.POINTER(Vertex),C.c_uint,C.POINTER(Raw),C.POINTER(C.c_uint32),C.POINTER(Vertex),C.POINTER(C.c_uint),C.POINTER(C.c_uint)];corner=dll.nf_road_vertex_attributes;corner.argtypes=[C.c_double,C.POINTER(C.c_int32),C.c_uint,C.c_uint,C.c_uint,C.POINTER(C.c_uint32),C.POINTER(C.c_double)];generic=dll.nf_test_generic_clip;generic.argtypes=[C.POINTER(Vertex),C.c_uint,C.POINTER(Vertex)]
table=(C.c_uint32*32768).from_buffer_copy((p/'road-correction-reciprocal.bin').read_bytes());manifest=Path(sys.argv[1]);session=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=session['prefix'];root_path=Path(prefix+'-dense-camera-near-roots.json');roots=json.loads(root_path.read_text());checks=[]
for event in roots['checks']:
 index=event['from_index'];ordinal=event['ordinal'];kind=event['identity'][0];data=Path(prefix+f'-dense-{index:02d}-native-scene.bin').read_bytes();assert hashlib.sha256(data).hexdigest()==event['packet_sha256'];sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+j*12) for j in range(5))};at=8
 for j in range(ordinal+1):
  n,w,h=struct.unpack_from('<3I',sections[2],at);uv=struct.unpack_from('<'+str(n*2)+'d',sections[2],at+12+n*24);at+=12+n*40+w*h*4
 raw=Raw();raw.count=n;trace_hash=None
 if kind==1:
  trace=Path(prefix+f'-dense-{index:02d}-near-{ordinal}-isolated.ppm.edges.csv');rows=list(csv.DictReader(trace.read_text().splitlines()));assert len(rows)==n;trace_hash=hashlib.sha256(trace.read_bytes()).hexdigest()
  for field in ['shift','height','affine']:setattr(raw,field,int(rows[0][field]))
  raw.offset[:]=[int(rows[0]['offset0']),int(rows[0]['offset1'])]
  for row in rows:raw.attrs[int(row['edge'])][:]=[int(row['a2']),int(row['a3'])]
 for root in event['roots']:
  moving=root['vertex'];expected=[uv[moving*2],uv[moving*2+1]]
  if kind==1:
   value=(C.c_double*2)();assert corner(64,raw.attrs[moving],raw.shift,raw.height,raw.affine,table,value);expected=[value[0]+raw.offset[0]/(256*(1<<raw.shift)),value[1]+raw.offset[1]/(256*raw.height)]
  samples=[]
  for sample in root['samples']:
   points=sample['camera_vertices'];vertices=(Vertex*n)(*[Vertex(*point,uv[i*2],uv[i*2+1]) for i,point in enumerate(points)]);out=(Vertex*64)();count=C.c_uint();adjusted=C.c_uint()
   if kind==1:assert clip(vertices,n,C.byref(raw),table,out,C.byref(count),C.byref(adjusted))
   else:count.value=generic(vertices,n,out)
   # Source-order topology determines exactly which retained/generated corners
   # approach this vertex. No nearest-screen or polygon correspondence.
   approaching=[];out_index=0
   for i in range(n):
    previous=(i+n-1)%n;cross=(points[previous][2]<64)!=(points[i][2]<64)
    if cross:
     if moving in (previous,i):approaching.append(out[out_index])
     out_index+=1
    if points[i][2]>=64:
     if i==moving:approaching.append(out[out_index])
     out_index+=1
   assert out_index==count.value and approaching
   errors=[math.hypot(v.u-expected[0],v.v-expected[1]) for v in approaching];distance=[math.dist([v.x,v.y,v.z],root['camera_vertices'][moving]) for v in approaching];assert all(math.isfinite(x) for x in errors+distance)
   samples.append(dict(refresh_offset=sample['refresh_offset'],moving_depth=points[moving][2],approaching_vertices=len(approaching),uv_error=max(errors),position_error=max(distance),generated_count=count.value,adjusted=adjusted.value))
  checks.append(dict(identity=event['identity'],moving_vertex=moving,target=root['target'],source_trace_sha256=trace_hash,samples=samples))
out=Path(prefix+'-dense-camera-clip-limit-audit.json');out.write_text(json.dumps(dict(result='MEASURED',root_report_sha256=hashlib.sha256(root_path.read_bytes()).hexdigest(),component_sha256=hashlib.sha256((p/'road-clip-component.dll').read_bytes()).hexdigest(),checks=checks,scope='Actual retained-camera samples on both sides of near-plane roots through unchanged production road correction and generic wall clipping components. Source-order corners tracked exactly. Frozen source material/UV per interval; no original raster parity, live full-scene or scanout smoothness proof.'),indent=2));print(json.dumps(dict(report=str(out),roots=len(checks),smallest_offset_max_uv_error=max(s['uv_error'] for c in checks for s in c['samples'] if abs(s['refresh_offset'])==1e-7),smallest_offset_max_position_error=max(s['position_error'] for c in checks for s in c['samples'] if abs(s['refresh_offset'])==1e-7))))
