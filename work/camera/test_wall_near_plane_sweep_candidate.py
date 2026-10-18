import ctypes as C,itertools,json
from pathlib import Path
import numpy as np
root=Path('work/camera');d=C.CDLL(str((root/'owned-gpu-source-profile-provenance-candidate.dll').resolve()));f=d.nf_source_triangle_packet;f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
projection=(C.c_double*3)(120,87,128);color=(C.c_double*4)(1,1,1,1);cases=0;crossing_cases=0;empty=0;maximum_error=0
for depths in itertools.product((32.,64.,64.0001,128.),repeat=4):
 points=np.array([[-10,-10,depths[0],0,0],[10,-10,depths[1],1,0],[10,10,depths[2],1,1],[-10,10,depths[3],0,1]],dtype=np.float64)
 candidates=[p for p in points if p[2]>=64]
 crossings=0
 for i,p in enumerate(points):
  q=points[(i+1)%4]
  if (p[2]<64)!=(q[2]<64):
   weight=(64-p[2])/(q[2]-p[2]);intersection=p*(1-weight)+q*weight;intersection[2]=64;candidates.append(intersection);crossings+=1
 expected_count=0 if len(candidates)<3 else (len(candidates)-2)*3
 source=(C.c_double*20)(*points.reshape(-1));out=(C.c_double*3780)();written=C.c_uint()
 assert f(source,4,projection,color,out,378,C.byref(written))==0 and written.value==expected_count
 vertices=np.array(list(out)[:written.value*10]).reshape(-1,10)
 if not len(vertices):empty+=1
 for vertex in vertices:
  assert np.isfinite(vertex).all() and vertex[5]>0 and vertex[4]==0 and np.array_equal(vertex[6:],np.ones(4))
  z=1/vertex[5];recovered=np.array([(vertex[0]-120)*z/128,(vertex[1]-87)*z/128,z,vertex[2]*z,vertex[3]*z]);assert z>=64-1e-10
  error=min(np.max(np.abs(recovered-point)) for point in candidates);maximum_error=max(maximum_error,float(error));assert error<1e-9
 if crossings:crossing_cases+=1
 cases+=1
result=dict(result='PASS_WALL_NEAR_PLANE_PROJECTIVE_SWEEP',cases=cases,crossing_cases=crossing_cases,fully_clipped_cases=empty,maximum_recovered_point_error=maximum_error,scope='256 synthetic four-corner wall depth combinations against actual backend emitter. Independent source-edge intersection set and inverse projection checks. Not actual captured wall crossing or original visibility proof.')
(root/'prototype-runs/wall-near-plane-sweep-20261009.json').write_text(json.dumps(result,indent=2));print(result)
