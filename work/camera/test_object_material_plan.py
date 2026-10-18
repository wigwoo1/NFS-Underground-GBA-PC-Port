from pathlib import Path
import ctypes as C,struct,random,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);fn=d.nfs_visibility_object_material_plan;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,65536),(0x03000000,65536),(0x04000000,65536),(0x08000000,0x800000)):u.mem_map(a,n)
u.mem_write(0x03000000,(p/'visibility-overflow-171-wide/iwram.bin').read_bytes());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u.mem_write(0x08000000,rom);reciprocal=C.create_string_buffer(rom[0x627700:0x647700]);r=random.Random(2368);branches=[]
def stop(cpu,pc,n,ctx):
 if pc in (0x03002460,0x03002588,0x0300262c):cpu.emu_stop()
u.hook_add(UC_HOOK_CODE,stop)
@Read
def read(ctx,a,out,n):
 try:C.memmove(out,bytes(u.mem_read(a,n)),n);return 1
 except Exception:return 0
for trial in range(500):
 state=bytearray(256);obj=bytearray(r.randbytes(164));flags=r.randrange(128)&~16;struct.pack_into('<H',obj,10,flags)
 for off,val in ((54,r.randrange(4)),(72,r.randrange(1,12)),(70,r.randrange(5)),(68,r.randrange(65536))):struct.pack_into('<H',obj,off,val)
 for off,val in ((4,0x0200c000),(36,0x02002000),(80,0x02001000)):struct.pack_into('<I',state,off,val)
 struct.pack_into('<2H',state,230,0,158);projection=bytearray(32);scale=r.randrange(100,10000);struct.pack_into('<h',projection,10,80);struct.pack_into('<I',projection,28,scale);materials=r.randbytes(32768);depth=r.randrange(10000);y=r.randrange(-1000,1001);xyz=(C.c_uint32*3)(0,y&0xffffffff,depth)
 u.mem_write(0x02000000,bytes(state));u.mem_write(0x02001000,bytes(projection));u.mem_write(0x02002000,materials);u.mem_write(0x0200b000,bytes(obj));u.mem_write(0x04008000,bytes(256));u.mem_write(0x0400800c,struct.pack('<I',y&0xffffffff));u.mem_write(0x04008018,struct.pack('<2I',scale,80))
 owned=C.create_string_buffer(bytes(obj),164);out=C.create_string_buffer(b'X'*16,16);status=fn(bytes(state),owned,xyz,read,None,reciprocal,out);assert status>=0
 for reg,val in ((UC_ARM_REG_R6,0x02000000),(UC_ARM_REG_R7,0x0200b000),(UC_ARM_REG_SP,0x04008000),(UC_ARM_REG_R12,depth),(UC_ARM_REG_LR,flags),(UC_ARM_REG_R8,0),(UC_ARM_REG_R10,158)):u.reg_write(reg,val)
 u.emu_start(0x03002368,0x03002640,count=1000);pc=u.reg_read(UC_ARM_REG_PC);assert bytes(u.mem_read(0x0200b000,164))==owned.raw
 if status:
  assert pc in (0x03002460,0x03002588);actual=[u.reg_read(UC_ARM_REG_R4),u.reg_read(UC_ARM_REG_R12),struct.unpack('<I',bytes(u.mem_read(0x04008004,4)))[0],int(pc==0x03002460)];assert list(struct.unpack('<4I',out.raw))==actual;branches.append(actual[3])
 else:assert pc==0x0300262c and out.raw==b'X'*16;branches.append(-1)
report=dict(result='PASS',original_ARM_cases=500,billboards=branches.count(1),models=branches.count(0),culled=branches.count(-1),scope='Original2368..245C cull/material/texture branch and full object bytes; no raster execution.')
(p/'object-material-plan-tests.json').write_text(json.dumps(report,indent=2));print(report)
