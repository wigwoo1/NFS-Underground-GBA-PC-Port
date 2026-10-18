"""Execute recovered ARM copy with actual captured ABI; no live scene replacement."""
import ctypes as C,csv,json,hashlib,sys
from pathlib import Path
from project_paths import load_session
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent/'pydeps'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR
s=load_session(p/'prototype-runs/threaded-prepared-4c0a478bbea14eedbc3a639513b0b9d6-session.json')
rom=Path(s['rom']).read_bytes();assert hashlib.sha256(rom).hexdigest()==s['rom_sha256'].lower()
code=(p/'motion-original-initial-inputs-iwram.bin').read_bytes()[0x3814:0x3a14]
checks=[]
for row in csv.DictReader((p/'sky-caller-trace.csv').open()):
 dest=int(row['destination'],16);source=int(row['source'],16);width=int(row['width']);height=int(row['height']);ss=int(row['source_stride']);ds=int(row['destination_stride'])
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x8000);u.mem_write(0x03003814,code);u.mem_map(0x06000000,0x20000);u.mem_write(0x06000000,b'\xcc'*0x20000)
 base=source&~0xfff;u.mem_map(base,0x6000);u.mem_write(base,rom[base-0x08000000:base-0x08000000+0x6000])
 sp=0x03007d00;u.mem_write(sp,ss.to_bytes(4,'little')+ds.to_bytes(4,'little'))
 for reg,value in [(UC_ARM_REG_R0,dest),(UC_ARM_REG_R1,source),(UC_ARM_REG_R2,width),(UC_ARM_REG_R3,height),(UC_ARM_REG_SP,sp),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,value)
 written=set()
 def write(uc,access,address,size,value,user):
  if 0x06000000<=address<0x06020000:written.update(range(address,address+size))
 u.hook_add(UC_HOOK_MEM_WRITE,write);u.emu_start(0x03003814,0x03007000,count=100000)
 assert u.reg_read(UC_ARM_REG_SP)==sp
 actual=bytes(u.mem_read(0x06000000,0x20000))
 assert len(written)==15136
 assert written and all(actual[a-0x06000000]==rom[source-0x08000000+a-dest] for a in written)
 assert all(actual[i]==0xcc for i in range(0x20000) if 0x06000000+i not in written)
 checks.append(dict(refresh=int(row['refresh']),destination=hex(dest),source=hex(source),width_argument=width,height_argument=height,source_stride=ss,destination_stride=ds,written_bytes=len(written),first_offset=min(written)-0x06000000,last_offset=max(written)-0x06000000,all_copied_indices_exact=True,outside_unchanged=True))
assert len(checks)==161
report=dict(result='PASS',checks=checks,code_sha256=hashlib.sha256(code).hexdigest(),scope='Independent original ARM sky copy executes161 moving-route ABIs including256-byte row stores and final16-byte tail and all observed stores match ROM indices; does not prove renderer integration, whole scene or game timing.')
(p/'sky-original-copy-abi-tests.json').write_text(json.dumps(report,indent=2));print('PASS original ARM sky copy:',len(checks),'complete footprints')
