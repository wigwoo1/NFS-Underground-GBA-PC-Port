import random,math,struct
from owned_road_rigid_candidate import rigid_points,helper
from owned_sampled_road_camera import _rigid
r=random.Random(61006);sumfn=helper().nf_compensated_sum3
cases=[(1e16,1.,-1e16),(0.,-0.,0.),(-0.,-0.,-0.),(float('inf'),1.,2.),(float('inf'),float('-inf'),0.)]
cases.extend(tuple(math.ldexp(r.uniform(-1,1),r.randint(-500,500)) for _ in range(3)) for _ in range(10000))
for terms in cases:
 a=sumfn(*terms);b=sum(terms)
 assert math.isnan(a) and math.isnan(b) or struct.pack('d',a)==struct.pack('d',b),(terms,a,b)
for n in (1,2,8,32):
 for _ in range(200):
  world=tuple(r.uniform(-1e6,1e6) for _ in range(n*3));pose=tuple(r.uniform(-10,10) for _ in range(12))
  expected=tuple(v for i in range(0,len(world),3) for v in _rigid(world[i:i+3],pose));actual=rigid_points(world,pose)
  assert all(struct.pack('d',a)==struct.pack('d',b) for a,b in zip(actual,expected))
print('PASS:10005 compensated sum bit comparisons and800 exact rigid road batches')
