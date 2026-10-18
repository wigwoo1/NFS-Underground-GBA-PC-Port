import random,struct
from pathlib import Path
from owned_portal_continuous import coordinate,projection_depth,coordinate_at_depth
r=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);rng=random.Random(602)
for i in range(10000):
 x=rng.uniform(-32768,32767) if i%3 else rng.randrange(-32768,32768)
 z=rng.uniform(1,32765) if i%4 else rng.randrange(1,32766)
 scale=rng.choice((128,256,512,1024,65535));center=rng.randrange(-32768,32768)
 assert coordinate_at_depth(x,projection_depth(z,scale,r),center)==coordinate(x,z,scale,center,r)
for z in (0,32767):
 try:projection_depth(z,256,r);raise AssertionError('Invalid depth accepted')
 except ValueError:pass
print('PASS: 10000 exact old-coordinate comparisons, fractional/integer/negative/wrap values, depth-domain rejection')
