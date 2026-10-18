"""Native road horizontal attribute clipping versus original ARM routine."""
from pathlib import Path
import ctypes as C,json,struct,random,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nf_road_polygon_clip;fn.argtypes=[C.c_void_p,C.c_uint,C.c_int32,C.c_int32,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
reciprocal=C.create_string_buffer(rom[0x627700:0x647700]);u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)):u.mem_map(a,n)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,(p/'visibility-overflow-171-wide/iwram.bin').read_bytes())
rng=random.Random(43003);vertices=0;atomic=0
for case in range(628):
 count=rng.randrange(3,17);left=rng.randrange(0,100);right=rng.randrange(left,241)
 if case>=500:left=rng.randrange(1,241);right=rng.randrange(left)
 rows=[[rng.randrange(-200,441)]+[rng.randrange(-1000000,1000001) for j in range(5)] for i in range(count)]
 raw=struct.pack('<'+'i'*count*6,*(v for row in rows for v in row));state=bytearray(256);struct.pack_into('<I',state,108,0x02001000);struct.pack_into('<2H',state,226,left,right);struct.pack_into('<H',state,242,count)
 u.mem_write(0x030000c0,bytes(state));u.mem_write(0x02001000,raw+b'\0'*3072)
 for reg,v in ((UC_ARM_REG_R0,0x030000c0),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,v)
 u.emu_start(0x03000efc,0x03006000,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 n=struct.unpack('<H',bytes(u.mem_read(0x030000c0+244,2)))[0];expected=bytes(u.mem_read(0x02001000+count*24,n*24))
 out=C.create_string_buffer(b'X'*3072,3072);actual=C.c_uint(123);assert fn(raw,count,left,right,reciprocal,out,128,C.byref(actual))
 
 if actual.value!=n or out.raw[:n*24]!=expected:
  print('CASE',case,'bounds',left,right,'rows',rows,'count',n,actual.value)
  print('expected',[struct.unpack_from('<6i',expected,i*24) for i in range(n)]);print('actual',[struct.unpack_from('<6i',out.raw,i*24) for i in range(actual.value)]);raise SystemExit(1)
 vertices+=n
 if n:
  out=C.create_string_buffer(b'X'*3072,3072);actual=C.c_uint(123)
  assert not fn(raw,count,left,right,reciprocal,out,n-1,C.byref(actual)) and out.raw==b'X'*3072 and actual.value==123;atomic+=1
out=C.create_string_buffer(b'X'*3072,3072);n=C.c_uint(123)
for count,left,right in ((65,0,240),):
 assert not fn(raw,count,left,right,reciprocal,out,128,C.byref(n)) and out.raw==b'X'*3072 and n.value==123;atomic+=1
captured=[json.loads((p/f'road-polygon-parity-{a}.json').read_text()) for a in ('0.25','0.5','0.75')]
report=dict(result='PASS',random_original_arm_cases=628,reversed_bounds_original_arm_cases=128,random_output_vertices=vertices,atomic_rejections=atomic,captured_road_occurrences=sum(len(c['cases']) for c in captured),scope='Exact six-word projected attribute clipping against original03000efc, including UV/depth interpolation and order. Native world renderer/live eligibility integration and raster padding are not verified.')
(p/'road-polygon-clip-tests.json').write_text(json.dumps(report,indent=2));print(report)
