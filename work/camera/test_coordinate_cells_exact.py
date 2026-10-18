import random,struct
from pathlib import Path
from owned_portal_continuous import coordinate,cells
from owned_portal_transform import signed32
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);rng=random.Random(61006)
for i in range(10000):
 x=rng.uniform(-32768,32767);z=rng.uniform(1,len(table)-1.001);scale=rng.choice((64,128,256,512));center=rng.randrange(-240,241)
 if i%3==0:x=float(int(x))
 if i%5==0:z=float(int(z))
 expected=cells((x,z),lambda v,d:center+(signed32((signed32(table[d]*scale)>>7)*(v>>1))>>16))
 assert coordinate(x,z,scale,center,table)==expected,(i,x,z)
print('PASS 10000 fractional/integer coordinate cells bit-exact including signed arithmetic')
