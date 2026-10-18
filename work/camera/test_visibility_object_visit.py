from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x20000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_visit;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_void_p,C.c_void_p]
callback_seen=[]
def hook(uc,pc,size,ctx):
 if pc==0x0201f000:callback_seen.append(1);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
 if pc in [0x03002090,0x030021f8]:uc.emu_stop()
u.hook_add(UC_HOOK_CODE,hook)
rng=random.Random(2000)
for case in range(1024):
 index=case%256;obj=bytearray(rng.randbytes(164));struct.pack_into('<H',obj,8,case%8);struct.pack_into('<H',obj,0x48,0 if case%3==0 else 1);struct.pack_into('<H',obj,0x4e,0)
 initial=bytearray(32)
 if case&256:initial[index//8]|=1<<(index%8)
 u.mem_write(0x030070c0,bytes(initial));u.mem_write(0x0200003c,struct.pack('<I',0x02001000));u.mem_write(0x02000078,struct.pack('<I',0x0201e000));u.mem_write(0x0201e000,struct.pack('<I',0x0201f000));u.mem_write(0x02001000+index*164,bytes(obj));callback_seen.clear()
 for reg,val in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,index),(UC_ARM_REG_SP,0x03007c00)]:u.reg_write(reg,val)
 u.emu_start(0x03002000,0x03002600,count=200)
 out=C.create_string_buffer(bytes(initial));selector=C.c_uint32(123)
 result=fn(out,32,index,C.create_string_buffer(bytes(obj)),C.byref(selector))
 assert result==int(u.reg_read(UC_ARM_REG_PC)==0x03002090) and out.raw[:32]==bytes(u.mem_read(0x030070c0,32))
 assert selector.value==(0 if callback_seen else 65535)
out=C.create_string_buffer(bytes(initial));selector=C.c_uint32(123)
assert fn(out,32,256,C.create_string_buffer(bytes(obj)),C.byref(selector))==-1 and selector.value==123 and out.raw[:32]==initial
report=dict(result='PASS',original_ARM_synthetic_cases=1024,invalid_index_atomic=True,scope='Visit bitmap,active gate and callback selector only; callback stubbed and post-callback sorting not covered.')
(root/'visibility-object-visit-tests.json').write_text(json.dumps(report,indent=2));print(report)
