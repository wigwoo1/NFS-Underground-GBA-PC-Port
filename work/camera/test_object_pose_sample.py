"""Independent quaternion interpolation and fixed-point object adapter tests."""
from pathlib import Path
import ctypes as C,math,random,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
fn=d.nf_object_pose_sample;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_void_p]
def normalize(q):
 n=math.sqrt(sum(v*v for v in q));return [v/n for v in q]
def reference(a,b,t):
 qa=normalize(a[3:]);qb=normalize(b[3:]);dot=sum(x*y for x,y in zip(qa,qb))
 if dot<0:qb=[-v for v in qb];dot=-dot
 theta=math.acos(min(dot,1))
 if dot>=.9995:q=normalize([(1-t)*x+t*y for x,y in zip(qa,qb)])
 else:q=normalize([(math.sin((1-t)*theta)*x+math.sin(t*theta)*y)/math.sin(theta) for x,y in zip(qa,qb)])
 x,y,z,w=q
 # Independently form column vectors of quaternion action on world basis.
 columns=[1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w),2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w),2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y)]
 def rounded(v):return int(math.copysign(math.floor(abs(v)+.5),v))
 return [rounded(((1-t)*a[i]+t*b[i])*256) for i in range(3)],[rounded(v*16384) for v in columns]+[0,0,0]
r=random.Random(314);record=bytes(r.randrange(256) for _ in range(164));cases=0
for i in range(120):
 a=[r.uniform(-20000,20000) for _ in range(3)]+[r.uniform(-1,1) for _ in range(4)];b=[r.uniform(-20000,20000) for _ in range(3)]+[r.uniform(-1,1) for _ in range(4)]
 if i==0:b=a[:3]+[-v for v in a[3:]]
 for t in (0,.25,.5,.75,1):
  out=C.create_string_buffer(b'X'*164,164);rot=C.create_string_buffer(b'Y'*48,48)
  assert fn(record,struct.pack('<7d',*a),struct.pack('<7d',*b),t,out,rot)
  xyz,matrix=reference(a,b,t);assert list(struct.unpack_from('<3i',out.raw,12))==xyz
  assert list(struct.unpack('<12i',rot.raw))==matrix
  assert out.raw[:12]==record[:12] and out.raw[24:]==record[24:];cases+=1
  # Supported in-place owned record update preserves unrelated fields.
  alias=C.create_string_buffer(record,164);aliasrot=C.create_string_buffer(48)
  assert fn(alias,struct.pack('<7d',*a),struct.pack('<7d',*b),t,alias,aliasrot) and alias.raw==out.raw and aliasrot.raw==rot.raw
valid=[0,0,0,0,0,0,1];rejected=0
for a,b,t in ((valid,valid,float('nan')),(valid,valid,-.1),(valid,valid,1.1),([float('inf')]+valid[1:],valid,.5),([0]*7,valid,.5),([1e20]+valid[1:],valid,0)):
 out=C.create_string_buffer(b'X'*164,164);rot=C.create_string_buffer(b'Y'*48,48)
 assert not fn(record,struct.pack('<7d',*a),struct.pack('<7d',*b),t,out,rot)
 assert out.raw==b'X'*164 and rot.raw==b'Y'*48;rejected+=1
report=dict(result='PASS',independent_pose_cases=cases,in_place_cases=cases,atomic_rejections=rejected,scope='Native presentation-only object record/Q14 rotation adapter. No live timing or full-scene proof.')
(p/'object-pose-sample-tests.json').write_text(json.dumps(report,indent=2));print(report)
