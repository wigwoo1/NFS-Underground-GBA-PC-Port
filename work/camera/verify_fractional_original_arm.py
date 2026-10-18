"""Original ARM query/root/builder versus retained fractional native fixtures."""
from pathlib import Path
import ctypes as C,struct,json,sys,hashlib
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');out=Path('outputs/nfsug-native-renderer/camera-research');report_path=Path(sys.argv[1]) if len(sys.argv)>1 else out/'fractional-repeat-command-trace.json';report=json.loads(report_path.read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_void_p,C.c_size_t)
query=d.nfs_visibility_query;query.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p]
evaluate=d.nfs_visibility_evaluate;evaluate.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p]
results=[]
for sample in report['samples']:
 fixture=Path(sample['query_fixture']).read_bytes();magic,stateaddr,selected,recovery=struct.unpack_from('<4I',fixture);assert magic==0x3146514e
 pose=struct.unpack_from('<26I',fixture,16);ram=fixture[120:];assert len(ram)==0x48000
 def memory(address,n):
  for base,blob in ((0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)):
   if base<=address and address+n<=base+len(blob):return blob[address-base:address-base+n]
  raise ValueError((hex(address),n))
 @Read
 def read(ctx,address,dst,n):
  C.memmove(dst,memory(address,n),n);return 1
 original=memory(stateaddr,256);table,groups=struct.unpack_from('<2I',original,0x60);viewptr=struct.unpack_from('<I',original,0x54)[0]
 state=C.create_string_buffer(original);chosen=C.c_uint(selected);pair=(C.c_uint*2)();assert query(state,C.byref(chosen),recovery,(C.c_uint*2)(*pose[:2]),(C.c_uint*12)(*pose[2:14]),read,None,pair)
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
 for address,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))):u.mem_map(address,n)
 u.mem_write(0x08000000,rom);u.mem_write(0x02000000,ram[:0x40000]);u.mem_write(0x03000000,ram[0x40000:]);sp=0x03007d00
 u.mem_write(0x03005dd0,struct.pack('<I',pose[0]));u.mem_write(0x030000a0,struct.pack('<I',pose[1]));u.mem_write(0x03005d44,struct.pack('<H',selected));u.mem_write(sp+0xa4,struct.pack('<I',0x03009200));u.mem_write(0x03009278,struct.pack('<H',recovery));u.mem_write(0x03009000,struct.pack('<12I',*pose[2:14]));u.mem_write(sp+0x98,struct.pack('<I',0x03009000))
 for reg,value in ((UC_ARM_REG_R0,pose[1]),(UC_ARM_REG_R1,pose[0]),(UC_ARM_REG_SP,sp),(UC_ARM_REG_R7,stateaddr+0xea),(UC_ARM_REG_R8,stateaddr+0xc0),(UC_ARM_REG_R9,stateaddr+0xc8),(UC_ARM_REG_R10,stateaddr),(UC_ARM_REG_R4,sp+0x7c)):u.reg_write(reg,value)
 u.emu_start(0x08002cb5,0x08002d92,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x08002d92
 arm_pair=[u.reg_read(UC_ARM_REG_R7),u.reg_read(UC_ARM_REG_R9)];assert arm_pair==list(pair)
 assert state.raw[:256]==bytes(u.mem_read(stateaddr,256))
 u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_R7,arm_pair[0]);u.reg_write(UC_ARM_REG_R9,arm_pair[1]);u.reg_write(UC_ARM_REG_R10,stateaddr);u.mem_write(sp+0xa0,struct.pack('<I',table));u.emu_start(0x08002feb,0x03004c74,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x03004c74,hex(u.reg_read(UC_ARM_REG_PC))
 u.mem_write(viewptr,struct.pack('<12I',*pose[14:26]));u.reg_write(UC_ARM_REG_R0,stateaddr);u.reg_write(UC_ARM_REG_R1,stateaddr);u.reg_write(UC_ARM_REG_CPSR,u.reg_read(UC_ARM_REG_CPSR)&~32)
 u.emu_start(0x03004c74,0x03004d50,count=2000000);assert u.reg_read(UC_ARM_REG_PC)==0x03004d50
 s=C.create_string_buffer(original);q=C.create_string_buffer(memory(table,512));g=C.create_string_buffer(memory(groups,4096));chosen=C.c_uint(selected)
 assert evaluate(s,q,g,C.byref(chosen),recovery,(C.c_uint*2)(*pose[:2]),(C.c_uint*12)(*pose[2:14]),(C.c_uint*12)(*pose[14:26]),read,None,C.create_string_buffer(rom[0x627700:0x647700]))
 count=struct.unpack_from('<H',s.raw,238)[0];armcount=struct.unpack('<H',u.mem_read(stateaddr+238,2))[0]
 checks=dict(state=s.raw[:256]==bytes(u.mem_read(stateaddr,256)),active_queue=q.raw[:count*16]==bytes(u.mem_read(table,count*16)),membership=g.raw[:4096]==bytes(u.mem_read(groups,4096)),selected=chosen.value==struct.unpack('<H',u.mem_read(0x03005d44,2))[0],count=count==armcount)
 results.append(dict(alpha=sample['alpha'],query_pair=arm_pair,native_queue_count=count,original_queue_count=armcount,checks=checks,original_regions=[struct.unpack('<H',u.mem_read(table+i*16,2))[0] for i in range(armcount)]))
 assert all(checks.values()),results[-1]
assert len(results)==len(report['samples']) and results
(report_path.with_name(report_path.stem+'-original-arm-verification.json') if len(sys.argv)>1 else out/'fractional-original-arm-query-builder-verification.json').write_text(json.dumps(dict(result='PASS',cases=results,scope='Original Thumb point query/root choice and original ARM visibility builder compared with native at all supplied retained fractional poses. Exact active queue/state/membership/selection. No raster/occlusion/fullscene motion proof.'),indent=2));print(json.dumps(results,indent=2))
