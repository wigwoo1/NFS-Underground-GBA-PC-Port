from pathlib import Path
import ctypes as C,struct,random,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
for base,size in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(base,size)
u.mem_write(0x08000000,rom);u.mem_write(0x03006768,struct.pack('<I',1))
d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);d.nf_model_world_rotation_owned.argtypes=[Read,C.c_void_p,C.c_void_p,C.c_void_p]
@Read
def read(user,address,out,size):
 try:C.memmove(out,bytes(u.mem_read(address,size)),size);return 1
 except Exception:return 0
rng=random.Random(0x233e0);object=bytearray(164);struct.pack_into('<I',object,140,0x02001000)
for trial in range(700):
 pose=rng.randbytes(36);u.mem_write(0x02001140,pose);u.mem_write(0x03007c58,bytes(48))
 for reg,value in [(UC_ARM_REG_R7,0x02001000),(UC_ARM_REG_R5,0x03007c58),(UC_ARM_REG_SP,0x03007c00)]:u.reg_write(reg,value)
 u.emu_start(0x080233e1,0x08023448,count=100)
 out=C.create_string_buffer(48);assert d.nf_model_world_rotation_owned(read,None,bytes(object),out);assert out.raw==bytes(u.mem_read(0x03007c58,48))
out=C.create_string_buffer(b'X'*48,48);u.mem_write(0x03006768,bytes(4));assert not d.nf_model_world_rotation_owned(read,None,bytes(object),out) and out.raw==b'X'*48
u.mem_write(0x03006768,struct.pack('<I',1));struct.pack_into('<I',object,140,0xffffff00);assert not d.nf_model_world_rotation_owned(read,None,bytes(object),out) and out.raw==b'X'*48
report=dict(result='PASS',original_thumb_cases=700,atomic_rejections=2,scope='Original external Q12 pose to world Q14 orientation branch only; disabled external-pose branch unsupported.')
(p/'model-world-rotation-tests.json').write_text(json.dumps(report,indent=2));print(report)
