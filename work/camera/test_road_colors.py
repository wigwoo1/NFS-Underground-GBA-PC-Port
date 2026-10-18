"""Native affine road color samples versus original ARM030056d8."""
from pathlib import Path
import ctypes as C,struct,json,random,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000)):u.mem_map(a,n)
u.mem_write(0x03000000,(p/'visibility-overflow-171-wide/iwram.bin').read_bytes())
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);d=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));fn=d.nf_road_span_pixels;fn.argtypes=[C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_uint]
rng=random.Random(5656);fail_at=None;reads=0
@Read
def read(ctx,address,out,size):
 global reads
 reads+=1
 if fail_at is not None and reads>=fail_at:return 0
 if not 0x02010000<=address<=0x02010000+len(texture)-size:return 0
 C.memmove(out,texture[address-0x02010000:address-0x02010000+size],size);return 1
samples=atomic=0
for case in range(500):
 shift=rng.randrange(1,7);height=rng.randrange(1,33);texture=rng.randbytes((1<<shift)*height*2);width=rng.randrange(0,121);doubled=case%2
 params=[shift,((1<<shift)<<16)-1,(height<<16)-1,0,0,0x02010000,0x06000000,width]+[rng.randrange(2**32) for j in range(4)];raw=struct.pack('<12I',*params)
 u.mem_write(0x02010000,texture);u.mem_write(0x02000000,raw);u.mem_write(0x03007098,struct.pack('<I',doubled));u.mem_write(0x06000000,b'X'*480)
 for reg,val in ((UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,val)
 u.emu_start(0x030056d8,0x03006000,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 out=C.create_string_buffer(b'X'*240,240);reads=0;assert fn(raw,read,None,out,120);expected=bytes(u.mem_read(0x06000000,width*2));assert out.raw[:width*2]==expected,case
 if doubled:assert bytes(u.mem_read(0x06000000+240,width*2))==expected
 samples+=width
 if width:
  out=C.create_string_buffer(b'X'*240,240);reads=0;fail_at=1+width//2
  assert not fn(raw,read,None,out,120) and out.raw==b'X'*240;fail_at=None;atomic+=1
  assert not fn(raw,read,None,out,width-1) and out.raw==b'X'*240;atomic+=1
captured=[json.loads((p/f'road-color-parity-{a}.json').read_text()) for a in ('0.25','0.5','0.75')]
report=dict(result='PASS',random_original_arm_cases=500,color_samples=samples,atomic_rejections=atomic,captured_spans=sum(c['spans'] for c in captured),captured_samples=sum(c['samples'] for c in captured),scope='Native resolved16bit texture span samples match original single/doubled row writer. Perspective subdivision and complete native renderer/live timing not covered.')
(p/'road-color-tests.json').write_text(json.dumps(report,indent=2));print(report)
