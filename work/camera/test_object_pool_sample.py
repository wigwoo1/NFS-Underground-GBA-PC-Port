"""Owned stable-slot interpolation, wrapped angles, selection and atomic publication."""
from pathlib import Path
import ctypes as C,struct,random,math,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nf_object_pool_sample_masked;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_double,C.c_void_p]
def nearest(x):return math.floor(x+.5) if x>=0 else math.ceil(x-.5)
def phase(a,b,mask,t):
 delta=(b-a)&mask
 if delta>(mask+1)//2:delta-=mask+1
 return (a+nearest(t*delta))&mask
rng=random.Random(20261003)
for trial in range(400):
 a=bytearray(rng.randbytes(3*164));b=bytearray(a);t=(.25,.5,.75)[trial%3];expected=bytearray(a)
 for slot in (0,2):
  off=slot*164;struct.pack_into('<H',a,off+72,1);struct.pack_into('<H',b,off+72,1);struct.pack_into('<H',expected,off+72,1)
  for j in (12,16,20):
   x=rng.randint(-2147483648,2147483647);y=rng.randint(-2147483648,2147483647);struct.pack_into('<i',a,off+j,x);struct.pack_into('<i',b,off+j,y);struct.pack_into('<i',expected,off+j,nearest((1-t)*x+t*y))
  for j in (48,50,52):
   x,y=rng.randrange(65536),rng.randrange(65536);struct.pack_into('<H',a,off+j,x);struct.pack_into('<H',b,off+j,y);struct.pack_into('<H',expected,off+j,phase(x,y,16383,t))
  x,y=rng.getrandbits(32),rng.getrandbits(32);struct.pack_into('<I',a,off+44,x);struct.pack_into('<I',b,off+44,y);struct.pack_into('<I',expected,off+44,(x&~0x3fffff)|phase(x,y,0x3fffff,t))
 # Unselected slot deliberately mismatches identity and contains unrelated bytes.
 b[164:328]=rng.randbytes(164);mask=bytes([5])+bytes(31);out=C.create_string_buffer(b'X'*len(a),len(a));assert fn(bytes(a),bytes(b),3,mask,t,out) and out.raw==expected
 alias=C.create_string_buffer(bytes(a),len(a));assert fn(alias,bytes(b),3,mask,t,alias) and alias.raw==expected
 for endpoint,record in [(0,a),(1,b)]:assert fn(bytes(a),bytes(b),3,mask,endpoint,out) and out.raw==record
bad=bytearray(b);struct.pack_into('<H',bad,78,struct.unpack_from('<H',a,78)[0]^1);out=C.create_string_buffer(b'X'*len(a),len(a));assert not fn(bytes(a),bytes(bad),3,mask,.5,out) and out.raw==b'X'*len(a)
for t in (-1,2,float('nan')):assert not fn(bytes(a),bytes(b),3,mask,t,out) and out.raw==b'X'*len(a)
transitions=0
for activation in (False,True):
 older=bytearray(a);newer=bytearray(b);struct.pack_into('<H',older,72,0 if activation else 1);struct.pack_into('<H',newer,72,1 if activation else 0)
 for t in (0,.25,.5,.75,1):
  output=C.create_string_buffer(b'X'*len(a),len(a));assert fn(bytes(older),bytes(newer),3,bytes([1])+bytes(31),t,output) and output.raw==(bytes(newer) if t==1 else bytes(older));transitions+=1
report=dict(result='PASS',synthetic_paired_cases=400,masked_unrelated_slots_preserved=400,aliased_outputs=400,exact_endpoints=800,discrete_activation_deactivation_samples=transitions,atomic_rejections=4,scope='Stable-slot presentation interpolation: Q8 xyz and wrapped Q14/Q22 heading, discrete state retained from older scene; activation/deactivation switches exactly at newer endpoint. No simulation advancement. Does not prove paired scene visibility or gameplay timing.')
(p/'object-pool-sample-tests.json').write_text(json.dumps(report,indent=2));print(report)
