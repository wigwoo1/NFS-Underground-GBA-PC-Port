import random,struct
from owned_ring_correction_candidate import corrections
from owned_continuous_wall_visibility import _ring_endpoint_corrections as prior
r=random.Random(20261006);count=0
for n in (1,2,8,32):
 for _ in range(100):
  ring=bytearray(n*68);offsets=bytearray(n*32)
  for i in range(n):
   struct.pack_into('<2i',ring,i*68,r.randint(-2147450000,2147450000),r.randint(-2147450000,2147450000));struct.pack_into('<H',ring,i*68+42,r.choice((0,65535)))
   struct.pack_into('<2h',offsets,i*32,r.randint(-32768,32767),r.randint(-32768,32767))
  cameras=[struct.pack('<12i',*(r.randint(-2147483648,2147483647) for _ in range(12))) for _ in range(2)]
  endpoints=tuple(tuple(x/16384 for x in struct.unpack('<12i',c)) for c in cameras)
  args=(bytes(ring),bytes(offsets),*cameras,endpoints)
  assert corrections.__wrapped__(*args)==prior.__wrapped__(*args);count+=1
ring=bytearray(68);struct.pack_into('<i',ring,0,2147483647);offsets=bytearray(32);struct.pack_into('<h',offsets,0,1)
for fn in (corrections.__wrapped__,prior.__wrapped__):
 try:fn(bytes(ring),bytes(offsets),bytes(48),bytes(48),((0.,)*12,)*2)
 except ValueError as e:assert str(e)=='Unsupported sampled world offset wrap'
 else:raise AssertionError('Offset wrap accepted')
print('PASS:400 exact ring correction tuples,1/2/8/32points,signed wrap,offset activation and overflow rejection')
