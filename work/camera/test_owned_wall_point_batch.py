import ctypes as C,random,struct,time,statistics
from pathlib import Path
lib=C.CDLL(str(Path('work/camera/owned-wall-point-batch.dll').resolve()));f=lib.nf_owned_wall_point_batch;f.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_double,C.c_void_p]
r=random.Random(719)
for trial in range(100):
 world=[r.uniform(-1e5,1e5) for _ in range(64)];corr=[r.uniform(-1e3,1e3) for _ in range(128)];camera=[r.uniform(-2,2) for _ in range(12)];alpha=r.random()
 w=(C.c_double*64)(*world);c=(C.c_double*128)(*corr);m=(C.c_double*12)(*camera);out=(C.c_double*64)();assert f(w,c,32,m,alpha,out)==1
 expected=[]
 for i in range(32):
  wx,wz=world[i*2:i*2+2];x=(wx+camera[9])*camera[0]+(wz+camera[11])*camera[6];z=(wx+camera[9])*camera[2]+(wz+camera[11])*camera[8]
  expected.extend((x+(1-alpha)*corr[4*i]+alpha*corr[4*i+2],z+(1-alpha)*corr[4*i+1]+alpha*corr[4*i+3]))
 assert bytes(out)==struct.pack('<64d',*expected),trial
assert f(None,c,32,m,.5,out)==0 and f(w,c,65537,m,.5,out)==0 and f(w,c,32,m,float('nan'),out)==0
print('PASS3200 native wall point pairs binary-exact to Python; invalid pointer/count/alpha rejection')
