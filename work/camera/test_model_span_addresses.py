from pathlib import Path
import ctypes as C,struct,json,sys,random
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_READ
from unicorn.arm_const import *
p=Path('work/camera');code=(p/'motion-original-model-rect-iwram.bin').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000)]:u.mem_map(a,n)
u.mem_write(0x03000000,code);rng=random.Random(0x5920);tex=bytes(0 if i%5==0 else rng.randrange(1,256) for i in range(0x40000));u.mem_write(0x02000000,tex)
f=C.CDLL(str((p/'native_model.dll').resolve())).nfs_model_span_addresses;f.argtypes=[C.c_uint32,C.c_uint32,C.c_uint,C.c_uint]+[C.c_uint32]*4+[C.c_void_p]*2
reads=[]
def read(cpu,access,address,size,value,data):reads.append(address);assert size==1
u.hook_add(UC_HOOK_MEM_READ,read,begin=0x02000000,end=0x0203ffff);samples=zeros=0
for case in range(1000):
 count=rng.randrange(1,65);shift=rng.randrange(0,9);uv=[rng.randrange(-2048,2048) for _ in range(2)];step=[rng.randrange(-512,512) for _ in range(2)];destination=0x06000010+(case%2);source=0x02020000
 src=(C.c_uint32*240)();dst=(C.c_uint32*240)();assert f(source,destination,count,shift,*[v&0xffffffff for v in uv+step],src,dst)
 for offset,value in zip([0x5a30,0x5a34,0x5a38,0x5a3c,0x5a40],[shift,*uv,*step]):u.mem_write(struct.unpack_from('<I',code,offset)[0],struct.pack('<I',value&0xffffffff))
 initial=bytes([0xa5])*256;u.mem_write(0x06000000,initial)
 for reg,value in [(UC_ARM_REG_R0,source),(UC_ARM_REG_R1,destination),(UC_ARM_REG_R2,count),(UC_ARM_REG_SP,0x03007b00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,value)
 reads.clear();u.emu_start(0x03005920,0x03007000,count=5000);assert reads==list(src)[:count]
 expected=bytearray(initial)
 for i in range(count):value=tex[src[i]-0x02000000];expected[dst[i]-0x06000000]=value;zeros+=value==0
 assert bytes(u.mem_read(0x06000000,256))==expected
 samples+=count
r=dict(result='PASS_NATIVE_MODEL_SPAN_ADDRESSES_AND_WRITES',original_ARM_cases=1000,texture_samples=samples,opaque_zero_writes=zeros,scope='Random Q8 U/V and signed increments, fractional carry, odd/even destinations and adjacent-byte preservation against original model writer. Actual model scanline accumulators not yet reconstructed; no scene pixel or timing proof.')
(p/'model-span-address-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(r)
