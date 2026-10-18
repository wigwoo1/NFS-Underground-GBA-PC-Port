import runpy,sys,ctypes as C,struct
from pathlib import Path
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
v=runpy.run_path('work/camera/audit_failed_world_motion.py');h=EndpointRoadPlanner(v['rom'],v['data']['table']);roads,_=h.plan(v['scenes'][0].graph);p=PreparedWorldMotion(*v['data']['frames'],*v['scenes'],h,roads,v['rom']);frame,cm,models,*_=p.sample(.03)
d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_pose_face_visible.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_double,C.c_void_p]
for index,row in enumerate(records(frame)['records']):
 if row['kind']!=3:continue
 b=row['blocks'];m=models[index*12:index*12+12];verts=[struct.unpack_from('<3h',b[4],j) for j in range(0,len(b[4]),6)];camera=[[m[9+k]+sum(local[c]*m[c*3+k] for c in range(3)) for k in range(3)] for local in verts];offset=0
 for face,n in enumerate(b[5]):
  ids=struct.unpack_from('<'+'H'*n,b[6],offset*2);offset+=n;polygon=[]
  for j in range(n):
   a=camera[ids[(j+n-1)%n]];z=camera[ids[j]];ai=a[2]>=64;bi=z[2]>=64
   if ai!=bi:
    t=(64-a[2])/(z[2]-a[2]);polygon.append([a[k]+t*(z[k]-a[k]) for k in range(3)])
   if bi:polygon.append(z)
  if len(polygon)<3:continue
  raw=(C.c_double*(len(polygon)*5))(*[q for point in polygon for q in (*point,0,0)]);rect=(C.c_int32*4)(*struct.unpack('<4i',b[9]));scale=struct.unpack_from('<I',b[0],64)[0];cx,cy=struct.unpack_from('<2h',b[3],8);result=d.nf_owned_pose_face_visible(raw,len(polygon),scale,cx,cy,rect)
  if result<0:print('INVALID',index,face,'depths',[point[2] for point in polygon], 'near-plane-error', min(point[2] for point in polygon)-64)
p.close();h.close()
