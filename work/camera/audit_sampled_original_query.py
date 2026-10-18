"""Original Thumb spatial query versus native C at sampled full-Q8 inputs."""
from pathlib import Path
import ctypes as C,json,struct,sys,math,os,subprocess,hashlib
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent/'pydeps'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
builder_checks=[]
if os.environ.get('NF_TEST_FRESH_ROOT_BUILDER')=='1':
 source=(p/'audit_original_builder_oracle.py').read_text();exec(source[source.index('def offset('):source.index('for serial in [16')]);builder_check=check
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();report=json.loads((p/'race-source-availability.json').read_text());sources={x['serial']:x for x in report['sources']};d=C.CDLL(str(p/'visibility-probe-wide.dll'));P=C.c_void_p;Read=C.CFUNCTYPE(C.c_int,P,C.c_uint32,P,C.c_size_t);d.nfs_visibility_query.argtypes=[P,P,C.c_uint,P,P,Read,P,P];d.nf_visibility_view_sample.argtypes=[P,P,C.c_double,P]
rompath=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');recip=C.create_string_buffer(rom[0x627700:0x647700]);d.nfs_visibility_build.argtypes=[P,P,P,Read,P,P]
d.nfs_visibility_select.argtypes=[P,Read,P,P];d.nfs_visibility_offset.argtypes=[P,P];d.nfs_visibility_pair.argtypes=[P,C.c_uint,P,Read,P,P]
d.nfs_visibility_choose_root.argtypes=[P,P,Read,P,P,P]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x08000000,rom);checks=[]
def off(a):return a-0x02000000 if a<0x03000000 else 0x40000+a-0x03000000
def signed(x):return x if x<0x80000000 else x-0x100000000
for older,newer in [(16,17),(64,65)]:
 ram=(p/('oracle-builder-'+str(older)+'.bin')).read_bytes();rb=(p/('oracle-builder-'+str(newer)+'.bin')).read_bytes();state=0x030000c0;va=struct.unpack_from('<I',ram,off(state)+84)[0];vb=struct.unpack_from('<I',rb,off(state)+84)[0];selected=struct.unpack_from('<H',ram,off(0x03005d44))[0]
 @Read
 def read(ctx,a,out,n):
  try:
   data=rom[a-0x08000000:a-0x08000000+n] if a>=0x08000000 else ram[off(a):off(a)+n];assert len(data)==n;C.memmove(out,data,n);return 1
  except:return 0
 for tick in range(101):
  alpha=tick/100;view=(C.c_uint32*12)();assert d.nf_visibility_view_sample(C.create_string_buffer(ram[off(va):off(va)+48]),C.create_string_buffer(rb[off(vb):off(vb)+48]),alpha,view)
  bases=[]
  for j in range(2):
   value=signed(sources[older]['builder_query_words'][j])*(1-alpha)+signed(sources[newer]['builder_query_words'][j])*alpha;bases.append((math.floor(value+.5) if value>=0 else math.ceil(value-.5))&0xffffffff)
  view[9]=(-(signed(bases[0])//256))&0xffffffff;view[11]=(-(signed(bases[1])//256))&0xffffffff
  matrix=[view[j*3+i] for i in range(3) for j in range(3)]+[0,0,0];u.mem_write(0x02000000,ram[:0x40000]);u.mem_write(0x03000000,ram[0x40000:]);sp=0x03007d00
  u.mem_write(0x03005dd0,struct.pack('<I',bases[0]));u.mem_write(0x030000a0,struct.pack('<I',bases[1]));u.mem_write(sp+0xa4,struct.pack('<I',0x03009200));u.mem_write(0x03009278,struct.pack('<H',17));u.mem_write(0x03009000,struct.pack('<12I',*matrix));u.mem_write(sp+0x98,struct.pack('<I',0x03009000))
  for reg,val in [(UC_ARM_REG_R0,bases[1]),(UC_ARM_REG_R1,bases[0]),(UC_ARM_REG_SP,sp),(UC_ARM_REG_R7,state+234),(UC_ARM_REG_R8,state+192),(UC_ARM_REG_R9,state+200),(UC_ARM_REG_R10,state),(UC_ARM_REG_R4,sp+124)]:u.reg_write(reg,val)
  u.emu_start(0x08002cb5,0x08002d92,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x08002d92
  s=C.create_string_buffer(ram[off(state):off(state)+256],256);pair=(C.c_uint32*2)();chosen=C.c_uint32(selected);assert d.nfs_visibility_query(s,C.byref(chosen),17,(C.c_uint32*2)(*bases),(C.c_uint32*12)(*matrix),read,None,pair)
  original_selected=struct.unpack('<H',bytes(u.mem_read(0x03005d44,2)))[0];exact=chosen.value==original_selected and list(pair)==[u.reg_read(UC_ARM_REG_R7),u.reg_read(UC_ARM_REG_R9)] and s.raw==bytes(u.mem_read(state,256));checks.append(dict(older=older,newer=newer,alpha=alpha,pair=list(pair),selected=chosen.value,original_selected=original_selected,state_and_pair_exact=exact));assert exact,checks[-1]
  prepared=C.create_string_buffer(ram[off(state):off(state)+256],256);C.memmove(C.addressof(prepared)+192,struct.pack('<I',(-view[9])&0xffffffff),4);C.memmove(C.addressof(prepared)+200,struct.pack('<I',(-view[11])&0xffffffff),4);C.memmove(C.addressof(prepared)+234,struct.pack('<H',selected),2);found=C.c_uint32();assert d.nfs_visibility_select(prepared,read,None,C.byref(found));prepared_exact=False
  if found.value!=65535:
   query_offset=(C.c_uint32*3)();assert d.nfs_visibility_offset((C.c_uint32*12)(*matrix),query_offset);prepared_pair=(C.c_uint32*2)();point=(C.c_uint32*4)((-view[9]*256)&0xffffffff,(-view[11]*256)&0xffffffff,query_offset[0],query_offset[2]);assert d.nfs_visibility_pair(prepared,selected,point,read,None,prepared_pair);prepared_exact=prepared.raw==s.raw and list(prepared_pair)==list(pair)
  checks[-1].update(prepared_composition_exact=prepared_exact,prepared_initial_region=found.value)
  root_address=0x03009400;sentinel=b'\xcc'*16;u.mem_write(root_address,sentinel);u.mem_write(sp+0xa0,struct.pack('<I',root_address));first,second=list(pair);chosen_pair=second if first==65535 else first;stop=0x08003064 if second==chosen_pair else 0x08003012
  u.emu_start(0x08002feb,stop,count=200000);assert u.reg_read(UC_ARM_REG_PC)==stop
  root=(C.c_ubyte*16)(*sentinel);root_selected=C.c_uint32(0xcccccccc);assert d.nfs_visibility_choose_root(s,pair,read,None,C.byref(root_selected),root)
  original_root=bytes(u.mem_read(root_address,16));original_region=struct.unpack('<H',bytes(u.mem_read(0x03005d44,2)))[0];root_exact=bytes(root)==original_root and root_selected.value==original_region;checks[-1].update(root_and_selected_exact=root_exact,root=struct.unpack('<H',bytes(root[:2]))[0]);assert root_exact,checks[-1]
  if os.environ.get('NF_TEST_FRESH_ROOT_BUILDER')=='1':
   changed=bytearray(ram);changed[off(state):off(state)+256]=s.raw;changed[off(va):off(va)+48]=bytes(view);queue_address=struct.unpack_from('<I',s.raw,96)[0];seed=bytearray(16);seed[:2]=bytes(root[:2]);seed[2:10]=s.raw[88:96];changed[off(queue_address):off(queue_address)+16]=seed
   query_checks=checks;checks=builder_checks;builder_check('fresh-'+str(older)+'-'+str(newer)+'-'+str(tick),bytes(changed));checks=query_checks
result=dict(result='PASS_QUERY_AND_ROOT_COMPONENT',checks=checks,builder_checks=builder_checks,scope='Original Thumb query08002cb4..08002d92 at202sampled fullQ8 points; synthetic recovery17, root selection08002fea through descriptor redirect exact; synthetic recovery17; no viewport initialization/builder/collector/fullscene60fps proof');(p/'sampled-original-query-audit.json').write_text(json.dumps(result,indent=2));print('PASS',len(checks))






