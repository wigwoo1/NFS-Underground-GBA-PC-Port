import random
from owned_portal_transform_batch import transform_pair
from owned_portal_transform import transform
r=random.Random(6)
for n in (1,2,32):
 for _ in range(100):
  points=tuple((r.randint(-2147483648,2147483647),r.randint(-2147483648,2147483647)) for _ in range(n))
  a=tuple(r.randint(-2147483648,2147483647) for _ in range(12));b=tuple(r.randint(-2147483648,2147483647) for _ in range(12))
  assert transform_pair(points,a,b)==tuple((*transform(x,z,a),*transform(x,z,b)) for x,z in points)
a=(0,)*12
for points,ma,mb in [((),a,a),(((0,0),)*33,a,a),(((2147483648,0),),a,a),(((0.5,0),),a,a),(((0,0),),a[:11],a)]:
 try:transform_pair(points,ma,mb)
 except ValueError:pass
 else:raise AssertionError('Invalid owned batch accepted')
print('PASS: exact owned batch at1/2/32points; count, signed32, type and camera length rejection')
