from pathlib import Path
import sys,ctypes as C,struct,random,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x40000);u.mem_write(0x03000000,(p/'motion-original-span-iwram.bin').read_bytes());fn=C.CDLL(str((p/'wall-edge-order.dll').resolve())).nf_wall_edge_order;fn.argtypes=[C.c_int,C.c_int,C.c_uint,C.c_void_p];rng=random.Random(0x1ec8)
for case in range(1000):
 left,right=rng.randrange(-32768,32768),rng.randrange(-32768,32768);flags=rng.randrange(65536);out=(C.c_int*3)();assert fn(left,right,flags,out);u.mem_write(0x02001000,struct.pack('<2h',left,right));u.reg_write(UC_ARM_REG_R5,0x02001000);u.reg_write(UC_ARM_REG_R6,flags);u.emu_start(0x03001ec8,0x03001ef8,count=20);actual=(*struct.unpack('<2h',u.mem_read(0x02001000,4)),u.reg_read(UC_ARM_REG_R6));assert tuple(out)==actual
r=dict(result='PASS_ORIGINAL_WALL_ORDER_BLOCK',cases=1000,scope='Original sourceflag conditional horizontal swap block; vertical/depth/UV ordering not swapped here. No fullwall raster proof.');(p/'wall-edge-order-tests.json').write_text(json.dumps(r,indent=2));print(r)
