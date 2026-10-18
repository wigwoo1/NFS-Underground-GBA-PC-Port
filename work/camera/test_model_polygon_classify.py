from pathlib import Path
import ctypes as C,struct,json,sys,random
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x40000);u.mem_write(0x03000000,(p/'motion-original-span-iwram.bin').read_bytes())
f=C.CDLL(str((p/'native_model.dll').resolve())).nfs_model_polygon_classify;f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
rng=random.Random(0x5824);counts={}
for case in range(2000):
 n=rng.randrange(3,33);points=[[rng.randrange(-32768,32768),rng.randrange(-32768,32768)] for _ in range(n)]
 rect=[rng.randrange(-32768,32768) for _ in range(4)];rect[0],rect[2]=sorted((rect[0],rect[2]));rect[1],rect[3]=sorted((rect[1],rect[3]));indices=list(range(n));rng.shuffle(indices)
 data=struct.pack('<'+'h'*n*2,*[v for xy in points for v in xy]);idx=(C.c_uint16*n)(*indices);out=C.c_int();assert f(data,n,idx,n,(C.c_int32*4)(*rect),C.byref(out))
 poly=bytearray(32);struct.pack_into('<I',poly,0,0x02001000);struct.pack_into('<I',poly,8,0x02002000);struct.pack_into('<I',poly,20,n)
 for a,b in [(0x02001000,data),(0x02002000,bytes(idx)),(0x02003000,bytes(poly)),(0x02004000,struct.pack('<4i',*rect))]:u.mem_write(a,b)
 for reg,v in [(UC_ARM_REG_R0,0x02004000),(UC_ARM_REG_R1,0x02003000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,v)
 u.emu_start(0x03005824,0x03007000,count=2000);assert out.value==u.reg_read(UC_ARM_REG_R0);counts[str(out.value)]=counts.get(str(out.value),0)+1
report=dict(result='PASS_NATIVE_MODEL_POLYGON_CLASSIFIER',original_ARM_cases=2000,classification_counts=counts,scope='Original rectangle classification component with randomized source rings and bounds. Actual per-draw model rectangles not yet captured in motion snapshot; clipping/raster/fullscene unverified.')
(p/'model-polygon-classify-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
