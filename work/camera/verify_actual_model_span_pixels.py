from pathlib import Path
import ctypes as C,struct,json,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_READ
from unicorn.arm_const import *
from scene_batches import records
p=Path('work/camera');old=list(records(p/'motion-original-model-rect-world.bin'));new=list(records(p/'motion-original-model-spans-world.bin'));filtered=[e for e in new if e['pc']!=0x03005920];assert len(old)==len(filtered)
for a,b in zip(old,filtered):assert all(a[k]==b[k] for k in ('pc','frame','regs','blocks'))
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();code=(p/'motion-original-model-spans-iwram.bin').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,0x1000000)):u.mem_map(a,n)
ram=bytearray((p/"motion-original-model-spans-ewram.bin").read_bytes());u.mem_write(0x02000000,bytes(ram));u.mem_write(0x03000000,code);u.mem_write(0x08000000,rom)
f=C.CDLL(str((p/'native_model.dll').resolve())).nfs_model_span_addresses;f.argtypes=[C.c_uint32,C.c_uint32,C.c_uint,C.c_uint]+[C.c_uint32]*4+[C.c_void_p]*2
reads=[]
def read(cpu,access,address,size,value,data):assert size==1;reads.append(address)
u.hook_add(UC_HOOK_MEM_READ,read,begin=0x02000000,end=0x0203ffff)
u.hook_add(UC_HOOK_MEM_READ,read,begin=0x08000000,end=0x08ffffff)
native=bytearray(0x20000);calls=samples=zeros=0
for e in new:
 if e['pc']==0x03004770:
  address,asset=e['blocks'][66]
  if 0x02000000<=address<0x02040000:
   ram[address-0x02000000:address-0x02000000+len(asset)]=asset;u.mem_write(address,asset)
 if e['pc']!=0x03005920:continue
 shift,U,V,du,dv=struct.unpack('<5I',e['blocks'][91][1]);texture,dest,count=e['regs'][:3];src=(C.c_uint32*240)();dst=(C.c_uint32*240)();assert f(texture,dest,count,shift,U,V,du,dv,src,dst)
 for i,value in enumerate([shift,U,V,du,dv]):u.mem_write(struct.unpack_from('<I',code,0x5a30+i*4)[0],struct.pack('<I',value))
 for reg,value in [(UC_ARM_REG_R0,texture),(UC_ARM_REG_R1,dest),(UC_ARM_REG_R2,count),(UC_ARM_REG_SP,0x03007b00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,value)
 reads.clear();u.emu_start(0x03005920,0x03007000,count=20000);assert reads==list(src)[:count],(e['id'],count,shift,U,V,du,dv,reads[:8],list(src)[:8])
 for i in range(count):
  address=src[i];value=rom[address-0x08000000] if address>=0x08000000 else ram[address-0x02000000];native[dst[i]-0x06000000]=value;zeros+=value==0
 assert bytes(u.mem_read(0x06000000,0x20000))==native,e['id']
 calls+=1;samples+=count
r=dict(result='PASS_ACTUAL_MODEL_SPAN_PIXELS',existing_trace_events_unchanged=len(old),captured_model_spans=calls,texture_samples=samples,opaque_zero_writes=zeros,scope='Actual captured model Q8 globals and writer registers to native addresses/persistent pixel writes exact original ARM. Captured accumulators remain oracle component input; native polygon-to-scanline generation/fullscene not proved.')
(p/'actual-model-span-pixel-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(r)

