"""Native vertical road edge step versus original ARM03002f88."""
from pathlib import Path
import ctypes as C,struct,json,random,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();recip=C.create_string_buffer(rom[0x627700:0x647700])
d=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));fn=d.nf_road_edge_step;fn.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)):u.mem_map(a,n)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,(p/'visibility-overflow-171-wide/iwram.bin').read_bytes());rng=random.Random(2302);accepted=rejected=0
for case in range(500):
 count=rng.randrange(3,17);rows=[[rng.randrange(-200,441),rng.randrange(-50,220),rng.randrange(-1000,1000)]+[rng.randrange(-1000000,1000001) for j in range(3)] for i in range(count)]
 vertices=struct.pack('<'+'i'*count*6,*(v for row in rows for v in row));c=[rng.randrange(0,10000) for j in range(18)];c[2]=rng.randrange(count);c[8]=count;c[10]=0x02001000;c[11]=count;c[12]=rng.randrange(0,60);c[13]=rng.randrange(c[12]+1,161);c[17]=0x02008000;raw=struct.pack('<18I',*c);fb=struct.pack('<4I',0x0600a000,0,0,240);side=rng.randrange(2);orientation=rng.randrange(2)
 u.mem_write(0x02001000,vertices);u.mem_write(0x02008000,fb);u.mem_write(0x03007b00,raw)
 for reg,val in ((UC_ARM_REG_R0,0x03007b00),(UC_ARM_REG_R1,side),(UC_ARM_REG_R2,orientation),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,val)
 u.emu_start(0x03002f88,0x03006000,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 expected_status=u.reg_read(UC_ARM_REG_R0);out=C.create_string_buffer(b'X'*72,72);status=fn(raw,side,orientation,vertices,count,recip,fb,out);assert status==expected_status,case
 if status:assert out.raw==bytes(u.mem_read(0x03007b00,72)),case;accepted+=1
 else:assert out.raw==b'X'*72;rejected+=1
out=C.create_string_buffer(b'X'*72,72);bad=list(c);bad[2]=count
assert fn(struct.pack('<18I',*bad),side,orientation,vertices,count,recip,fb,out)==-1 and out.raw==b'X'*72
captured=[json.loads((p/f'road-edge-parity-{a}.json').read_text()) for a in ('0.25','0.5','0.75')]
report=dict(result='PASS',random_original_arm_cases=500,accepted=accepted,rejected=rejected,captured_calls=sum(v['calls'] for v in captured),captured_accepted=sum(v['accepted'] for v in captured),invalid_index_atomic=True,scope='Original road edge traversal/top trimming and complete72byte context parity. Does not verify native span raster/full-scene live timing.')
(p/'road-edge-tests.json').write_text(json.dumps(report,indent=2));print(report)
