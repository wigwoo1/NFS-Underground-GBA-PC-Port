"""Find near-plane roots using the actual retained-source camera interpolation."""
import ctypes as C,hashlib,json,struct,sys
from pathlib import Path
import numpy as np
manifest=Path(sys.argv[1]);session=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=session['prefix'];p=Path(__file__).resolve().parent;bridge=p/'visibility-probe-wide.dll';dll=C.CDLL(str(bridge));sample=dll.nf_rigid_scene_sample;sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p];pose_sample=dll.nf_pose_sample;pose_sample.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p]
source_path=Path(prefix+'-dense-source-identity-verification.json');source=json.loads(source_path.read_text());cameras={}
for row in source['original_endpoints']:
 data=Path(row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];offset,size=struct.unpack_from('<2I',data,36);models=data[offset:offset+size];at=struct.unpack_from('<I',models,8)[0] if models[:4]==b'NML1' else 0;cameras[row['identity'][3]]=np.array(struct.unpack_from('<7d',models,at+48),dtype=np.float64)
refreshes=sorted(cameras);fixed=np.array([0,0,0,0,0,0,1],dtype=np.float64)
def transformed(vertices,t):
 intervals=[(a,b) for a,b in zip(refreshes,refreshes[1:]) if a<=t<=b];assert intervals
 a,b=intervals[0];alpha=(t-a)/(b-a);out=np.empty_like(vertices);camera=np.empty(7);assert sample(cameras[a].ctypes.data,cameras[b].ctypes.data,fixed.ctypes.data,fixed.ctypes.data,alpha,vertices.ctypes.data,len(vertices),out.ctypes.data);assert pose_sample(cameras[a].ctypes.data,cameras[b].ctypes.data,alpha,camera.ctypes.data);return out,camera,[a,b],alpha
motion_path=Path(prefix+'-dense-projected-motion-audit.json');motion=json.loads(motion_path.read_text());checks=[]
for step in motion['steps']:
 for event in step['clipping_events']:
  if not event['near_crossing_vertices']:continue
  assert event['kind']=='world';index=step['from_index'];data=Path(prefix+f'-dense-{index:02d}-native-scene.bin').read_bytes();assert hashlib.sha256(data).hexdigest()==motion['frames'][index-1]['packet_sha256'];sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+j*12) for j in range(5))};at=8
  for j in range(event['from_ordinal']+1):
   n,w,h=struct.unpack_from('<3I',sections[2],at);vertices=np.frombuffer(sections[2][at+12:at+12+n*24],dtype='<f8').reshape(n,3).copy();at+=12+n*40+w*h*4
  reference=next(c for c in motion['frames'][index-1]['clipping'] if c['kind']=='world' and c['ordinal']==event['from_ordinal']);assert reference['identity']==event['identity']
  left=motion['frames'][index-1]['target'];right=motion['frames'][step['to_index']-1]['target'];a=transformed(vertices,left)[0];b=transformed(vertices,right)[0];roots=[];assert abs(float(a[:,2].min())-reference['depth_min'])<1e-7 and abs(float(a[:,2].max())-reference['depth_max'])<1e-7
  for vertex in event['near_crossing_vertices']:
   lo,hi=left,right;zlo=a[vertex,2]-64;zhi=b[vertex,2]-64;assert (zlo<0)!=(zhi<0)
   for iteration in range(48):
    mid=(lo+hi)/2;z=transformed(vertices,mid)[0][vertex,2]-64
    if (z<0)==(zlo<0):lo=mid;zlo=z
    else:hi=mid
   target=(lo+hi)/2;points,camera,interval,alpha=transformed(vertices,target);samples=[]
   for epsilon in [1e-3,1e-5,1e-7]:
    for side in [-1,1]:
     points_side,camera_side,source_pair,side_alpha=transformed(vertices,target+side*epsilon);samples.append(dict(refresh_offset=side*epsilon,depth=float(points_side[vertex,2]),camera=camera_side.tolist(),camera_vertices=points_side.tolist(),source_refreshes=source_pair,alpha=side_alpha))
   assert (samples[-2]['depth']<64)!=(samples[-1]['depth']<64)
   roots.append(dict(vertex=vertex,target=target,depth_residual=float(points[vertex,2]-64),bracket_width_refreshes=hi-lo,source_refreshes=interval,alpha=alpha,camera=camera.tolist(),camera_vertices=points.tolist(),samples=samples))
  checks.append(dict(from_index=index,to_index=step['to_index'],identity=event['identity'],ordinal=event['from_ordinal'],packet_sha256=hashlib.sha256(data).hexdigest(),roots=roots))
out=Path(prefix+'-dense-camera-near-roots.json');out.write_text(json.dumps(dict(result='LOCATED',bridge_sha256=hashlib.sha256(bridge.read_bytes()).hexdigest(),source_report_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),motion_report_sha256=hashlib.sha256(motion_path.read_bytes()).hexdigest(),checks=checks,scope='Actual native rigid camera interpolation from hashvalidated original camera endpoints, piecewise at source refresh boundaries. Bisection roots within measured crossing frame pairs and both-side camera-space samples. World geometry immutable. Root/depth evidence only; no UV/raster or whole-game smoothness proof.'),indent=2));print(json.dumps(dict(report=str(out),events=len(checks),roots=sum(len(c['roots']) for c in checks),maximum_depth_residual=max(abs(r['depth_residual']) for c in checks for r in c['roots']))))
