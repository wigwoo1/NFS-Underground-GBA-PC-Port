"""Native perspective road subdivision versus original ARM03003190."""
from pathlib import Path
import ctypes as C,struct,json,random,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();recip=rom[0x627700:0x647700]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)):u.mem_map(a,n)
u.mem_write(0x03000000,(p/'visibility-overflow-171-wide/iwram.bin').read_bytes());u.mem_write(0x08000000,rom)
spans=[]
def hook(cpu,pc,length,ctx):
 if pc==0x030056d8:spans.append(bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),64)));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
d=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));fn=d.nf_road_perspective_plan;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
rng=random.Random(3190);total=atomic=0
boundary_widths=[0,1,15,16,17,31,32,33,63,64,65,119,120]
width_histogram={};run_length_histogram={}
for case in range(500+len(boundary_widths)):
 width=boundary_widths[case] if case<len(boundary_widths) else rng.randrange(0,121);q=rng.randrange(5000,200000);qend=rng.randrange(q*4//5,q*6//5)
 values=[rng.randrange(2**32) for j in range(16)];values[4]=struct.unpack_from('<I',recip,width*4)[0]>>8;values[6]=0x06000000;values[7]=width;values[10]=q;values[13]=qend
 for i in (8,9,11,12):values[i]=rng.randrange(-500000,500001)&0xffffffff
 raw=struct.pack('<16I',*values);u.mem_write(0x02000000,raw);spans.clear()
 for reg,val in ((UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,val)
 u.emu_start(0x03003190,0x03006000,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 out=C.create_string_buffer(b'X'*2048,2048);final=C.create_string_buffer(b'Y'*64,64);n=C.c_uint(123);assert fn(raw,recip,out,32,C.byref(n),final)
 assert n.value==len(spans) and out.raw[:n.value*64]==b''.join(spans) and final.raw==bytes(u.mem_read(0x02000000,64)),case;total+=n.value
 width_histogram[width]=width_histogram.get(width,0)+1
 lengths=[struct.unpack_from('<I',run,28)[0] for run in spans]
 assert sum(lengths)==width and all(1<=length<=16 for length in lengths)
 for length in lengths:run_length_histogram[length]=run_length_histogram.get(length,0)+1
 if n.value:
  out=C.create_string_buffer(b'X'*2048,2048);final=C.create_string_buffer(b'Y'*64,64);count=C.c_uint(123)
  assert not fn(raw,recip,out,n.value-1,C.byref(count),final) and out.raw==b'X'*2048 and final.raw==b'Y'*64 and count.value==123;atomic+=1
captured=[json.loads((p/f'road-perspective-parity-{a}.json').read_text()) for a in ('0.25','0.5','0.75')]
report=dict(result='PASS',random_original_arm_cases=500,explicit_boundary_cases=len(boundary_widths),width_histogram=width_histogram,run_length_histogram=run_length_histogram,subspans=total,atomic_capacity_rejections=atomic,captured_calls=sum(c['calls'] for c in captured),captured_subspans=sum(c['subspans'] for c in captured),scope='Complete perspective subspan context/order and final mutation match original. Native high-resolution renderer and live timing not covered.')
(p/'road-perspective-tests.json').write_text(json.dumps(report,indent=2));print(report)
