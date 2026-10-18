"""Empty native coverage agrees with original edge-extrema early return."""
from pathlib import Path
import ctypes as C,struct,json,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
u.mem_map(0x02000000,0x40000);u.mem_map(0x03000000,0x10000)
u.mem_write(0x03000000,(p/'visibility-overflow-171-wide/iwram.bin').read_bytes())
context=bytearray(72);struct.pack_into('<4I',context,40,0x02001000,0,0,158)
u.mem_write(0x02000000,bytes(context));u.mem_write(0x02001000,bytes(24))
for r,v in ((UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0x02002000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(r,v)
u.emu_start(0x03005798,0x03006000,count=10000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000 and u.reg_read(UC_ARM_REG_R0)==128
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nf_road_span_plan;fn.argtypes=[C.c_void_p,C.c_uint,C.c_int32,C.c_int32,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
vertices=bytes(24);reciprocal=rom[0x627700:0x647700];fb=struct.pack('<4I',0x06000000,0,0,240);out=C.create_string_buffer(b'X'*8192,8192);n=C.c_uint(123)
assert fn(vertices,0,0,158,0,1,reciprocal,fb,out,512,C.byref(n)) and n.value==0 and out.raw==b'X'*8192
report=dict(result='PASS',original_empty_extrema_return=128,native_empty_spans=0,output_storage_unchanged=True,scope='Original5798 skips road edge scheduling with zero clipped vertices; no rasterization claim.')
(p/'live-road-empty-tests.json').write_text(json.dumps(report,indent=2));print(report)
