import ctypes as C,random
from owned_ring_sample_candidate import helper,inputs
r=random.Random(20261006)
def native(worlds,deltas,camera,alpha):
 w,d=inputs(tuple(worlds),tuple(deltas));cam=(C.c_double*12)(*camera);out=(C.c_double*(len(worlds)*2))();status=helper().nf_sample_ring_points(w,d,len(worlds),cam,alpha,out);return status,tuple((out[i*2],out[i*2+1]) for i in range(len(worlds)))
def prior(worlds,deltas,camera,alpha):
 points=[]
 for (wx,wz),(ax,az,bx,bz) in zip(worlds,deltas):
  x=(wx+camera[9])*camera[0]+(wz+camera[11])*camera[6];z=(wx+camera[9])*camera[2]+(wz+camera[11])*camera[8]
  points.append((x+(1-alpha)*ax+alpha*bx,z+(1-alpha)*az+alpha*bz))
 status=2 if any(z>24575 for _,z in points) else -1 if any(not -32768<=v<32768 for p in points for v in p) else 1
 return status,tuple(points)
for n in (1,2,8,32):
 for _ in range(200):
  worlds=[(r.randint(-100000,100000),r.randint(-100000,100000)) for _ in range(n)]
  deltas=[tuple(r.uniform(-1000,1000) for _ in range(4)) for _ in range(n)];camera=tuple(r.uniform(-2,2) for _ in range(12));alpha=r.random()
  assert native(worlds,deltas,camera,alpha)==prior(worlds,deltas,camera,alpha)
cam=(1.,0.,0.,0.,0.,0.,0.,0.,1.,0.,0.,0.)
assert native([(40000,30000)],[(0.,)*4],cam,.5)[0]==2
assert native([(40000,0)],[(0.,)*4],cam,.5)[0]==-1
print('PASS:800 exact sampled batches; far-before-wrap precedence and wrap rejection')
