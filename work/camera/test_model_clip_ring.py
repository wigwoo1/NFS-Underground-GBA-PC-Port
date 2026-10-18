import ctypes as C,random,struct
from model_clip_arm_oracle import clip,rom
lib=C.CDLL('work/camera/visibility-probe-wide.dll');fn=lib.nfs_model_clip_ring;fn.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
table=C.create_string_buffer(rom[0x627700:0x647700]);rng=random.Random(0x4270);rect=[0,0,240,160];checked=0
for case in range(500):
 if case%2:
  x1,x2=sorted([rng.randrange(-80,321),rng.randrange(-80,321)]);y1,y2=sorted([rng.randrange(-80,241),rng.randrange(-80,241)]);points=[[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
 else:points=[[rng.choice([-80,0,1,239,240,320]),rng.choice([-80,0,1,159,160,240])] for _ in range(3)]
 uv=[[rng.randrange(65536),rng.randrange(65536)] for _ in points]
 inside=[any(rect[a]<=p[a]<rect[a+2] for p in points) for a in range(2)]
 if not all(inside):continue
 flags=sum((1<<a) for a in range(2) if any(p[a]<rect[a] or p[a]>=rect[a+2] for p in points))
 if not flags:continue
 reference=clip(points,uv,rect,flags);data=[v for p,t in zip(points,uv) for v in (*p,*t)];out=(C.c_int32*256)();n=C.c_uint()
 assert fn((C.c_int32*len(data))(*data),len(points),(C.c_int32*4)(*rect),flags,table,out,64,C.byref(n))
 xy=[list(out[i*4:i*4+2]) for i in range(n.value)];tex=[list(out[i*4+2:i*4+4]) for i in range(n.value)]
 assert (xy,tex)==(reference['points'],reference['uv']),(case,points,uv,flags,xy,tex,reference)
 checked+=1
assert checked>=100
print('PASS',checked,'complete original ARM partial triangle/quad/boundary XY/UV rings')

