import ctypes as C,json,math
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'source-triangle-packet-candidate.dll').resolve()));P=C.c_void_p;f=d.nf_source_triangle_packet;f.argtypes=[P,C.c_uint,P,P,P,C.c_uint,P]
def emit(points,capacity=186):
 a=(C.c_double*len(points))(*points);projection=(C.c_double*3)(120,87,128);color=(C.c_double*4)(1,1,1,1);out=(C.c_double*1860)();written=C.c_uint(999);r=f(a,len(points)//5,projection,color,out,capacity,C.byref(written));return r,written.value,list(out)[:written.value*10]
r,n,v=emit([-1,-1,32,0,0,1,-1,128,1,0,0,1,128,0,1]);assert r==0 and n==6 and all(math.isfinite(x) for x in v)
assert emit([-1,-1,32,0,0,1,-1,32,1,0,0,1,32,0,1])[1]==0
assert emit([-1,-1,128,0,0,1,-1,128,1,0,0,1,128,0,1],2)[:2]==(2,0)
assert emit([float('nan'),-1,128,0,0,1,-1,128,1,0,0,1,128,0,1])[0]==1
result=dict(result='PASS_SOURCE_TRIANGLE_PACKET_COMPONENT',crossing_near_plane_vertices=n,fully_clipped_zero=True,capacity_rejected=True,nonfinite_rejected=True,scope='Source camera-space emitter component only; live geometry decoding and complete D3D integration pending.')
(p/'prototype-runs/source-triangle-packet-component.json').write_text(json.dumps(result,indent=2));print(result)
