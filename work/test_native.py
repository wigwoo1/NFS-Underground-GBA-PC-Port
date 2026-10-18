from pathlib import Path
import sys,struct,random,ctypes as C,json,time
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_LR,UC_ARM_REG_SP,UC_ARM_REG_PC
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
code=rom[0x771e4:0x771e4+0xc0]
class Span(C.Structure):
 _fields_=[(k,C.c_uint32)for k in ['width_shift','u_mask','v_mask','u','v','du','dv','count']]+[('duplicate_row',C.c_int)]
lib=C.CDLL(str(Path('work/native_span.dll').resolve()))
lib.nfs_draw_span.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.POINTER(Span)]
r=random.Random(0x4e4653)
emu=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for addr,size in [(0x03000000,0x10000),(0x02000000,0x40000),(0x08000000,0x100000),(0x06000000,0x20000)]:emu.mem_map(addr,size)
emu.mem_write(0x030056d8,code)
tex=r.randbytes(256*256*2);emu.mem_write(0x08000000,tex)
texture=C.create_string_buffer(tex)
t=time.perf_counter()
for test in range(1000):
 shift=r.choice([2,3,4,5,6,7,8]);um=(1<<r.randrange(1,shift+1))-1;vm=(1<<r.randrange(1,9))-1
 s=Span(shift,(um<<16)|65535,(vm<<16)|65535,r.getrandbits(32),r.getrandbits(32),r.getrandbits(32),r.getrandbits(32),r.choice([0,1,2,16,119,120,r.randrange(121)]),r.randrange(2))
 original=r.randbytes(480);dst=C.create_string_buffer(original)
 emu.mem_write(0x06000000,original)
 words=[shift,s.u_mask,s.v_mask,0,0,0x08000000,0x06000000,s.count,s.u,s.v,s.du,s.dv]
 emu.mem_write(0x02000000,struct.pack('<12I',*words));emu.mem_write(0x03007098,struct.pack('<I',s.duplicate_row))
 emu.reg_write(UC_ARM_REG_R0,0x02000000);emu.reg_write(UC_ARM_REG_SP,0x03007f00);emu.reg_write(UC_ARM_REG_LR,0x080ff000)
 emu.emu_start(0x030056d8,0x080ff000,count=10000)
 assert emu.reg_read(UC_ARM_REG_PC)==0x080ff000
 assert lib.nfs_draw_span(dst,480,texture,len(tex),C.byref(s))==1
 expected=bytes(emu.mem_read(0x06000000,480))
 assert dst.raw[:480]==expected, f'VRAM mismatch in test {test}'
# Invalid ranges must fail without modifying destination.
s=Span(8,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0,0,1,0)
dst=C.create_string_buffer(b'\xa5'*480)
assert lib.nfs_draw_span(dst,480,texture,len(tex),C.byref(s))==0 and dst.raw[:480]==b'\xa5'*480
result={'randomized_differential_cases':1000,'matched_bytes_per_case':480,'original_rom_function':'0x080771e4','runtime_function':'0x030056d8','checks':['packed palette pairs','unsigned UV wraparound','negative increments','zero and full width','optional duplicate scanline','invalid range leaves destination unchanged'],'seconds':round(time.perf_counter()-t,3),'result':'PASS','scope':'Memory output of this one span routine only; not whole-game equivalence, resolution, timing, or performance.'}
Path('outputs/nfsug-research/native-tests.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
