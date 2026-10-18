"""Execute actual directional-sign terminal column calls against native address plans."""
import ctypes as C,hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from scene_batches import batches
p=Path('work/camera');capture_path=Path(sys.argv[1]);capture=json.loads(capture_path.read_text());trace=Path(capture['trace']);assert hashlib.sha256(trace.read_bytes()).hexdigest()==capture['trace_sha256']
material=json.loads(Path(sys.argv[2]).read_text());wanted={tuple(c['interval']) for c in material['checks']}
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for address,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,(len(rom)+4095)&~4095)):u.mem_map(address,n)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);reads=[];writes=[]
def on_read(cpu,access,address,size,value,ctx):
 if 0x08000000<=address<0x08000000+len(rom):assert size==1;reads.append(address)
def on_write(cpu,access,address,size,value,ctx):
 assert size==1;writes.append((address,value))
u.hook_add(UC_HOOK_MEM_READ,on_read);u.hook_add(UC_HOOK_MEM_WRITE,on_write,begin=0x06000000,end=0x0601ffff)
d=C.CDLL(str((p/'native_wall.dll').resolve()));fn=d.nfs_wall_unshaded_addresses;fn.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p];checks=[]
for batch in batches(trace):
 key=(batch['begin_refresh'],batch['end_refresh'])
 if key not in wanted:continue
 active=None;calls=rows=opaque=zero=odd_horizontal=lod_columns=0
 for e in batch['events']:
  if e['pc'] in (0x030032f0,0x03004770):active=None
  if e['pc']==0x03000304:active=e['blocks'][5][0]
  if active!=0x08574c3c or e['pc']!=0x030053e8:continue
  address,state=e['blocks'][75];regs=e['regs'];count=regs[3];assert count<=320
  src=(C.c_uint*320)();dst=(C.c_uint*320)();assert fn(C.create_string_buffer(state),regs[1],regs[2],count,src,dst)
  words=struct.unpack('<17I',state);base=words[9];width=1<<words[3];lod=bool(words[6] and words[11]>0x1b000);lod_columns+=lod
  if lod:base+=words[7];width//=4
  expected=[]
  for a,b in zip(list(src)[:count],list(dst)[:count]):
   assert 0x08000000<=a<0x08000000+len(rom);value=rom[a-0x08000000];odd_horizontal+=((a-base)%width)&1
   if value:expected.append((b,value));opaque+=1
   else:zero+=1
  u.mem_write(address,state);reads.clear();writes.clear()
  for i in range(13):u.reg_write(UC_ARM_REG_R0+i,regs[i])
  u.reg_write(UC_ARM_REG_SP,0x03007e00);u.reg_write(UC_ARM_REG_LR,0x03007000);u.emu_start(0x030053e8,0x03007000,count=1000000);assert u.reg_read(UC_ARM_REG_PC)==0x03007000
  assert reads==list(src)[:count] and writes==expected,(key,calls)
  calls+=1;rows+=count
 checks.append(dict(interval=key,columns=calls,exact_source_reads=rows,exact_nonzero_writes=opaque,exact_zero_skips=zero,odd_horizontal_texel_reads=odd_horizontal,lod_columns=lod_columns))
assert len(checks)==len(wanted)==6 and all(c['columns'] for c in checks)
out=capture_path.with_name(capture_path.stem.replace('-verification','-sign-column-verification')+'.json');out.write_text(json.dumps(dict(result='PASS',checks=checks,scope='Actual captured original ARM terminal sign columns exactly match native source-address/nonzero-write plan. Does not verify upstream column attribute interpolation, paired VRAM replication, GPU sampling or continuous motion.'),indent=2));print(json.dumps(dict(result='PASS',scenes=len(checks),columns=sum(c['columns'] for c in checks),reads=sum(c['exact_source_reads'] for c in checks),writes=sum(c['exact_nonzero_writes'] for c in checks),zero_skips=sum(c['exact_zero_skips'] for c in checks))))
