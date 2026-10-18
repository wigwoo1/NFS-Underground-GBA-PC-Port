from pathlib import Path
import sys,ctypes as C,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
from scene_batches import records
p=Path('work/camera');old=list(records(p/'motion-original-sprite-writes-world.bin'));new=list(records(p/'motion-original-sprite-inputs-world.bin'));kept=[e for e in new if e['pc']!=0xffff0102];assert len(old)==len(kept)
for a,b in zip(old,kept):
 for k in ('pc','frame','regs','blocks'):assert a[k]==b[k]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,0x1000000)]:u.mem_map(a,n)
u.mem_write(0x03000000,(p/'motion-original-sprite-inputs-iwram.bin').read_bytes())
d=C.CDLL(str((p/'native_initial_page.dll').resolve()));f=d.nfs_initial_block_copy;f.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_void_p,C.c_size_t,C.c_uint32];checks=[]
for e in new:
 if e['pc']!=0xffff0102:continue
 r=e['regs'];a,src=e['blocks'][102];initial=bytes((i*37+13)&255 for i in range(0x20000));out=C.create_string_buffer(initial,len(initial));assert f(out,len(initial),r[0]-0x06000000,src,len(src),r[2]);u.mem_write(0x06000000,initial);u.mem_write(a,src)
 for reg,value in [(UC_ARM_REG_R0,r[0]),(UC_ARM_REG_R1,r[1]),(UC_ARM_REG_R2,r[2]),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,value)
 u.emu_start(0x03000298,0x03006000,count=200000);assert out.raw==bytes(u.mem_read(0x06000000,len(initial)))
 checks.append(dict(refresh=e['frame'],source=hex(a),destination=hex(r[0]),bytes=len(src)))
report=dict(result='PASS_NATIVE_SPRITE_BLOCK_COPY',existing_records_preserved=len(old),calls=len(checks),copied_bytes=sum(c['bytes'] for c in checks),checks=checks,scope='Owned captured copy inputs vs original ARM full buffer; no complete sprite/OAM/palette composition claim.')
(p/'native-sprite-block-copy-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
