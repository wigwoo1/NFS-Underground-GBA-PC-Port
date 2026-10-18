from pathlib import Path
import ctypes as C,struct,json,sys,random
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x40000);u.mem_write(0x03000000,(p/'motion-original-span-iwram.bin').read_bytes())
f=C.CDLL(str((p/'native_model.dll').resolve())).nfs_model_face_visible;f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
called=[]
def hook(cpu,address,size,data):
 if address==0x03003d24:called.append(True);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
def check(points,indices):
 data=struct.pack('<'+'h'*len(points)*2,*[v for xy in points for v in xy]);idx=(C.c_uint16*len(indices))(*indices);visible=C.c_int();assert f(data,len(points),idx,len(indices),C.byref(visible))
 u.mem_write(0x02001000,data);u.mem_write(0x02002000,bytes(idx));u.mem_write(0x02003000,bytes([len(indices)]));u.mem_write(0x03007d00,struct.pack('<2I',0x02003000,0x02004000))
 for reg,v in ((UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_R7,0x02001000),(UC_ARM_REG_R8,0x02002000),(UC_ARM_REG_R9,0x02004000)):u.reg_write(reg,v)
 called.clear();u.emu_start(0x03004804,0x03004898,count=100)
 assert bool(called)==bool(visible.value)
 return visible.value
models=json.loads((p/'native-motion-model-faces.json').read_text())['models'];snap={m['event']:m for s in json.loads((p/'motion-model-snapshots.json').read_text())['scenes'] for m in s['models']};draws=[]
for m in models:
 visible=[]
 for i,face in enumerate(snap[m['event']]['faces']):
  if check(m['points'],face['vertices']):visible.append(i)
 draws.append(dict(event=m['event'],faces=len(m['faces']),dispatched_faces=visible))
rng=random.Random(0x4804)
for i in range(1000):check([[rng.randrange(-32768,32768),rng.randrange(-32768,32768)] for _ in range(3)],[0,1,2])
r=dict(result='PASS_MODEL_FACE_DISPATCH',model_faces=sum(d['faces'] for d in draws),dispatched_faces=sum(len(d['dispatched_faces']) for d in draws),random_original_ARM_cases=1000,draws=draws,scope='Native first-three determinant and branch selection exact original ARM block for native-projected scene faces and overflow cases. Original full model draw/culling/material setup and polygon raster writes remain unverified.')
(p/'motion-model-face-dispatch-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('draws','scope')})
