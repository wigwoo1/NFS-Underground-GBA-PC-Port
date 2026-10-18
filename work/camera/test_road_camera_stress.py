"""Original low-word camera arithmetic independent stress oracle."""
from pathlib import Path
import ctypes as C,json,random
p=Path('work/camera');d=C.CDLL(str((p/'road-camera-continuous.dll').resolve()));f=d.nf_road_camera_continuous;f.argtypes=[C.POINTER(C.c_double),C.POINTER(C.c_int32),C.POINTER(C.c_double)]
r=random.Random(140005);checks=0
si=lambda x:((x+2**31)%2**32)-2**31
half=lambda x:((x+32768)%65536)-32768
def oracle(v,m):
 x=v[0]+m[9];z=v[2]+m[11]
 return [half(si(x*m[0]+z*m[6])>>14),v[1]+m[10],half(si(x*m[2]+z*m[8])>>14)]
for n in range(2000):
 m=[r.randrange(-2**31,2**31) for _ in range(12)];v=[r.randrange(-2**31,2**31-1) for _ in range(3)];out=(C.c_double*3)();assert f((C.c_double*3)(*v),(C.c_int32*12)(*m),out);assert list(out)==oracle(v,m);checks+=1
 # Independent convex interpolation of four original integer corners.
 fx,fz=r.random(),r.random();q=[v[0]+fx,v[1]+.25,v[2]+fz];assert f((C.c_double*3)(*q),(C.c_int32*12)(*m),out)
 actual_fx=q[0]-v[0];actual_fz=q[2]-v[2];expected=[0,q[1]+m[10],0]
 for a in range(2):
  for b in range(2):
   w=(actual_fx if a else 1-actual_fx)*(actual_fz if b else 1-actual_fz);corner=oracle([v[0]+a,v[1],v[2]+b],m)
   for k in (0,2):expected[k]+=w*corner[k]
 assert max(abs(a-b) for a,b in zip(out,expected))<1e-8;checks+=1
report=dict(result='PASS',checks=checks,seed=140005,scope='Integer low32 wrap and independent fractional fixed-matrix interpolation. Extreme wrap transitions are not representative motion evidence. Snapshot already owns view[12]; prepared_view exports it. Packet road material trailer still lacks raw matrix.')
(p/'road-camera-stress-tests.json').write_text(json.dumps(report,indent=2));print(report)
