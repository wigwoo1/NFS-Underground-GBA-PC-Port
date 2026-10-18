from pathlib import Path
import ctypes as C,struct,json,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,(len(rom)+4095)//4096*4096)):u.mem_map(a,n)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,(p/'motion-original-span-iwram.bin').read_bytes())
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);fn=C.CDLL(str((p/'road-polygon-clip.dll').resolve())).nf_road_span_pixels;fn.argtypes=[C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_uint]
@Read
def reader(ctx,address,out,size):
 off=address-0x08000000
 if not 0<=off<=len(rom)-size:return 0
 C.memmove(out,rom[off:off+size],size);return 1
calls=json.loads((p/'native-road-writer-calls.json').read_text());samples=duplicates=0
for call in calls:
 params=call['params'];raw=struct.pack('<16I',*params);width=params[7];double=call['signature'][-1];out=(C.c_uint16*512)();assert fn(raw,reader,None,out,512);expected=bytes(out)[:width*2]
 u.mem_write(0x02001000,raw);u.mem_write(0x03007098,struct.pack('<I',double))
 for reg,val in ((UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,val)
 u.emu_start(0x030056d8,0x03006000,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 assert bytes(u.mem_read(params[6],width*2))==expected,call
 if double:assert bytes(u.mem_read(params[6]+240,width*2))==expected;duplicates+=width*2
 samples+=width*2
r=dict(result='PASS_ACTUAL_NATIVE_ROAD_PIXEL_BYTES',writer_calls=len(calls),primary_bytes=samples,duplicated_bytes=duplicates,scope='Native packed16bit texture samples vs original ARM writer with actual native reconstructed ordered parameters and supplied ROM. Both index lanes and duplicated row bytes verified; palette/display/fullscene motion/timing unverified.')
(p/'native-actual-road-pixel-tests.json').write_text(json.dumps(r,indent=2));print(r)
