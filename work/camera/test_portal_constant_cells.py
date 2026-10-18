from owned_portal_continuous import cells,coordinate
import math,json,struct
from pathlib import Path
for value in (-233,0,228,233):
 for point in ((.13,.71),(.99,.23),(1.31,2.79),(.7,.3,.13)):
  assert cells(point,lambda *args:value)==value
assert math.isclose(cells((.3,.7),lambda x,y:2*x+3*y),2.7,rel_tol=0,abs_tol=1e-14)
r=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
from owned_portal_transform import signed32
for x,z in ((30.71,6582.1316836586675),(80.99,6703.719910772843),(0.,128.),(-10.,257.)):
 expected=cells((x,z),lambda ix,iz:120+(signed32((signed32(r[iz]*128)>>7)*(ix>>1))>>16))
 assert coordinate(x,z,128,120,r)==expected
print('PASS constant cells, affine extension, specialized projection parity')
